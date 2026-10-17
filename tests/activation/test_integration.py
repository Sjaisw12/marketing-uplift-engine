"""Only tiny invented Parquet, synthetic keys, fake Git and simulated encryption."""

import base64
import copy
import json
import shutil
import threading
import tomllib
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from execution_safeguards.interfaces import NAMES
from execution_safeguards.protocol import RECOVERY_DOMAIN, Denied, canonical, digest, file_hash
from execution_safeguards.receipt import AmbiguousWrite, ReceiptStore
from production_adapter.parquet import _batches, ids_sha
from stage_b_activation import authorization, backup
from stage_b_activation.coordinator import _Coordinator, production
from stage_b_activation.preflight import validate

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 10, 17, tzinfo=UTC)
START = NOW.isoformat()
END = (NOW + timedelta(minutes=45)).isoformat()
COMMIT = "a" * 40


class Memory:
    namespace = "stage-b-receipts"

    def __init__(self, prefix="", data=None, lock=None):
        self.prefix = prefix
        self.data = {} if data is None else data
        self.lock = threading.Lock() if lock is None else lock

    def read(self, ref):
        return copy.deepcopy(self.data.get(ref))

    def list(self):
        return sorted(self.data)

    def create(self, ref, payload):
        with self.lock:
            if ref in self.data:
                raise Denied("Existing atomic slot")
            self.data[ref] = copy.deepcopy(payload)


class Remote:
    def __init__(self):
        self.sha = None
        self.reads = self.writes = 0

    def access(self):
        self.reads += 1
        return "b" * 40

    def commit(self):
        return self.sha

    def publish(self, directory, transfer):
        if self.sha is not None:
            raise Denied("Duplicate private branch")
        self.writes += 1
        self.sha = digest(transfer)[:40]
        return self.sha


class Model:
    def __init__(self, name):
        self.name = name

    def predict(self, x, **kwargs):
        assert x.shape[1] == (13 if self.name == "s_learner" else 12)
        return 1 / (1 + np.exp(-x[:, 0] / 10 - (x[:, -1] / 10 if x.shape[1] == 13 else 0)))


@pytest.fixture
def campaign(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ids = np.arange(80, dtype=np.uint64)
    path = tmp_path / "synthetic.parquet"
    columns = {
        "row_id": ids,
        **{f"f{i}": np.sin(ids.astype(float) + i) for i in range(12)},
        "treatment": ((ids // 2) % 2).astype(np.uint8),
        "visit": (ids % 2).astype(np.uint8),
    }
    pq.write_table(pa.table(columns), path)
    source_hash = file_hash(path)
    key = Ed25519PrivateKey.generate()
    public = base64.b64encode(key.public_key().public_bytes_raw()).decode()
    settings = tomllib.loads((ROOT / "configs/phase9.toml").read_text())
    config = json.loads((ROOT / "activation/config.json").read_text())
    config["disk_reserve_bytes"] = 0  # tiny /tmp fixtures only, not reviewed production config
    config["ciphertext_chunk_bytes"] = 1024
    project = tomllib.loads((ROOT / "configs/project.toml").read_text())
    project["resources"]["min_free_disk_bytes"] = 0
    project["resources"]["batch_rows"] = 17
    fake_rules = json.loads((ROOT / "production/rulesets.json").read_text())["rulesets"]
    receipt = f"refs/tags/stage-b-receipts/{source_hash}/{ids_sha(ids)}"
    prefix = receipt.replace("stage-b-receipts/", "stage-b-journal/") + "/"
    fake_rules[0]["conditions"]["ref_name"]["include"] = [receipt]
    fake_rules[1]["conditions"]["ref_name"]["include"] = [prefix + "*"]
    parent = {
        "config": {
            "owner": "fixture-owner",
            "execution_id": "fixture-one",
            "public_key_base64": public,
            "public_key_sha256": __import__("hashlib")
            .sha256(key.public_key().public_bytes_raw())
            .hexdigest(),
            "receipt_ruleset_id": 25285405,
            "journal_ruleset_id": 25285424,
        },
        "settings": settings,
        "dataset_sha256": source_hash,
        "model_manifest_sha256": "c" * 64,
        "holdout": {"sha256": ids_sha(ids)},
        "policies": {"primary": "none", "diagnostics": "unchanged fixture"},
        "receipt_ref": receipt,
        "journal_prefix": prefix,
    }
    plan = {"lock_sha": "d" * 64, "parent": parent, "config": config}
    report = {
        "schema": 1,
        "execution_lock_sha256": plan["lock_sha"],
        "reviewed_commit": COMMIT,
        "observed_at": START,
        "expires_at": END,
        "private_repository": {"full_name": config["backup_repository"], "private": True},
        "rulesets": fake_rules,
    }
    receipts, journal, remote = Memory(), Memory(prefix), Remote()

    class Source:
        def __init__(self):
            self.ids = ids
            self.feature_calls = self.outcome_calls = 0

        def check(self):
            if file_hash(path) != source_hash:
                raise Denied("Changed synthetic source")

        def models(self):
            return {n: Model(n) for n in NAMES}

        def features(self):
            self.feature_calls += 1
            return _batches(path, ids, ["row_id", *[f"f{i}" for i in range(12)]], project)

        def outcomes(self):
            self.outcome_calls += 1
            # The test itself checks durable evidence at the exact reader boundary.
            history = sorted(journal.data.values(), key=lambda e: e["sequence"])
            assert history[-1]["stage"] == "outcome_access_started"
            return _batches(path, ids, ["row_id", "treatment", "visit"], project)

    source = Source()

    def fresh(instance="worker-a"):
        return _Coordinator(
            plan,
            COMMIT,
            source,
            ReceiptStore(receipts),
            journal,
            remote,
            tmp_path / "private",
            instance,
            lambda: None,
            lambda: NOW,
        )

    def sign(payload, domain=authorization.DOMAIN):
        return {
            "payload": copy.deepcopy(payload),
            "signature": base64.b64encode(key.sign(domain + canonical(payload))).decode(),
        }

    payload = {
        **authorization.draft(plan),
        "reviewed_commit": COMMIT,
        "preflight_sha256": digest(report),
        "not_before": START,
        "expires_at": END,
    }
    envelope = sign(payload)
    actual_export = backup.export_checkpoint

    def simulated_encrypt(binary, cfg, archive, cipher):
        # Explicit fake encryption; NEVER evidence of real confidentiality.
        with Path(cipher).open("xb") as out, Path(archive).open("rb") as inp:
            out.write(b"synthetic-test-only-fake-cipher\n")
            shutil.copyfileobj(inp, out)

    def export(*args, **kwargs):
        return actual_export(*args, **kwargs, encryptor=simulated_encrypt)

    monkeypatch.setattr(backup, "export_checkpoint", export)

    def ready(c, seal=True):
        c.start(envelope, report)
        c.score_features()
        transfer = c.export("synthetic-no-binary")
        private_commit = c.publish(transfer)
        p = backup.backup_payload(c.manifest, transfer, private_commit, digest(report), START, END)
        signature = sign(p, authorization.BACKUP_DOMAIN)
        if seal:
            c.seal(transfer, signature, report)
        return transfer, signature

    return {
        "c": fresh(),
        "fresh": fresh,
        "plan": plan,
        "report": report,
        "auth": envelope,
        "source": source,
        "receipts": receipts,
        "journal": journal,
        "remote": remote,
        "sign": sign,
        "ready": ready,
        "path": path,
        "tmp": tmp_path,
    }


def test_complete_synthetic_integration(campaign):
    c = campaign["c"]
    campaign["ready"](c)
    result = c.evaluate()
    assert len(result["family"]) == 765 and len(result["keys"]) == 15
    assert result["iid"]["draws"].shape[0] == result["stratified"]["draws"].shape[0] == 2000
    assert c.journal.read(c.tip)[-1]["stage"] == "completed"
    assert campaign["source"].feature_calls == campaign["source"].outcome_calls == 1
    assert campaign["remote"].writes == len(campaign["receipts"].data) == 1
    with pytest.raises(Denied):
        c.evaluate()
    with pytest.raises(Denied):
        campaign["fresh"]("other").start(campaign["auth"], campaign["report"])


@pytest.mark.parametrize(
    "bad",
    [
        "missing",
        "forged",
        "expired",
        "null-window",
        "long-window",
        "lock",
        "model",
        "dataset",
        "owner",
        "commit",
        "preflight",
    ],
)
def test_authorization_rejected_before_claim_or_data(campaign, bad):
    auth = copy.deepcopy(campaign["auth"])
    if bad == "missing":
        auth = {}
    elif bad == "forged":
        auth["signature"] = base64.b64encode(b"\0" * 64).decode()
    else:
        if bad == "expired":
            auth["payload"]["expires_at"] = START
        elif bad == "null-window":
            auth["payload"]["not_before"] = None
        elif bad == "long-window":
            auth["payload"]["expires_at"] = (NOW + timedelta(days=2)).isoformat()
        else:
            field = {
                "lock": "execution_lock_sha256",
                "model": "model_manifest_sha256",
                "dataset": "dataset_sha256",
                "owner": "owner",
                "commit": "reviewed_commit",
                "preflight": "preflight_sha256",
            }[bad]
            auth["payload"][field] = "0" * 64
        auth = campaign["sign"](auth["payload"])
    with pytest.raises(Denied):
        campaign["c"].start(auth, campaign["report"])
    assert not campaign["receipts"].data and campaign["source"].feature_calls == 0
    assert campaign["source"].outcome_calls == 0


@pytest.mark.parametrize(
    "bad", ["public", "rules-off", "bypass", "creation-blocked", "coverage", "stale"]
)
def test_preflight_failures(campaign, bad):
    report = copy.deepcopy(campaign["report"])
    if bad == "public":
        report["private_repository"]["private"] = False
    elif bad == "rules-off":
        report["rulesets"][0]["enforcement"] = "disabled"
    elif bad == "bypass":
        report["rulesets"][0]["bypass_actors"] = [{"actor_id": 1}]
    elif bad == "creation-blocked":
        report["rulesets"][1]["rules"].append({"type": "creation"})
    elif bad == "coverage":
        report["rulesets"][0]["conditions"]["ref_name"]["include"] = ["wrong"]
    else:
        report["expires_at"] = START
    with pytest.raises(Denied):
        validate(report, campaign["plan"], COMMIT, NOW)


@pytest.mark.parametrize("phase", ["unstarted", "claimed", "scored", "exported"])
def test_outcome_access_denied_before_owner_seal(campaign, phase):
    c = campaign["c"]
    if phase != "unstarted":
        c.start(campaign["auth"], campaign["report"])
    if phase in {"scored", "exported"}:
        c.score_features()
    if phase == "exported":
        c.export("fixture")
    with pytest.raises(Denied):
        c.evaluate()
    assert campaign["source"].outcome_calls == 0


@pytest.mark.parametrize(
    "bad",
    [
        "unsigned",
        "wrong-restore",
        "wrong-commit",
        "wrong-recipient",
        "wrong-catalog",
        "wrong-execution",
        "missing-part",
        "corrupt-part",
    ],
)
def test_backup_proof_failures_never_open_outcomes(campaign, bad):
    c = campaign["c"]
    transfer, proof = campaign["ready"](c, seal=False)
    if bad == "unsigned":
        proof["signature"] = base64.b64encode(b"\0" * 64).decode()
    elif bad in {"missing-part", "corrupt-part"}:
        p = c.private / "export/publish" / transfer["parts"][0]["path"]
        if bad == "missing-part":
            p.unlink()
        else:
            p.write_bytes(b"corrupt")
    else:
        field = {
            "wrong-restore": "owner_confirms_mac_decryption_and_restore",
            "wrong-commit": "commit",
            "wrong-recipient": "recipient_sha256",
            "wrong-catalog": "catalog_sha256",
            "wrong-execution": "binding",
        }[bad]
        proof["payload"][field] = False if bad == "wrong-restore" else "0" * 64
        proof = campaign["sign"](proof["payload"], authorization.BACKUP_DOMAIN)
    with pytest.raises((Denied, FileNotFoundError)):
        c.seal(transfer, proof, campaign["report"])
    assert campaign["source"].outcome_calls == 0


@pytest.mark.parametrize(
    "what", ["prediction", "membership", "backup-ref", "seed", "model", "policy", "dataset"]
)
def test_tampering_after_seal_stops_before_outcome_reader(campaign, what):
    c = campaign["c"]
    campaign["ready"](c)
    if what in {"prediction", "membership"}:
        (c.predictions / ("scores.npy" if what == "prediction" else "memberships.npy")).write_bytes(
            b"bad"
        )
    elif what == "backup-ref":
        campaign["remote"].sha = "f" * 40
    elif what == "dataset":
        campaign["path"].write_bytes(b"bad")
    else:
        c.plan["parent"][what] = "modified"
    with pytest.raises(Denied):
        c.evaluate()
    assert campaign["source"].outcome_calls == 0


def recovery_request(c, instance="recovered"):
    return {
        "schema": 1,
        "purpose": "same-campaign-recovery",
        "binding": c.binding,
        "journal_sha256": digest(c.journal.read(c.tip)),
        "new_instance": instance,
        "previous_worker_terminated": True,
        "not_before": START,
        "expires_at": END,
    }


def test_signed_recovery_preserves_receipt_and_never_rescores(campaign):
    c = campaign["c"]
    transfer, proof = campaign["ready"](c)
    before = copy.deepcopy(campaign["receipts"].data)
    recovered = campaign["fresh"]("recovered")
    signature = campaign["sign"](recovery_request(c), RECOVERY_DOMAIN)
    recovered.recover(
        campaign["auth"],
        campaign["report"],
        c.manifest,
        transfer,
        proof,
        campaign["report"],
        c.tip,
        signature,
    )
    assert campaign["receipts"].data == before
    with pytest.raises(Denied):
        c.evaluate()  # old worker cannot ignore the advanced journal tip
    assert len(recovered.evaluate()["family"]) == 765
    assert campaign["source"].feature_calls == campaign["source"].outcome_calls == 1


@pytest.mark.parametrize(
    "bad",
    [
        "unsigned",
        "expired",
        "wide-window",
        "wrong-worker",
        "changed-tip",
        "changed-checkpoint",
        "missing-checkpoint",
        "same-instance",
    ],
)
def test_recovery_fails_closed(campaign, bad):
    c = campaign["c"]
    transfer, proof = campaign["ready"](c)
    request = recovery_request(c)
    instance = "recovered"
    manifest, tip = copy.deepcopy(c.manifest), c.tip
    if bad == "expired":
        request["expires_at"] = START
    elif bad == "wide-window":
        request["expires_at"] = (NOW + timedelta(days=2)).isoformat()
    elif bad == "wrong-worker":
        request["new_instance"] = "different"
    elif bad == "changed-tip":
        tip = "f" * 64
    elif bad == "changed-checkpoint":
        manifest["binding"]["execution_id"] = "different"
    elif bad == "missing-checkpoint":
        (c.predictions / "scores.npy").unlink()
    elif bad == "same-instance":
        instance = c.instance
        request["new_instance"] = instance
    signature = campaign["sign"](request, RECOVERY_DOMAIN)
    if bad == "unsigned":
        signature["signature"] = base64.b64encode(b"\0" * 64).decode()
    with pytest.raises((Denied, FileNotFoundError)):
        campaign["fresh"](instance).recover(
            campaign["auth"],
            campaign["report"],
            manifest,
            transfer,
            proof,
            campaign["report"],
            tip,
            signature,
        )
    assert campaign["source"].outcome_calls == 0


@pytest.mark.parametrize("action", ["feature", "outcome", "export", "publish"])
def test_interrupted_actions_are_not_silently_repeated(campaign, monkeypatch, action):
    c = campaign["c"]

    def crash(*args, **kwargs):
        raise RuntimeError("invented crash")

    if action == "feature":
        c.start(campaign["auth"], campaign["report"])
        monkeypatch.setattr(c.source, "features", crash)
        with pytest.raises(RuntimeError):
            c.score_features()
        with pytest.raises(Denied):
            c.score_features()
    elif action == "outcome":
        transfer, proof = campaign["ready"](c)
        monkeypatch.setattr(c.source, "outcomes", crash)
        with pytest.raises(RuntimeError):
            c.evaluate()
        with pytest.raises(Denied):
            c.evaluate()
        request = campaign["sign"](recovery_request(c), RECOVERY_DOMAIN)
        with pytest.raises(Denied, match="audit only"):
            campaign["fresh"]("recovered").recover(
                campaign["auth"],
                campaign["report"],
                c.manifest,
                transfer,
                proof,
                campaign["report"],
                c.tip,
                request,
            )
    elif action == "export":
        c.start(campaign["auth"], campaign["report"])
        c.score_features()
        monkeypatch.setattr(backup, "export_checkpoint", crash)
        with pytest.raises(RuntimeError):
            c.export("fixture")
        with pytest.raises(Denied):
            c.export("fixture")
        assert campaign["remote"].writes == 0
    else:
        c.start(campaign["auth"], campaign["report"])
        c.score_features()
        transfer = c.export("fixture")
        monkeypatch.setattr(c.remote, "publish", crash)
        with pytest.raises(RuntimeError):
            c.publish(transfer)
        with pytest.raises(Denied):
            c.publish(transfer)
    assert campaign["source"].outcome_calls == 0


@pytest.mark.parametrize("action", ["receipt", "journal-before", "journal-after", "readback"])
def test_ambiguous_writes_and_readback_never_open_outcomes(campaign, monkeypatch, action):
    c = campaign["c"]
    if action == "receipt":
        original = campaign["receipts"].create

        def lost(ref, payload):
            original(ref, payload)
            raise TimeoutError("response lost after commit")

        monkeypatch.setattr(campaign["receipts"], "create", lost)
        with pytest.raises(AmbiguousWrite):
            c.start(campaign["auth"], campaign["report"])
        with pytest.raises(Denied):
            c.start(campaign["auth"], campaign["report"])
    else:
        campaign["ready"](c)
        original = campaign["journal"].create

        def lost(ref, event):
            if action != "journal-before":
                original(ref, event)
            raise TimeoutError("synthetic ambiguous journal response")

        if action == "readback":
            read = campaign["journal"].read

            def unreadable(ref):
                event = read(ref)
                if event and event["stage"] == "outcome_access_started":
                    raise OSError("synthetic failed readback")
                return event

            monkeypatch.setattr(campaign["journal"], "read", unreadable)
        else:
            monkeypatch.setattr(campaign["journal"], "create", lost)
        with pytest.raises(AmbiguousWrite):
            c.evaluate()
        with pytest.raises(Denied):
            c.evaluate()
    assert campaign["source"].outcome_calls == 0


@pytest.mark.parametrize("damage", ["truncate", "tamper"])
def test_durable_history_damage_stops_access(campaign, damage):
    c = campaign["c"]
    campaign["ready"](c)
    key = sorted(campaign["journal"].data)[-1]
    if damage == "truncate":
        del campaign["journal"].data[key]
    else:
        campaign["journal"].data[key]["previous_sha256"] = "0" * 64
    with pytest.raises(Denied):
        c.evaluate()
    assert campaign["source"].outcome_calls == 0


def test_concurrent_stage_claim_has_only_one_winner(campaign):
    from execution_safeguards.journal import Journal

    c = campaign["c"]
    c.start(campaign["auth"], campaign["report"])
    shared = campaign["journal"]
    barrier = threading.Barrier(2)

    class Racing(Memory):
        def create(self, ref, payload):
            barrier.wait(timeout=10)
            super().create(ref, payload)

    def attempt(_):
        backend = Racing(shared.prefix, shared.data, shared.lock)
        j = Journal(backend, c.binding)
        try:
            j.append(
                "feature_scoring_started",
                {"source_sha256": c.plan["parent"]["dataset_sha256"]},
                c.instance,
                c.tip,
            )
            return True
        except Denied:
            return False

    with ThreadPoolExecutor(2) as pool:
        assert sum(pool.map(attempt, [0, 1])) == 1
    assert campaign["source"].feature_calls == campaign["source"].outcome_calls == 0


def test_production_default_and_unsigned_draft_never_construct_source(monkeypatch):
    def fail(*args, **kwargs):
        pytest.fail("Production source constructed without approval")

    monkeypatch.setattr("stage_b_activation.coordinator.FrozenSource", fail)
    with pytest.raises(Denied, match="Stage B disabled"):
        production(ROOT, "/never-created", "worker")
    with pytest.raises(Denied, match="Stage B disabled"):
        production(ROOT, "/never-created", "worker", {"payload": {}, "signature": None})


def test_ambiguous_completed_write_cannot_repeat_analysis(campaign, monkeypatch):
    c = campaign["c"]
    campaign["ready"](c)
    create = campaign["journal"].create

    def lost(ref, event):
        create(ref, event)
        if event["stage"] == "completed":
            raise TimeoutError("synthetic response lost after completion")

    monkeypatch.setattr(campaign["journal"], "create", lost)
    with pytest.raises(AmbiguousWrite):
        c.evaluate()
    assert campaign["source"].outcome_calls == 1
    with pytest.raises(Denied):
        c.evaluate()
    assert campaign["source"].outcome_calls == 1


def test_frozen_source_outcome_interface_is_one_use_and_checks_durable_stage(campaign):
    from stage_b_activation.source import FrozenSource

    source = FrozenSource.__new__(FrozenSource)
    source._ids = np.arange(80, dtype=np.uint64)
    source._outcomes_opened = False
    source.path = campaign["path"]
    source.config = tomllib.loads((ROOT / "configs/project.toml").read_text())
    source.config["resources"]["min_free_disk_bytes"] = 0
    state = {"stage": "features_scored"}

    def guard(stage):
        if stage != state["stage"]:
            raise Denied("Durable stage not verified")

    source._guard = guard
    with pytest.raises(Denied):
        source.outcomes()
    assert not source._outcomes_opened
    state["stage"] = "outcome_access_started"
    assert all(b.schema.names == ["row_id", "treatment", "visit"] for b in source.outcomes())
    with pytest.raises(Denied):
        source.outcomes()
