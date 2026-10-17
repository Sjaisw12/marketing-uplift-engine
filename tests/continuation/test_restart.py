"""Real OS process death/restart, with no GitHub, real keys, models or holdout access."""

import base64
import copy
import hashlib
import json
import os
import select
import subprocess
import sys
import tomllib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from execution_safeguards.bundle import restore_bundle
from execution_safeguards.protocol import Denied, canonical, digest, file_hash, strict_json
from production_adapter.parquet import ids_sha
from stage_b_activation.authorization import BACKUP_DOMAIN, draft
from stage_b_activation.backup import backup_payload
from stage_b_continuation import approval
from stage_b_continuation.lock import verify

ROOT = Path(__file__).resolve().parents[2]
WORKER = Path(__file__).with_name("worker.py")


def write(path, value):
    path.write_text(json.dumps(value))


@pytest.fixture
def case(tmp_path):
    key = Ed25519PrivateKey.generate()  # ephemeral synthetic key; never production
    public = key.public_key().public_bytes_raw()
    now = datetime(2026, 10, 17, tzinfo=UTC)
    ids = np.arange(80, dtype=np.uint64)
    source = tmp_path / "invented.parquet"
    pq.write_table(
        pa.table(
            {
                "row_id": ids,
                **{f"f{i}": np.sin(ids + i) for i in range(12)},
                "treatment": ((ids // 2) % 2).astype(np.uint8),
                "visit": (ids % 2).astype(np.uint8),
            }
        ),
        source,
    )
    source_sha = file_hash(source)
    receipt = f"refs/tags/stage-b-receipts/{source_sha}/{ids_sha(ids)}"
    config = json.loads((ROOT / "activation/config.json").read_text())
    config.update(disk_reserve_bytes=0, ciphertext_chunk_bytes=1024)
    project = tomllib.loads((ROOT / "configs/project.toml").read_text())
    project["resources"].update(min_free_disk_bytes=0, batch_rows=17)
    plan = {
        "lock_sha": "d" * 64,
        "config": config,
        "parent": {
            "config": {
                "owner": "synthetic-owner",
                "execution_id": "synthetic-only",
                "public_key_base64": base64.b64encode(public).decode(),
                "public_key_sha256": hashlib.sha256(public).hexdigest(),
                "receipt_ruleset_id": 25285405,
                "journal_ruleset_id": 25285424,
            },
            "dataset_sha256": source_sha,
            "model_manifest_sha256": "c" * 64,
            "holdout": {"sha256": ids_sha(ids)},
            "receipt_ref": receipt,
            "journal_prefix": receipt.replace("stage-b-receipts", "stage-b-journal") + "/",
            "settings": tomllib.loads((ROOT / "configs/phase9.toml").read_text()),
            "policies": {"primary": "none", "diagnostics": "fixed synthetic"},
        },
    }
    commit = "a" * 40
    rules = json.loads((ROOT / "production/rulesets.json").read_text())["rulesets"]
    rules[0]["conditions"]["ref_name"]["include"] = [receipt]
    rules[1]["conditions"]["ref_name"]["include"] = [plan["parent"]["journal_prefix"] + "*"]

    def report(at):
        return {
            "schema": 1,
            "execution_lock_sha256": plan["lock_sha"],
            "reviewed_commit": commit,
            "observed_at": at.isoformat(),
            "expires_at": (at + timedelta(minutes=45)).isoformat(),
            "private_repository": {"full_name": config["backup_repository"], "private": True},
            "rulesets": copy.deepcopy(rules),
        }

    def sign(payload, domain):
        return {
            "payload": payload,
            "signature": base64.b64encode(key.sign(domain + canonical(payload))).decode(),
        }

    original = report(now)
    auth = sign(
        {
            **draft(plan),
            "reviewed_commit": commit,
            "preflight_sha256": digest(original),
            "not_before": now.isoformat(),
            "expires_at": (now + timedelta(minutes=45)).isoformat(),
        },
        approval.START_DOMAIN,
    )
    fixture = {
        "plan": plan,
        "project": project,
        "source_sha256": source_sha,
        "commit": commit,
        "start": now.isoformat(),
        "resume_time": (now + timedelta(hours=2)).isoformat(),
        "authorization": auth,
        "original_report": original,
    }
    write(tmp_path / "fixture.json", fixture)

    def prepare_restore():
        pause = strict_json((tmp_path / "private/pause.json").read_bytes())
        # Independent restore into a different directory: synthetic files ONLY.
        restore_bundle(
            tmp_path / "private/export/checkpoint.tar",
            tmp_path / "owner-restored",
            digest(pause["manifest"]),
            1000000,
        )
        for name, spec in pause["manifest"]["files"].items():
            assert file_hash(tmp_path / "owner-restored" / name) == spec["sha256"]
        later = now + timedelta(hours=2)
        fresh = report(later)
        end = (later + timedelta(minutes=45)).isoformat()
        grant = sign(
            approval.continuation_payload(
                plan, commit, pause, "worker-b", fresh, later.isoformat(), end
            ),
            approval.CONTINUE_DOMAIN,
        )
        proof = sign(
            backup_payload(
                pause["manifest"],
                pause["transfer"],
                pause["private_commit"],
                digest(fresh),
                later.isoformat(),
                end,
            ),
            BACKUP_DOMAIN,
        )
        write(tmp_path / "continue.json", {"approval": grant, "backup": proof, "preflight": fresh})
        return pause

    return {"root": tmp_path, "fixture": fixture, "sign": sign, "restore": prepare_restore}


def env():
    return {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "OPENBLAS_NUM_THREADS": "2",
        "OMP_NUM_THREADS": "2",
    }


def paused(case):
    p = subprocess.Popen(
        [sys.executable, str(WORKER), str(case["root"]), "part1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env(),
    )
    try:
        ready, _, _ = select.select([p.stdout], [], [], 30)
        assert ready, "Synthetic worker failed to reach durable pause"
        line = p.stdout.readline()
        assert line.strip() == "SYNTHETIC_PUBLICATION_DURABLE", (
            p.stderr.read() if p.poll() is not None else line
        )
    finally:
        p.kill()
        out, err = p.communicate(timeout=10)
    assert p.returncode == -9, (out, err)
    return p.pid


def run(case, phase="resume"):
    return subprocess.run(
        [sys.executable, str(WORKER), str(case["root"]), phase],
        capture_output=True,
        text=True,
        timeout=45,
        env=env(),
    )


def test_actual_process_death_and_authorized_expired_original_resume(case):
    old_pid = paused(case)
    case["restore"]()
    result = run(case)
    assert result.returncode == 0, result.stderr
    status = json.loads(result.stdout)
    assert status["pid"] != old_pid and status["stage"] == "completed" and status["family"] == 765
    root = case["root"]
    assert len(list((root / "receipts").glob("*.json"))) == 1
    assert (
        (root / "features.calls").read_text() == (root / "outcomes.calls").read_text() == "called\n"
    )
    assert run(case).returncode != 0  # same continuation cannot be replayed


@pytest.mark.parametrize(
    "bad",
    [
        "checkpoint_missing",
        "checkpoint_corrupt",
        "pause",
        "original",
        "backup",
        "continuation",
        "expired_continuation",
        "expired_preflight",
        "changed_model",
        "changed_policy",
        "changed_dataset",
        "journal_gap",
        "journal_tamper",
        "journal_truncate",
        "private_commit",
        "no_restore",
        "missing_approval",
        "missing_backup",
        "resigned_pause",
    ],
)
def test_resume_failures_never_read_outcomes(case, bad):
    paused(case)
    case["restore"]()
    root = case["root"]
    p = strict_json((root / "continue.json").read_bytes())
    if bad == "checkpoint_missing":
        (root / "private/predictions/scores.npy").unlink()
    elif bad == "checkpoint_corrupt":
        with (root / "private/predictions/scores.npy").open("r+b") as f:
            f.write(b"tampered")
    elif bad == "pause":
        pause = strict_json((root / "private/pause.json").read_bytes())
        pause["private_commit"] = "f" * 40
        write(root / "private/pause.json", pause)
    elif bad == "original":
        (root / "private/original-approval.json").write_text("{}")
    elif bad == "backup":
        p["backup"]["signature"] = base64.b64encode(b"\0" * 64).decode()
    elif bad == "continuation":
        p["approval"]["signature"] = base64.b64encode(b"\0" * 64).decode()
    elif bad == "expired_continuation":
        p["approval"]["payload"]["expires_at"] = case["fixture"]["start"]
        p["approval"] = case["sign"](p["approval"]["payload"], approval.CONTINUE_DOMAIN)
    elif bad == "expired_preflight":
        p["preflight"] = case["fixture"]["original_report"]
    elif bad == "changed_model":
        f = case["fixture"]
        f["plan"]["parent"]["model_manifest_sha256"] = "e" * 64
        write(root / "fixture.json", f)
    elif bad == "changed_policy":
        f = case["fixture"]
        f["plan"]["parent"]["policies"]["primary"] = "tampered"
        write(root / "fixture.json", f)
    elif bad == "changed_dataset":
        (root / "invented.parquet").write_bytes(b"changed synthetic identity")
    elif bad == "journal_gap":
        (root / "journal/000001.json").unlink()
    elif bad == "journal_tamper":
        path = root / "journal/000002.json"
        e = strict_json(path.read_bytes())
        e["evidence"]["checkpoint_sha256"] = "e" * 64
        write(path, e)
    elif bad == "journal_truncate":
        (root / "journal/000003.json").unlink()
    elif bad == "private_commit":
        write(root / "remote-commit.json", {"commit": "f" * 40})
    elif bad == "no_restore":
        p["backup"]["payload"]["owner_confirms_mac_decryption_and_restore"] = False
        p["backup"] = case["sign"](p["backup"]["payload"], BACKUP_DOMAIN)
    elif bad == "missing_approval":
        p["approval"] = {}
    elif bad == "missing_backup":
        p["backup"] = {}
    elif bad == "resigned_pause":
        pause = strict_json((root / "private/pause.json").read_bytes())
        pause["private_commit"] = "e" * 40
        write(root / "private/pause.json", pause)
        p["approval"]["payload"]["pause_sha256"] = digest(pause)
        p["approval"] = case["sign"](p["approval"]["payload"], approval.CONTINUE_DOMAIN)
    write(root / "continue.json", p)
    result = run(case)
    assert result.returncode != 0, result.stdout
    assert not (root / "outcomes.calls").exists()
    assert (root / "features.calls").read_text() == "called\n"
    assert len(list((root / "receipts").glob("*.json"))) == 1


@pytest.mark.parametrize(
    "phase",
    ["ambiguous", "premature", "outcome_crash", "outcome_reader_crash", "state_write_failure"],
)
def test_interrupted_continuation_never_replays(case, phase):
    paused(case)
    case["restore"]()
    result = run(case, phase)
    assert result.returncode != 0
    assert run(case).returncode != 0
    calls = case["root"] / "outcomes.calls"
    if phase == "outcome_reader_crash":
        assert calls.read_text() == "called\n"
    else:
        assert not calls.exists()


def test_two_competing_continuation_processes_evaluate_at_most_once(case):
    paused(case)
    case["restore"]()
    processes = [
        subprocess.Popen(
            [sys.executable, str(WORKER), str(case["root"]), "resume"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env(),
        )
        for _ in range(2)
    ]
    for p in processes:
        p.communicate(timeout=45)
    assert sum(p.returncode == 0 for p in processes) == 1
    assert (case["root"] / "outcomes.calls").read_text() == "called\n"
    assert (case["root"] / "features.calls").read_text() == "called\n"


def test_competing_new_process_blocked_by_os_lease(case):
    paused(case)
    case["restore"]()
    holder = subprocess.Popen(
        [sys.executable, str(WORKER), str(case["root"]), "hold"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env(),
    )
    try:
        ready, _, _ = select.select([holder.stdout], [], [], 20)
        assert ready
        assert holder.stdout.readline().strip() == "SYNTHETIC_LEASE_HELD"
        result = run(case)
        assert result.returncode != 0 and "Another local worker" in result.stderr
    finally:
        holder.kill()
        holder.communicate(timeout=10)
    assert run(case).returncode == 0


def test_child_lock_and_old_authorization_domain_rejected(case):
    # Child lock is metadata-only; checks all immutable parent files without data queries.
    plan = verify(ROOT)
    assert (
        plan["activation_lock_sha256"]
        == "bd08dd6f38c672adcd3367c3134c0d3f7ad424dada60dabb47c3f2c0a216d103"
    )
    fixture = case["fixture"]
    a = copy.deepcopy(fixture["authorization"])
    from stage_b_activation.authorization import DOMAIN

    a = case["sign"](a["payload"], DOMAIN)
    with pytest.raises(Denied):
        approval.start(
            a,
            fixture["plan"],
            fixture["commit"],
            fixture["original_report"],
            datetime.fromisoformat(fixture["start"]),
        )


@pytest.mark.parametrize(
    "bad",
    ["missing_signature", "forged", "expired", "wrong_commit", "wrong_lock", "unresumable_start"],
)
def test_new_start_rejects_invalid_or_unresumable_grants(case, bad):
    f = case["fixture"]
    a = copy.deepcopy(f["authorization"])
    now = datetime.fromisoformat(f["start"])
    if bad == "missing_signature":
        a["signature"] = None
    elif bad == "forged":
        a["signature"] = base64.b64encode(b"\0" * 64).decode()
    elif bad == "expired":
        now += timedelta(hours=2)
    else:
        key = {
            "wrong_commit": "reviewed_commit",
            "wrong_lock": "execution_lock_sha256",
            "unresumable_start": "not_before",
        }[bad]
        a["payload"][key] = (
            (now - timedelta(minutes=1)).isoformat()
            if bad == "unresumable_start"
            else "f" * (40 if bad == "wrong_commit" else 64)
        )
        a = case["sign"](a["payload"], approval.START_DOMAIN)
    with pytest.raises(Denied):
        approval.start(a, f["plan"], f["commit"], f["original_report"], now)


def test_unsigned_real_factory_never_constructs_source(monkeypatch, tmp_path):
    import stage_b_continuation.operator as module

    def forbidden(*args):
        pytest.fail("Unauthorized real source constructed")

    monkeypatch.setattr(module, "FrozenSource", forbidden)
    with pytest.raises(Denied):
        module.production(
            ROOT, tmp_path / "never-created", "synthetic", {"payload": {}, "signature": None}, {}
        )
    assert not (tmp_path / "never-created").exists()
