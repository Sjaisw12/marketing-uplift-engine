"""Fail-closed coordinator exercised ONLY with bounded, declared synthetic fixtures."""

import base64
import copy
import hashlib
import os
import tomllib
from datetime import datetime
from pathlib import Path

import numpy as np

from .bundle import atomic_json
from .checkpoints import snapshot, verify_backup, verify_files
from .interfaces import (
    NAMES,
    evaluate_synthetic,
    load_predictions,
    save_predictions,
    score_synthetic,
    validate_predictions,
)
from .journal import Journal
from .lock import verify
from .protocol import (
    RECOVERY_DOMAIN,
    Denied,
    digest,
    file_hash,
    strict_json,
    verify_authorization,
    verify_signed_payload,
)
from .receipt import ReceiptStore, receipt_for

REAL_DATASET = "2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc"


class Coordinator:
    @classmethod
    def production(cls, *args, **kwargs):
        # No local boolean, claimed backup or signed test envelope can remove this gate.
        raise Denied("Stage B disabled: production key unset; later reviewed lock required")

    def __init__(
        self,
        repository,
        fixture_root,
        reviewed_fixture_sha256,
        receipt_transport,
        journal_transport,
        private_root,
        instance,
    ):
        self.repository = Path(repository)
        self.lock_sha = verify(self.repository)
        self.fixture_root = Path(fixture_root)
        path = self.fixture_root / "reviewed-fixture.json"
        if file_hash(path) != reviewed_fixture_sha256:
            raise Denied("Unreviewed synthetic artifact manifest")
        self.trusted = strict_json(path.read_bytes())
        if (
            self.trusted.get("synthetic_only") is not True
            or not 2 <= self.trusted["rows"] <= 4096
            or self.trusted["dataset_sha256"] == REAL_DATASET
        ):
            raise Denied("Real data forbidden by preparation coordinator")
        self.fixture_sha = reviewed_fixture_sha256
        self.public_key = self.trusted["authorization"]["public_key"]
        self.models = {n: self.fixture_root / "models" / f"{n}.json" for n in NAMES}
        self.settings = tomllib.loads((self.repository / "configs/phase9.toml").read_text())
        self.store = ReceiptStore(receipt_transport)
        self.journal_transport = journal_transport
        self.private = Path(private_root)
        self.instance = instance
        self.receipt = self.journal = None
        self.tip = digest([])
        self.manifest = None
        self.backup = None
        self._check_identities()

    def expected_authorization(self):
        auth = self.trusted["authorization"]
        return {
            "schema": 1,
            "purpose": "one-final-holdout-evaluation",
            "execution_lock_sha256": self.lock_sha,
            "model_manifest_sha256": digest(self.trusted["models"]),
            "dataset_sha256": self.trusted["dataset_sha256"],
            "holdout_sha256": self.trusted["ids_sha256"],
            "parameters_sha256": digest(
                {"settings": self.settings, "fixture_sha256": self.fixture_sha}
            ),
            "owner": auth["owner"],
            "execution_id": auth["execution_id"],
            "public_key_sha256": hashlib.sha256(base64.b64decode(self.public_key)).hexdigest(),
            "not_before": auth["not_before"],
            "expires_at": auth["expires_at"],
        }

    def _check_identities(self):
        try:
            self._identities()
        except OSError as exc:
            raise Denied("Required model/dataset/checkpoint identity missing") from exc

    def _identities(self):
        if verify(self.repository) != self.lock_sha:
            raise Denied("Changed implementation lock")
        if file_hash(self.fixture_root / "reviewed-fixture.json") != self.fixture_sha:
            raise Denied("Changed trusted policy/dataset/execution identity")
        if strict_json((self.fixture_root / "reviewed-fixture.json").read_bytes()) != self.trusted:
            raise Denied("In-memory trusted bindings changed")
        if tomllib.loads((self.repository / "configs/phase9.toml").read_text()) != self.settings:
            raise Denied("Frozen evaluation settings changed")
        for name, path in self.models.items():
            if file_hash(path) != self.trusted["models"][name]:
                raise Denied("Changed model identity")
        hashes = {n: file_hash(self.fixture_root / n) for n in ("features.json", "outcomes.json")}
        if (
            hashes != self.trusted["source_files"]
            or digest(hashes) != self.trusted["dataset_sha256"]
        ):
            raise Denied("Changed dataset identity")

    def _bind_journal(self):
        expected_prefix = (
            f"refs/tags/stage-b-journal/{self.receipt['dataset_sha256']}/"
            f"{self.receipt['holdout_sha256']}/"
        )
        if self.journal_transport.prefix != expected_prefix:
            raise Denied("Journal namespace does not match the fixed receipt cohort")
        self.binding = {
            "receipt_sha256": digest(self.receipt),
            "execution_lock_sha256": self.lock_sha,
            "execution_id": self.receipt["execution_id"],
            "owner": self.receipt["owner"],
        }
        self.journal = Journal(self.journal_transport, self.binding, self.public_key)

    def start(self, authorization, now=None):
        if self.receipt is not None:
            raise Denied("Coordinator already started")
        self._check_identities()
        auth_sha = verify_authorization(
            authorization, self.expected_authorization(), self.public_key, now
        )
        receipt = receipt_for(self.expected_authorization(), auth_sha)
        self.store.claim(receipt)
        self.receipt = receipt
        self._bind_journal()
        self._append(
            "receipt_verified",
            {"authorization_sha256": auth_sha, "receipt_sha256": digest(receipt)},
        )

    def _append(self, stage, evidence):
        self.tip = self.journal.append(stage, evidence, self.instance, self.tip)

    def _at(self, expected_stage):
        self._check_identities()
        if self.journal is None:
            raise Denied("No verified authorization and receipt")
        self.store.verify(self.receipt)
        events = self.journal.read(self.tip)
        if (
            not events
            or events[-1]["instance"] != self.instance
            or next(
                (e["stage"] for e in reversed(events) if e["stage"] != "recovery_approved"), None
            )
            != expected_stage
        ):
            raise Denied("Unauthorized writer or out-of-order transition")

    def score_features(self):
        self._at("receipt_verified")
        self._append("feature_scoring_started", {"source_sha256": self.trusted["dataset_sha256"]})
        # This is the ONLY feature input interface in preparation: declared tiny JSON,
        # never Parquet, SQL, arbitrary loader callbacks or final holdout membership.
        raw = strict_json((self.fixture_root / "features.json").read_bytes())
        if set(raw) != {"row_id", "columns", "x"}:
            raise Denied("Feature interface rejects labels/post-treatment columns")
        if any(type(v) is not int or not 0 <= v < 2**64 for v in raw["row_id"]):
            raise Denied("Source identifiers must be exact unsigned integers")
        ids, x = np.array(raw["row_id"], dtype=np.uint64), np.array(raw["x"], dtype=float)
        values = score_synthetic(
            ids,
            x,
            raw["columns"],
            self.models,
            self.trusted["models"],
            self.settings,
            self.trusted["ids_sha256"],
        )
        self.manifest = save_predictions(self.private, values, self.binding)
        atomic_json(self.private / "prediction-manifest.json", self.manifest)
        self._append("features_scored", {"checkpoint_sha256": digest(self.manifest)})
        return copy.deepcopy(self.manifest)

    def seal(self, restored_backup, signed_backup):
        self._at("features_scored")
        self._checkpoint_matches()
        proof = verify_backup(
            self.private, restored_backup, self.manifest, signed_backup, self.public_key
        )
        self.backup = (Path(restored_backup), copy.deepcopy(signed_backup))
        self._append(
            "predictions_sealed",
            {"checkpoint_sha256": digest(self.manifest), "backup_sha256": proof},
        )

    def evaluate(self):
        self._at("predictions_sealed")
        self._checkpoint_matches()
        if self.backup is None:
            raise Denied("No independently attested restored backup")
        backup_root, attestation = self.backup
        verify_backup(self.private, backup_root, self.manifest, attestation, self.public_key)
        sealed = load_predictions(self.private, self.manifest, self.binding)
        validate_predictions(sealed, self.trusted["ids_sha256"])
        self._append("outcome_access_started", {"checkpoint_sha256": digest(self.manifest)})
        raw = strict_json((self.fixture_root / "outcomes.json").read_bytes())
        if set(raw) != {"row_id", "treatment", "visit"}:
            raise Denied("Outcome projection mismatch")
        if raw["row_id"] != sealed["ids"].tolist():
            raise Denied("Outcome alignment mismatch")
        t, y = np.asarray(raw["treatment"]), np.asarray(raw["visit"])
        if t.shape != sealed["ids"].shape or y.shape != t.shape:
            raise Denied("Outcome length mismatch")
        result = evaluate_synthetic(sealed, t, y, self.settings)
        result_root = self.private / "results"
        result_root.mkdir(exist_ok=False)
        # Preserve sufficient numeric result evidence without inventing business claims.
        arrays = {"point": result["point"], "covariance": result["covariance"]}
        for method in ("iid", "stratified"):
            if "estimate" in result[method]:
                for field in (
                    "estimate",
                    "standard_error",
                    "pointwise_interval",
                    "simultaneous_interval",
                ):
                    arrays[f"{method}-{field}"] = result[method][field]
        if result["stratified_covariance"] is not None:
            arrays["stratified_covariance"] = result["stratified_covariance"]
        for name, array in arrays.items():
            with (result_root / f"{name}.npy").open("xb") as stream:
                np.save(stream, array, allow_pickle=False)
                stream.flush()
                os.fsync(stream.fileno())
        atomic_json(
            result_root / "metadata.json",
            {
                "synthetic_only": True,
                "settings": self.settings,
                "family": result["family"],
                "scenarios": result["keys"],
                "iid_critical": result["iid"]["critical"],
                "stratified_status": result["stratified"]["status"],
            },
        )
        results_manifest = snapshot(
            result_root, sorted(p.name for p in result_root.iterdir()), self.binding
        )
        atomic_json(result_root / "result-manifest.json", results_manifest)
        self._append("completed", {"result_manifest_sha256": digest(results_manifest)})
        return result

    def _checkpoint_matches(self):
        if self.manifest is None or self.manifest["binding"] != self.binding:
            raise Denied("No exact prediction manifest")
        expected = next(
            e["evidence"]["checkpoint_sha256"]
            for e in reversed(self.journal.read(self.tip))
            if "checkpoint_sha256" in e["evidence"]
        )
        if digest(self.manifest) != expected:
            raise Denied("Prediction manifest differs from durable journal")

    def recovery_expected(self, events, new_instance, expires_at, not_before):
        return {
            "schema": 1,
            "purpose": "same-campaign-recovery",
            "binding": self.binding,
            "journal_sha256": digest(events),
            "new_instance": new_instance,
            "previous_worker_terminated": True,
            "not_before": not_before,
            "expires_at": expires_at,
        }

    def recover(
        self,
        original_authorization,
        manifest,
        backup_root,
        signed_backup,
        expected_tip,
        signed_recovery,
        now,
    ):
        if self.receipt is not None:
            raise Denied("Recovery requires a fresh coordinator instance")
        self._check_identities()
        auth_sha = verify_authorization(
            original_authorization, self.expected_authorization(), self.public_key, now
        )
        self.receipt = receipt_for(self.expected_authorization(), auth_sha)
        self.store.verify(self.receipt)  # NEVER claim again.
        self._bind_journal()
        events = self.journal.read(expected_tip)
        last = next(
            (e["stage"] for e in reversed(events) if e["stage"] != "recovery_approved"), None
        )
        if last not in {"features_scored", "predictions_sealed"}:
            raise Denied("Ambiguous action or completed analysis; recovery cannot repeat it")
        if manifest is None or manifest["binding"] != self.binding:
            raise Denied("Recovery checkpoint belongs to different execution")
        if manifest is None or digest(manifest) != next(
            e["evidence"]["checkpoint_sha256"]
            for e in reversed(events)
            if "checkpoint_sha256" in e["evidence"]
        ):
            raise Denied("Recovery checkpoint does not match durable seal")
        verify_files(self.private, manifest)
        verify_backup(self.private, backup_root, manifest, signed_backup, self.public_key)
        p = signed_recovery.get("payload", {})
        expected = self.recovery_expected(
            events, self.instance, p.get("expires_at"), p.get("not_before")
        )
        verify_signed_payload(signed_recovery, expected, self.public_key, RECOVERY_DOMAIN)
        try:
            start, end = (datetime.fromisoformat(expected[k]) for k in ("not_before", "expires_at"))
            if start.utcoffset() is None or end.utcoffset() is None or not start <= now < end:
                raise Denied("Recovery approval expired/not yet valid")
        except (ValueError, TypeError) as exc:
            raise Denied("Invalid recovery validity") from exc
        self.tip = expected_tip
        self._append("recovery_approved", {"signed_recovery": copy.deepcopy(signed_recovery)})
        self.manifest = copy.deepcopy(manifest)
        self.backup = (Path(backup_root), copy.deepcopy(signed_backup))
