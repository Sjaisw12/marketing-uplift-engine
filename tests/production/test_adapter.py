"""Synthetic Parquet, prediction and export tests; never a real holdout reader."""

import base64
import hashlib
import json
import shutil
import tomllib
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from execution_safeguards.interfaces import NAMES
from execution_safeguards.protocol import Denied, digest, file_hash
from production_adapter.export import export_chunks, restore_chunks
from production_adapter.parquet import ParquetAdapter, _batches, ids_sha
from production_adapter.plan import LOCK, PreparedExecutor, build, verify
from production_adapter.scoring import evaluate_sealed, read_seal, score_batches

ROOT = Path(__file__).resolve().parents[2]


class Dummy:
    def __init__(self, name):
        self.name = name

    def predict(self, x, **kwargs):
        assert x.shape[1] == (13 if self.name == "s_learner" else 12)
        return 1 / (1 + np.exp(-(x[:, 0] / 10 + (x[:, -1] / 10 if x.shape[1] == 13 else 0))))


@pytest.fixture
def synthetic(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = tomllib.loads((ROOT / "configs/project.toml").read_text())
    config["resources"]["batch_rows"] = 17
    # /tmp is a separate ~5GiB mount; tiny fixtures do not need the 8GiB production reserve.
    config["resources"]["min_free_disk_bytes"] = 0
    ids = np.arange(80, dtype=np.uint64)
    columns = {
        "row_id": ids,
        **{f"f{i}": np.sin(ids.astype(float) + i) for i in range(12)},
        "treatment": ((ids // 2) % 2).astype(np.uint8),
        "visit": (ids % 2).astype(np.uint8),
        "conversion": np.zeros(80, dtype=np.uint8),
        "exposure": np.zeros(80, dtype=np.uint8),
    }
    path = tmp_path / "fixture.parquet"
    pq.write_table(pa.table(columns), path)
    settings = tomllib.loads((ROOT / "configs/phase9.toml").read_text())
    return path, ids, config, settings, tmp_path


def seal_fixture(synthetic):
    path, ids, config, settings, tmp = synthetic
    root = tmp / "predictions"
    m = score_batches(
        _batches(path, ids, ["row_id", *[f"f{i}" for i in range(12)]], config),
        ids,
        {n: Dummy(n) for n in NAMES},
        root,
        settings,
        {"synthetic_only": True},
        0,
    )
    return root, m


def test_projection_prediction_seal_and_frozen_kernel(synthetic):
    path, ids, config, settings, tmp = synthetic
    root, m = seal_fixture(synthetic)
    values = read_seal(root, m, m["binding"], ids_sha(ids))
    for j in range(4):
        assert values["memberships"][j].sum(axis=1).tolist() == [8, 16, 24, 32, 40]
    result = evaluate_sealed(
        _batches(path, ids, ["row_id", "treatment", "visit"], config),
        root,
        m,
        m["binding"],
        ids_sha(ids),
        settings,
    )
    assert len(result["family"]) == 765 and result["iid"]["draws"].shape[0] == 2000


@pytest.mark.parametrize("bad", ["exposure", "visit", "treatment", "conversion"])
def test_forbidden_projection(synthetic, bad):
    path, ids, config, _, _ = synthetic
    with pytest.raises(Denied):
        list(_batches(path, ids, ["row_id", bad], config))


@pytest.mark.parametrize("bad", ["missing", "duplicate", "nonfinite", "wrong-type", "null"])
def test_anomalies_stop_without_filtering(synthetic, bad):
    path, ids, config, _, _ = synthetic
    table = pq.read_table(path)
    if bad == "missing":
        table = table.slice(1)
    if bad == "duplicate":
        table = pa.concat_tables([table, table.slice(0, 1)])
    if bad == "nonfinite":
        table = table.set_column(1, "f0", pa.array([float("nan")] * 80))
    if bad == "wrong-type":
        table = table.set_column(1, "f0", pa.array([1] * 80, type=pa.int64()))
    if bad == "null":
        table = table.set_column(1, "f0", pa.array([None] * 80, type=pa.float64()))
    pq.write_table(table, path)
    with pytest.raises(Denied):
        list(_batches(path, ids, ["row_id", *[f"f{i}" for i in range(12)]], config))


def test_seal_checked_before_outcome_iteration(synthetic):
    root, m = seal_fixture(synthetic)
    (root / "memberships.npy").write_bytes(b"changed")

    def forbidden():
        pytest.fail("Outcome iterator entered before seal verification")
        yield

    with pytest.raises(Denied):
        evaluate_sealed(forbidden(), root, m, m["binding"], ids_sha(synthetic[1]), synthetic[3])


def test_private_chunks_restore_and_corruption(synthetic):
    root, m = seal_fixture(synthetic)
    tmp = synthetic[-1]
    catalog = export_chunks(root, m, tmp / "export", 1024, 0)
    shutil.copytree(tmp / "export", tmp / "owner-device-simulation")
    assert (
        restore_chunks(tmp / "owner-device-simulation", tmp / "restore", digest(catalog), 1048576)
        == m
    )
    assert file_hash(tmp / "restore/scores.npy") == m["files"]["scores.npy"]["sha256"]
    (tmp / "owner-device-simulation/part-000000.bin").write_bytes(b"corrupt")
    with pytest.raises(Denied):
        restore_chunks(tmp / "owner-device-simulation", tmp / "other", digest(catalog), 1048576)
    with pytest.raises(Denied):
        restore_chunks(tmp / "export", tmp / "tiny", digest(catalog), 1)
    with pytest.raises(FileExistsError):
        export_chunks(root, m, tmp / "export", 1024, 0)


def test_key_namespaces_and_authorization():
    p = build(ROOT)
    e = PreparedExecutor(ROOT)
    assert (
        hashlib.sha256(base64.b64decode(p["config"]["public_key_base64"])).hexdigest()
        == p["config"]["public_key_sha256"]
    )
    expected = e.expected_authorization("2026-01-01T00:00:00+00:00", "2027-01-01T00:00:00+00:00")
    assert expected["model_manifest_sha256"] == p["model_manifest_sha256"]
    with pytest.raises(Denied):
        e.verify_authorization(
            {"payload": expected, "signature": base64.b64encode(b"\0" * 64).decode()},
            expected["not_before"],
            expected["expires_at"],
        )
    _, j = e.inert_transports("a" * 40)
    assert j.prefix == p["journal_prefix"]
    with pytest.raises(Denied):
        j.list()


def test_real_apis_deny_before_io(monkeypatch):
    e = PreparedExecutor(ROOT)
    a = ParquetAdapter(ROOT, e.payload)

    def forbidden(*args, **kwargs):
        pytest.fail("Unauthorized I/O")

    monkeypatch.setattr(Path, "open", forbidden)
    for method in (
        e.start,
        e.score,
        e.seal,
        e.evaluate,
        e.recover,
        a.holdout_features,
        a.holdout_outcomes,
    ):
        with pytest.raises(Denied, match="Stage B disabled"):
            method(approved=True, receipt="claimed")


def test_portability_and_key_or_ruleset_tampering(tmp_path):
    p = build(ROOT)
    for name in p["files"]:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    assert build(tmp_path) == p
    lock = tmp_path / LOCK
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(json.dumps({"execution_lock_sha256": digest(p), "payload": p}))
    assert verify(tmp_path) == digest(p)
    config = tmp_path / "production/config.json"
    v = json.loads(config.read_text())
    v["public_key_sha256"] = "0" * 64
    config.write_text(json.dumps(v))
    with pytest.raises(Denied):
        build(tmp_path)

    shutil.copyfile(ROOT / "production/config.json", config)
    rules = tmp_path / "production/rulesets.json"
    v = json.loads(rules.read_text())
    v["rulesets"][0]["enforcement"] = "disabled"
    rules.write_text(json.dumps(v))
    with pytest.raises(Denied):
        build(tmp_path)


def test_durable_boundary_requires_receipt_seal_and_independent_backup(synthetic):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    from execution_safeguards.journal import Journal
    from execution_safeguards.protocol import BACKUP_DOMAIN, canonical
    from execution_safeguards.receipt import ReceiptStore
    from production_adapter.boundary import verify_boundary

    class Memory:
        prefix = "synthetic-local-journal/"

        def __init__(self):
            self.data = {}

        def list(self):
            return sorted(self.data)

        def read(self, key):
            return self.data.get(key)

        def create(self, key, value):
            if key in self.data:
                raise Denied("duplicate")
            self.data[key] = value

    receipt = {
        "execution_lock_sha256": "a" * 64,
        "owner": "fixture",
        "execution_id": "one",
        "dataset_sha256": "b" * 64,
        "holdout_sha256": "c" * 64,
    }
    store = ReceiptStore(Memory())
    rsha = store.claim(receipt)
    core = {
        "receipt_sha256": rsha,
        "execution_lock_sha256": "a" * 64,
        "owner": "fixture",
        "execution_id": "one",
    }
    root, m = seal_fixture(synthetic)
    m["binding"] = core
    backend = Memory()
    journal = Journal(backend, core)
    tip = digest([])
    for stage, evidence in [
        ("receipt_verified", {"receipt_sha256": rsha, "authorization_sha256": "d" * 64}),
        ("feature_scoring_started", {"source_sha256": "b" * 64}),
        ("features_scored", {"checkpoint_sha256": digest(m)}),
    ]:
        tip = journal.append(stage, evidence, "worker", tip)
    key = Ed25519PrivateKey.generate()
    public = base64.b64encode(key.public_key().public_bytes_raw()).decode()
    backup = synthetic[-1] / "backup"
    shutil.copytree(root, backup)
    expected = {
        "schema": 1,
        "purpose": "independent-private-backup",
        "manifest_sha256": digest(m),
        "binding": core,
    }
    attestation = {
        "payload": expected,
        "signature": base64.b64encode(key.sign(BACKUP_DOMAIN + canonical(expected))).decode(),
    }
    with pytest.raises(Denied):
        verify_boundary(
            root,
            m,
            core,
            ids_sha(synthetic[1]),
            backup,
            attestation,
            public,
            store,
            receipt,
            journal,
            tip,
            "worker",
        )
    tip = journal.append(
        "predictions_sealed",
        {"checkpoint_sha256": digest(m), "backup_sha256": digest(expected)},
        "worker",
        tip,
    )
    assert verify_boundary(
        root,
        m,
        core,
        ids_sha(synthetic[1]),
        backup,
        attestation,
        public,
        store,
        receipt,
        journal,
        tip,
        "worker",
    )["ids"].shape == (80,)
    with pytest.raises(Denied):
        verify_boundary(
            root,
            m,
            core,
            ids_sha(synthetic[1]),
            root,
            attestation,
            public,
            store,
            receipt,
            journal,
            tip,
            "worker",
        )


@pytest.mark.parametrize("change", ["binding", "cohort", "dtype"])
def test_seal_rejects_changed_identity_or_layout(synthetic, change):
    from execution_safeguards.checkpoints import snapshot

    root, manifest = seal_fixture(synthetic)
    binding = manifest["binding"]
    cohort = ids_sha(synthetic[1])
    if change == "binding":
        binding = {"different_execution": True}
    elif change == "cohort":
        cohort = "0" * 64
    else:
        np.save(root / "scores.npy", np.zeros((4, 80), dtype=np.float32), allow_pickle=False)
        manifest = snapshot(root, list(manifest["files"]), binding)
    with pytest.raises(Denied):
        read_seal(root, manifest, binding, cohort)


def test_disk_preflight_fails_before_scoring_or_output(synthetic):
    def forbidden():
        pytest.fail("Features consumed despite failed disk preflight")
        yield

    target = synthetic[-1] / "blocked"
    with pytest.raises(Denied, match="disk"):
        score_batches(
            forbidden(),
            synthetic[1],
            {n: Dummy(n) for n in NAMES},
            target,
            synthetic[3],
            {"synthetic_only": True},
            10**30,
        )
    assert not target.exists()
