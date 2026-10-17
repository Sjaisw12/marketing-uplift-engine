"""End-to-end synthetic campaign. No real datasets, model fitting or GitHub writes."""

import base64
import copy
import json
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from execution_safeguards.bundle import export_bundle, restore_bundle
from execution_safeguards.coordinator import RECOVERY_DOMAIN, Coordinator
from execution_safeguards.interfaces import FEATURES, NAMES, array_sha
from execution_safeguards.journal import Journal
from execution_safeguards.protocol import (
    BACKUP_DOMAIN,
    DOMAIN,
    Denied,
    canonical,
    digest,
    file_hash,
)
from execution_safeguards.receipt import AmbiguousWrite

from .test_receipt import MemoryTransport

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 10, 17, tzinfo=UTC)


class FileJournal:
    """Local-only test backend: independent clients share create-exclusive files."""

    prefix = "refs/tags/synthetic-local-journal/"

    def __init__(self, root, prefix=None):
        self.root = root
        if prefix is not None:
            self.prefix = prefix
        root.mkdir(exist_ok=True)

    def list(self):
        return [self.prefix + p.name for p in sorted(self.root.iterdir())]

    def read(self, ref):
        path = self.root / ref.removeprefix(self.prefix)
        return json.loads(path.read_text()) if path.exists() else None

    def create(self, ref, event):
        try:
            with (self.root / ref.removeprefix(self.prefix)).open("xb") as stream:
                stream.write(canonical(event))
        except FileExistsError as exc:
            raise Denied("Journal slot already claimed") from exc


@pytest.fixture
def campaign(tmp_path):
    source = tmp_path / "fixture"
    source.mkdir()
    models = source / "models"
    models.mkdir()
    ids = np.arange(80, dtype=np.uint64)
    x = np.random.default_rng(104).normal(size=(80, 12))
    (source / "features.json").write_bytes(
        canonical({"row_id": ids.tolist(), "columns": FEATURES, "x": x.tolist()})
    )
    (source / "outcomes.json").write_bytes(
        canonical(
            {
                "row_id": ids.tolist(),
                "treatment": ((ids // 2) % 2).tolist(),
                "visit": (ids % 2).tolist(),
            }
        )
    )
    model_sha = {}
    for index, name in enumerate(NAMES):
        path = models / f"{name}.json"
        weights = [0.01] * (13 if name == "s_learner" else 12)
        path.write_bytes(
            canonical({"synthetic_fixture_model": True, "weights": weights, "bias": index / 10 - 1})
        )
        model_sha[name] = file_hash(path)
    key = Ed25519PrivateKey.generate()
    public = base64.b64encode(key.public_key().public_bytes_raw()).decode()
    sources = {n: file_hash(source / n) for n in ("features.json", "outcomes.json")}
    manifest = {
        "synthetic_only": True,
        "rows": len(ids),
        "models": model_sha,
        "dataset_sha256": digest(sources),
        "source_files": sources,
        "ids_sha256": array_sha(ids),
        "authorization": {
            "public_key": public,
            "owner": "synthetic-owner",
            "execution_id": "one-synthetic-campaign",
            "not_before": "2026-01-01T00:00:00+00:00",
            "expires_at": "2027-01-01T00:00:00+00:00",
        },
    }
    (source / "reviewed-fixture.json").write_bytes(canonical(manifest))
    reviewed_sha = file_hash(source / "reviewed-fixture.json")
    receipts = MemoryTransport()
    prefix = f"refs/tags/stage-b-journal/{digest(sources)}/{array_sha(ids)}/"
    journal = FileJournal(tmp_path / "journal", prefix)
    private = tmp_path / "private"

    def sign(payload, domain=DOMAIN):
        return {
            "payload": copy.deepcopy(payload),
            "signature": base64.b64encode(key.sign(domain + canonical(payload))).decode(),
        }

    def fresh(instance="worker-a"):
        return Coordinator(
            ROOT,
            source,
            reviewed_sha,
            receipts,
            FileJournal(journal.root, prefix),
            private,
            instance,
        )

    coordinator = fresh()
    authorization = sign(coordinator.expected_authorization())

    def backup(c):
        bundle = tmp_path / "checkpoint.tar"
        export_bundle(private, c.manifest, bundle)
        # Simulated transfer to another path; does not prove off-workspace durability.
        transferred = tmp_path / "owner-device-simulation.tar"
        shutil.copyfile(bundle, transferred)
        restored = tmp_path / "restored-copy"
        restore_bundle(transferred, restored, digest(c.manifest), 1024 * 1024)
        payload = {
            "schema": 1,
            "purpose": "independent-private-backup",
            "manifest_sha256": digest(c.manifest),
            "binding": c.binding,
        }
        return restored, sign(payload, BACKUP_DOMAIN)

    return {
        "c": coordinator,
        "auth": authorization,
        "sign": sign,
        "fresh": fresh,
        "backup": backup,
        "source": source,
        "private": private,
        "journal": journal,
        "receipts": receipts,
        "ids": ids,
        "x": x,
    }


def test_complete_synthetic_campaign_uses_frozen_statistical_kernel(campaign):
    c = campaign["c"]
    c.start(campaign["auth"], NOW)
    manifest = c.score_features()
    backup, signature = campaign["backup"](c)
    c.seal(backup, signature)
    result = c.evaluate()
    assert len(result["family"]) == 765 and len(result["keys"]) == 15
    assert result["iid"]["draws"].shape[0] == 2000
    assert result["stratified"]["draws"].shape[0] == 2000
    assert manifest == c.manifest
    assert c.journal.read(c.tip)[-1]["stage"] == "completed"
    assert len(campaign["receipts"].values) == 1
    with pytest.raises(Denied):
        c.evaluate()
    with pytest.raises(Denied):
        campaign["fresh"]("worker-b").start(campaign["auth"], NOW)


@pytest.mark.parametrize("failure", ["missing", "forged", "expired", "lock", "owner", "dataset"])
def test_authorization_failures_never_claim_receipt(campaign, failure):
    c, envelope = campaign["c"], copy.deepcopy(campaign["auth"])
    if failure == "missing":
        envelope = {}
    elif failure == "forged":
        envelope["signature"] = base64.b64encode(b"\0" * 64).decode()
    elif failure == "expired":
        envelope["payload"]["expires_at"] = "2025-01-01T00:00:00+00:00"
        envelope = campaign["sign"](envelope["payload"])
    else:
        field = {"lock": "execution_lock_sha256", "owner": "owner", "dataset": "dataset_sha256"}[
            failure
        ]
        envelope["payload"][field] = "0" * 64
        envelope = campaign["sign"](envelope["payload"])
    with pytest.raises(Denied):
        c.start(envelope, NOW)
    assert not campaign["receipts"].values and not campaign["journal"].list()


@pytest.mark.parametrize("phase", ["unstarted", "claimed", "scored"])
def test_outcomes_denied_before_seal(campaign, phase, monkeypatch):
    c = campaign["c"]
    if phase != "unstarted":
        c.start(campaign["auth"], NOW)
    if phase == "scored":
        c.score_features()
    original = Path.read_bytes

    def deny_outcomes(path):
        if path == campaign["source"] / "outcomes.json":
            pytest.fail("Outcome access before seal")
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", deny_outcomes)
    with pytest.raises(Denied):
        c.evaluate()


@pytest.mark.parametrize("target", ["model", "dataset", "policy", "seed", "execution"])
def test_changed_identities_stop_before_scoring(campaign, target):
    c = campaign["c"]
    c.start(campaign["auth"], NOW)
    if target == "model":
        (campaign["source"] / "models/response.json").write_text("changed")
    elif target == "dataset":
        (campaign["source"] / "features.json").write_text("changed")
    elif target == "seed":
        c.settings["random_rank_seed"] += 1
    elif target == "execution":
        c.trusted["authorization"]["execution_id"] = "another"
    else:
        c.trusted["new_policy"] = "forbidden"
    with pytest.raises(Denied):
        c.score_features()
    assert not campaign["private"].exists()


@pytest.mark.parametrize(
    "failure", ["missing-file", "corrupted", "missing-backup", "changed-manifest"]
)
def test_checkpoint_and_backup_failures(campaign, failure):
    c = campaign["c"]
    c.start(campaign["auth"], NOW)
    c.score_features()
    backup, signature = campaign["backup"](c)
    if failure == "missing-file":
        (campaign["private"] / "scores.npy").unlink()
    elif failure == "corrupted":
        (backup / "scores.npy").write_bytes(b"corrupted")
    elif failure == "missing-backup":
        signature["signature"] = base64.b64encode(b"\0" * 64).decode()
    else:
        c.manifest["files"]["scores.npy"]["sha256"] = "0" * 64
    with pytest.raises((Denied, FileNotFoundError)):
        c.seal(backup, signature)
    assert c.journal.read(c.tip)[-1]["stage"] == "features_scored"


def test_concurrent_journal_writers_and_duplicate_order(campaign):
    c = campaign["c"]
    c.start(campaign["auth"], NOW)
    tip = c.tip
    barrier = threading.Barrier(2)
    backend = campaign["journal"]

    class Racing(FileJournal):
        def create(self, ref, event):
            barrier.wait(timeout=10)
            return super().create(ref, event)

    def append(instance):
        journal = Journal(Racing(backend.root, backend.prefix), c.binding)
        try:
            journal.append("feature_scoring_started", {"source_sha256": "a" * 64}, instance, tip)
            return True
        except Denied:
            return False

    # Same authorized instance still cannot acquire the same next slot twice.
    with ThreadPoolExecutor(2) as pool:
        assert sum(pool.map(append, [c.instance, c.instance])) == 1
    with pytest.raises(Denied):
        c.score_features()
    with pytest.raises(Denied):
        c.journal.append("completed", {"result_manifest_sha256": "a" * 64}, c.instance, tip)


def test_truncated_tampered_journal_and_ambiguous_write(campaign):
    c = campaign["c"]
    c.start(campaign["auth"], NOW)
    c.score_features()
    last = campaign["journal"].root / "000002"
    original = last.read_bytes()
    last.unlink()
    with pytest.raises(Denied):
        c.journal.read(c.tip)
    last.write_bytes(original)
    event = json.loads(original)
    event["binding"]["execution_id"] = "tampered"
    last.write_bytes(canonical(event))
    with pytest.raises(Denied):
        c.journal.read(c.tip)
    last.write_bytes(original)

    class TimedOut(FileJournal):
        def create(self, ref, event):
            super().create(ref, event)
            raise TimeoutError("lost response after write")

    journal = Journal(TimedOut(campaign["journal"].root, campaign["journal"].prefix), c.binding)
    with pytest.raises(AmbiguousWrite):
        journal.append(
            "predictions_sealed",
            {"checkpoint_sha256": digest(c.manifest), "backup_sha256": "a" * 64},
            c.instance,
            c.tip,
        )
    with pytest.raises(Denied):
        c.journal.read(c.tip)


def test_signed_recovery_changes_writer_not_campaign(campaign):
    c = campaign["c"]
    c.start(campaign["auth"], NOW)
    c.score_features()
    backup, signature = campaign["backup"](c)
    c.seal(backup, signature)
    receipt_before = copy.deepcopy(campaign["receipts"].values)
    new = campaign["fresh"]("worker-recovered")
    new.receipt = copy.deepcopy(c.receipt)
    new._bind_journal()
    request = new.recovery_expected(
        c.journal.read(c.tip),
        new.instance,
        "2027-01-01T00:00:00+00:00",
        "2026-01-01T00:00:00+00:00",
    )
    new.receipt = new.journal = None
    recovery = campaign["sign"](request, RECOVERY_DOMAIN)
    new.recover(campaign["auth"], c.manifest, backup, signature, c.tip, recovery, NOW)
    new._at("predictions_sealed")
    assert campaign["receipts"].values == receipt_before
    with pytest.raises(Denied):
        c._at("predictions_sealed")
    assert len(new.evaluate()["family"]) == 765
    # A durable recovery event retains the actual signature, not just an unverifiable hash.
    event_path = campaign["journal"].root / "000004"
    event = json.loads(event_path.read_text())
    event["evidence"]["signed_recovery"]["signature"] = base64.b64encode(b"\0" * 64).decode()
    event_path.write_bytes(canonical(event))
    with pytest.raises(Denied):
        new.journal.read()


@pytest.mark.parametrize("failure", ["unsigned", "expired", "wrong-instance", "interrupted-action"])
def test_recovery_requires_fresh_specific_approval(campaign, failure):
    c = campaign["c"]
    c.start(campaign["auth"], NOW)
    c.score_features()
    backup, signature = campaign["backup"](c)
    new = campaign["fresh"]("replacement")
    new.receipt = c.receipt
    new._bind_journal()
    request = new.recovery_expected(
        c.journal.read(c.tip),
        new.instance,
        "2027-01-01T00:00:00+00:00",
        "2026-01-01T00:00:00+00:00",
    )
    new.receipt = new.journal = None
    if failure == "expired":
        request["expires_at"] = "2025-01-01T00:00:00+00:00"
    if failure == "wrong-instance":
        request["new_instance"] = "unauthorized"
    if failure == "interrupted-action":
        c.journal.append(
            "predictions_sealed",
            {"checkpoint_sha256": digest(c.manifest), "backup_sha256": "a" * 64},
            c.instance,
            c.tip,
        )
    recovery = campaign["sign"](request, RECOVERY_DOMAIN)
    if failure == "unsigned":
        recovery["signature"] = base64.b64encode(b"\0" * 64).decode()
    with pytest.raises(Denied):
        new.recover(campaign["auth"], c.manifest, backup, signature, c.tip, recovery, NOW)


def test_production_factory_denies_before_io(monkeypatch):
    def fail(*args, **kwargs):
        pytest.fail("Production attempted I/O")

    monkeypatch.setattr(Path, "read_bytes", fail)
    with pytest.raises(Denied, match="Stage B disabled"):
        Coordinator.production(approved=True, public_key="claimed")


@pytest.mark.parametrize("action", ["scoring", "outcomes"])
def test_interrupted_action_never_gets_automatically_repeated(campaign, monkeypatch, action):
    c = campaign["c"]
    c.start(campaign["auth"], NOW)

    def crash(*args, **kwargs):
        raise RuntimeError("Synthetic interrupted action")

    if action == "scoring":
        monkeypatch.setattr("execution_safeguards.coordinator.score_synthetic", crash)
        with pytest.raises(RuntimeError):
            c.score_features()
    else:
        c.score_features()
        backup, signature = campaign["backup"](c)
        c.seal(backup, signature)
        monkeypatch.setattr("execution_safeguards.coordinator.evaluate_synthetic", crash)
        with pytest.raises(RuntimeError):
            c.evaluate()
    new = campaign["fresh"]("recovery-attempt")
    with pytest.raises(Denied, match="Ambiguous action"):
        new.recover(campaign["auth"], None, None, None, c.tip, {}, NOW)
