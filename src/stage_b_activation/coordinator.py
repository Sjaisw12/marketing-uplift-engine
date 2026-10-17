"""Integrated state machine; preparation exposes no production execution CLI.

Real construction requires a separately signed, time-limited exact-lock approval.
All tests instantiate the internal kernel with bounded synthetic sources/backends.
"""

import copy
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from execution_safeguards.bundle import atomic_json
from execution_safeguards.checkpoints import snapshot
from execution_safeguards.journal import GitJournalTransport, Journal
from execution_safeguards.protocol import RECOVERY_DOMAIN, Denied, digest, verify_signed_payload
from execution_safeguards.receipt import ReceiptStore, receipt_for
from production_adapter.scoring import evaluate_sealed, read_seal, score_batches

from . import authorization, backup
from .lock import verify
from .preflight import window
from .source import FrozenSource
from .transport import JournalRunner, PrivateRemote, StrictReceiptTransport


def production(root, private, instance, envelope=None, report=None):
    """No approval flag: absence of a valid OWNER signature leaves real execution disabled.

    This constructor is never called with production authorization during preparation.
    Metadata verification happens first; no source is constructed before the signature.
    """
    if not isinstance(envelope, dict) or not envelope.get("signature"):
        raise Denied("Stage B disabled: separate signed execution approval missing")
    root = Path(root)
    plan = verify(root)
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    if result.returncode:
        raise Denied("Cannot verify reviewed Git checkout")
    commit = result.stdout.strip()
    authorization.authorize(envelope, plan, commit, report)
    p = plan["parent"]
    runner = JournalRunner(root, p["receipt_ref"], p["journal_prefix"])
    store = ReceiptStore(StrictReceiptTransport(commit, runner))
    journal = GitJournalTransport(commit, p["dataset_sha256"], p["holdout"]["sha256"], runner)

    def identity():
        if verify(root) != plan:
            raise Denied("Changed reviewed execution files")
        current = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        if current.returncode or current.stdout.strip() != commit:
            raise Denied("Changed reviewed commit")

    source = FrozenSource(root, p)
    coordinator = _Coordinator(
        plan,
        commit,
        source,
        store,
        journal,
        PrivateRemote(root, plan["config"]["backup_branch"]),
        private,
        instance,
        identity,
    )
    source._guard = coordinator._at
    return coordinator


class _Coordinator:
    def __init__(
        self,
        plan,
        commit,
        source,
        receipt_store,
        journal_transport,
        remote,
        private,
        instance,
        identity,
        clock=None,
    ):
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", instance):
            raise Denied("Invalid executor instance")
        self.plan, self.commit = copy.deepcopy(plan), commit
        self.plan_sha = digest(plan)
        self.source, self.store, self.journal_transport = source, receipt_store, journal_transport
        self.remote = remote
        self.private, self.instance = Path(private), instance
        self.identity, self.clock = identity, clock or (lambda: datetime.now(UTC))
        self.receipt = self.journal = self.manifest = self.backup = None
        self.tip, self.blocked, self.started = digest([]), False, False
        self.active_window = None
        self.transfer_sha = None

    @property
    def predictions(self):
        return self.private / "predictions"

    def _check(self):
        if self.blocked or digest(self.plan) != self.plan_sha:
            raise Denied("Execution blocked/identity changed; read-only review required")
        self.identity()
        if self.active_window is not None:
            window(
                *self.active_window,
                self.clock(),
                self.plan["config"]["maximum_authorization_seconds"],
            )
        self.source.check()

    def _bind(self):
        p = self.plan["parent"]
        prefix = f"refs/tags/stage-b-journal/{p['dataset_sha256']}/{p['holdout']['sha256']}/"
        if self.journal_transport.prefix != prefix:
            raise Denied("Journal namespace differs from immutable cohort")
        self.binding = {
            "receipt_sha256": digest(self.receipt),
            "execution_lock_sha256": self.plan["lock_sha"],
            "execution_id": self.receipt["execution_id"],
            "owner": self.receipt["owner"],
        }
        self.journal = Journal(
            self.journal_transport, self.binding, p["config"]["public_key_base64"]
        )

    def _append(self, stage, evidence):
        # Sticky latch: even a failed readback cannot be retried as another action.
        self.blocked = True
        tip = self.journal.append(stage, evidence, self.instance, self.tip)
        events = self.journal.read(tip)
        if events[-1]["stage"] != stage or events[-1]["instance"] != self.instance:
            raise Denied("Durable transition readback/ownership failed")
        self.tip, self.blocked = tip, False

    def start(self, envelope, report):
        if self.started:
            raise Denied("Already attempted start; never claim again")
        self.started = True
        auth_sha = authorization.authorize(envelope, self.plan, self.commit, report, self.clock())
        self.active_window = (envelope["payload"]["not_before"], envelope["payload"]["expires_at"])
        self._check()
        self.remote.access()
        if self.journal_transport.list():
            raise Denied("Existing journal; recovery/review only")
        if self.remote.commit() is not None:
            raise Denied("Existing production backup campaign; review before receipt")
        self.receipt = receipt_for(envelope["payload"], auth_sha)
        self._bind()
        self.blocked = True
        self.store.claim(self.receipt)
        self.tip = digest([])
        self._append(
            "receipt_verified",
            {"authorization_sha256": auth_sha, "receipt_sha256": digest(self.receipt)},
        )
        self.private.mkdir(parents=True, exist_ok=False)
        atomic_json(
            self.private / "original-approval.json",
            {"authorization": envelope, "preflight": report},
        )

    def _at(self, stage):
        self._check()
        if self.journal is None:
            raise Denied("No authorized campaign")
        self.store.verify(self.receipt)
        events = self.journal.read(self.tip)
        functional = [e for e in events if e["stage"] != "recovery_approved"]
        if (
            not functional
            or functional[-1]["stage"] != stage
            or events[-1]["instance"] != self.instance
        ):
            raise Denied("Out-of-order action or unauthorized recovery writer")
        return events

    def score_features(self):
        self._at("receipt_verified")
        self._append(
            "feature_scoring_started", {"source_sha256": self.plan["parent"]["dataset_sha256"]}
        )
        self._at("feature_scoring_started")
        self.manifest = score_batches(
            self.source.features(),
            self.source.ids,
            self.source.models(),
            self.predictions,
            self.plan["parent"]["settings"],
            self.binding,
            self.plan["config"].get("disk_reserve_bytes", 8589934592),
        )
        read_seal(
            self.predictions, self.manifest, self.binding, self.plan["parent"]["holdout"]["sha256"]
        )
        self._check()
        self._append("features_scored", {"checkpoint_sha256": digest(self.manifest)})
        return copy.deepcopy(self.manifest)

    def _checkpoint(self):
        if self.manifest is None:
            raise Denied("No exact prediction checkpoint")
        events = self.journal.read(self.tip)
        expected = next(
            e["evidence"]["checkpoint_sha256"]
            for e in reversed(events)
            if "checkpoint_sha256" in e["evidence"]
        )
        if digest(self.manifest) != expected:
            raise Denied("Checkpoint differs from durable journal")
        return read_seal(
            self.predictions, self.manifest, self.binding, self.plan["parent"]["holdout"]["sha256"]
        )

    def export(self, age_binary):
        self._at("features_scored")
        self._checkpoint()
        self.blocked = True
        transfer = backup.export_checkpoint(
            self.predictions,
            self.manifest,
            self.private / "export",
            self.plan["config"],
            age_binary,
        )
        self.transfer_sha = digest(transfer)
        self.blocked = False
        return transfer

    def publish(self, transfer):
        self._at("features_scored")
        self._checkpoint()
        path = self.private / "export/publish"
        if self.transfer_sha is None or digest(transfer) != self.transfer_sha:
            raise Denied(
                "Only this coordinator’s exact completed encrypted export may be published"
            )
        backup.verify_transfer(path, self.manifest, transfer, self.plan["config"])
        self.blocked = True
        commit = self.remote.publish(path, transfer)
        if self.remote.commit() != commit:
            raise Denied("Ambiguous backup publication; reconcile read-only")
        self.blocked = False
        return commit

    def seal(self, transfer, signed_mac_restore, fresh_report):
        self._at("features_scored")
        self._checkpoint()
        proof = backup.verify_backup(
            self.predictions,
            self.manifest,
            self.private / "export/publish",
            transfer,
            signed_mac_restore,
            self.remote,
            self.plan,
            self.commit,
            fresh_report,
            self.clock(),
        )
        self.backup = copy.deepcopy((transfer, signed_mac_restore, fresh_report))
        atomic_json(
            self.private / "owner-backup-proof.json",
            {"transfer": transfer, "attestation": signed_mac_restore, "preflight": fresh_report},
        )
        self._append(
            "predictions_sealed",
            {"checkpoint_sha256": digest(self.manifest), "backup_sha256": proof},
        )

    def evaluate(self):
        self._at("predictions_sealed")
        self._checkpoint()
        if self.backup is None:
            raise Denied("No independently restored encrypted off-workspace backup")
        transfer, signature, report = self.backup
        proof = backup.verify_backup(
            self.predictions,
            self.manifest,
            self.private / "export/publish",
            transfer,
            signature,
            self.remote,
            self.plan,
            self.commit,
            report,
            self.clock(),
        )
        events = self.journal.read(self.tip)
        seal = next(e for e in reversed(events) if e["stage"] == "predictions_sealed")
        if seal["evidence"]["backup_sha256"] != proof:
            raise Denied("Backup attestation differs from durable seal")
        self._append("outcome_access_started", {"checkpoint_sha256": digest(self.manifest)})
        self._at("outcome_access_started")  # full durable readback BEFORE constructing any reader
        result = evaluate_sealed(
            self.source.outcomes(),
            self.predictions,
            self.manifest,
            self.binding,
            self.plan["parent"]["holdout"]["sha256"],
            self.plan["parent"]["settings"],
        )
        self._check()
        self._checkpoint()
        results = self.private / "results"
        results.mkdir(exist_ok=False)
        arrays = {"point": result["point"], "covariance": result["covariance"]}
        for method in ("iid", "stratified"):
            for name in (
                "estimate",
                "standard_error",
                "pointwise_interval",
                "simultaneous_interval",
                "draws",
            ):
                if name in result[method]:
                    arrays[f"{method}-{name}"] = result[method][name]
        if result["stratified_covariance"] is not None:
            arrays["stratified-covariance"] = result["stratified_covariance"]
        for name, array in arrays.items():
            with (results / f"{name}.npy").open("xb") as out:
                np.save(out, array, allow_pickle=False)
                out.flush()
                os.fsync(out.fileno())
        atomic_json(
            results / "metadata.json",
            {
                "binding": self.binding,
                "prediction_manifest_sha256": digest(self.manifest),
                "backup_attestation_sha256": proof,
                "family": result["family"],
                "scenarios": result["keys"],
                "primary": {
                    "policy": "no-targeting",
                    "assignments": 0,
                    "hypothetical_spending": 0,
                    "incremental_gain_relative_to_none": 0,
                    "identity_not_optimality_proof": True,
                },
                "iid_critical": result["iid"]["critical"],
                "stratified_critical": result["stratified"].get("critical"),
                "stratum_counts": result["stratum_counts"],
                "stratified_status": result["stratified"]["status"],
                "units": "visits per eligible record",
                "interpretation": (
                    "assumption-dependent; nominal intervals conditional on fitted policies"
                ),
            },
        )
        manifest = snapshot(results, sorted(p.name for p in results.iterdir()), self.binding)
        atomic_json(results / "result-manifest.json", manifest)
        self._append("completed", {"result_manifest_sha256": digest(manifest)})
        return result

    def recover(
        self,
        envelope,
        original_report,
        manifest,
        transfer,
        signed_backup,
        fresh_report,
        expected_tip,
        signed_recovery,
    ):
        if self.started or self.receipt is not None:
            raise Denied("Recovery requires a fresh coordinator")
        self.started = True
        sha = authorization.authorize(
            envelope, self.plan, self.commit, original_report, self.clock(), historical=True
        )
        self.receipt = receipt_for(envelope["payload"], sha)
        self.store.verify(self.receipt)  # never claim again
        self._bind()
        events = self.journal.read(expected_tip)
        functional = [e for e in events if e["stage"] != "recovery_approved"]
        if not functional or functional[-1]["stage"] not in {
            "features_scored",
            "predictions_sealed",
        }:
            raise Denied(
                "Interrupted action/consumed outcome access: audit only; no automatic replay"
            )
        if events[-1]["instance"] == self.instance:
            raise Denied("Recovery must name a new instance and terminate the previous worker")
        self.tip, self.manifest = expected_tip, copy.deepcopy(manifest)
        self._checkpoint()
        proof = backup.verify_backup(
            self.predictions,
            manifest,
            self.private / "export/publish",
            transfer,
            signed_backup,
            self.remote,
            self.plan,
            self.commit,
            fresh_report,
            self.clock(),
        )
        if (
            functional[-1]["stage"] == "predictions_sealed"
            and functional[-1]["evidence"]["backup_sha256"] != proof
        ):
            raise Denied("Recovery backup differs from sealed journal proof")
        p = signed_recovery.get("payload", {})
        expected = {
            "schema": 1,
            "purpose": "same-campaign-recovery",
            "binding": self.binding,
            "journal_sha256": digest(events),
            "new_instance": self.instance,
            "previous_worker_terminated": True,
            "not_before": p.get("not_before"),
            "expires_at": p.get("expires_at"),
        }
        verify_signed_payload(
            signed_recovery,
            expected,
            self.plan["parent"]["config"]["public_key_base64"],
            RECOVERY_DOMAIN,
        )
        self.active_window = (expected["not_before"], expected["expires_at"])
        self._check()
        self._append("recovery_approved", {"signed_recovery": copy.deepcopy(signed_recovery)})
        self.backup = copy.deepcopy((transfer, signed_backup, fresh_report))
