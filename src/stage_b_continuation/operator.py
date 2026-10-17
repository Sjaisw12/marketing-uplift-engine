"""Explicit restart at the published-backup boundary; no implicit retry or outcome replay."""

import copy
import fcntl
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from execution_safeguards.bundle import atomic_json
from execution_safeguards.journal import GitJournalTransport
from execution_safeguards.protocol import Denied, digest, strict_json
from execution_safeguards.receipt import ReceiptStore, receipt_for
from stage_b_activation import backup
from stage_b_activation.coordinator import _Coordinator
from stage_b_activation.source import FrozenSource
from stage_b_activation.transport import JournalRunner, PrivateRemote, StrictReceiptTransport

from . import approval
from .journal import Journal
from .lock import verify


class Lease:
    """Kernel-held local exclusion, released on death; never an automatic takeover grant."""

    def __init__(self, private):
        private = Path(private).absolute()
        if not private.parent.is_dir() or private.is_symlink():
            raise Denied("Explicit existing private parent and non-symlink state required")
        self.path = private.parent / ("." + private.name + ".worker.lock")
        self.fd = os.open(self.path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(self.fd)
            self.fd = None
            raise Denied("Another local worker holds this campaign") from exc

    def check(self):
        if self.fd is None or os.fstat(self.fd).st_ino != self.path.stat().st_ino:
            raise Denied("Worker closed or local lease replaced")

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None


def production(
    root, private, instance, authorization, report, continuation=None, signed_backup=None
):
    """Future signed execution only. No caller-injected key, source, clock or transport."""
    root, private = Path(root), Path(private)
    plan = verify(root)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    now = datetime.now(UTC)
    if continuation is None:
        approval.start(authorization, plan, commit, report, now)
    else:
        pause = strict_json((private / "pause.json").read_bytes())
        if pause["authorization"] != authorization:
            raise Denied("Original signed grant changed")
        approval.start(
            authorization, plan, commit, pause["original_preflight"], now, historical=True
        )
        approval.continuation(continuation, plan, commit, pause, instance, report, now)

    def identity():
        if (
            verify(root) != plan
            or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
            != commit
        ):
            raise Denied("Changed reviewed child identity")

    p = plan["parent"]
    runner = JournalRunner(root, p["receipt_ref"], p["journal_prefix"])
    source = FrozenSource(root, p)
    lease = Lease(private)
    try:
        c = Operator(
            plan,
            commit,
            source,
            ReceiptStore(StrictReceiptTransport(commit, runner)),
            GitJournalTransport(commit, p["dataset_sha256"], p["holdout"]["sha256"], runner),
            PrivateRemote(root, plan["config"]["backup_branch"]),
            private,
            instance,
            identity,
            lease=lease,
        )
        source._guard = c._at
        if continuation is not None:
            c.resume(pause, continuation, signed_backup, report)
        return c
    except BaseException:
        lease.close()
        raise


class Operator(_Coordinator):
    """Kernel also accepts synthetic components for isolated subprocess tests only."""

    def __init__(self, *args, lease, **kwargs):
        super().__init__(*args, **kwargs)
        self.lease, self.original, self.resumed = lease, None, False

    def close(self):
        self.blocked = True
        self.lease.close()

    def _check(self):
        self.lease.check()
        super()._check()

    def _bind(self):
        super()._bind()
        self.journal = Journal(self.journal_transport, self.binding, self.plan, self.commit)

    def _at(self, stage):
        self._check()
        if self.journal is None:
            raise Denied("No authorized campaign")
        self.store.verify(self.receipt)
        events = self.journal.read(self.tip)
        functional = [e for e in events if e["stage"] != "continuation_approved"]
        if (
            not functional
            or functional[-1]["stage"] != stage
            or events[-1]["instance"] != self.instance
        ):
            raise Denied("Wrong stage or obsolete worker")
        return events

    def start(self, envelope, report):
        if self.started or self.private.exists():
            raise Denied("Existing state or prior start attempt; never claim again")
        self.started = True
        auth_sha = approval.start(envelope, self.plan, self.commit, report, self.clock())
        self.active_window = (envelope["payload"]["not_before"], envelope["payload"]["expires_at"])
        self._check()
        self.remote.access()
        if self.journal_transport.list() or self.remote.commit() is not None:
            raise Denied("Existing campaign; no fresh claim")
        self.receipt = receipt_for(envelope["payload"], auth_sha)
        self._bind()
        self.blocked = True
        self.store.claim(self.receipt)
        self._append(
            "receipt_verified",
            {"authorization_sha256": auth_sha, "receipt_sha256": digest(self.receipt)},
        )
        self.blocked = True
        self.private.mkdir(mode=0o700)
        self.original = copy.deepcopy({"authorization": envelope, "preflight": report})
        atomic_json(self.private / "original-approval.json", self.original)
        self.blocked = False

    def publish(self, transfer):
        commit = super().publish(transfer)
        self._append(
            "backup_published",
            {
                "checkpoint_sha256": digest(self.manifest),
                "transfer_sha256": digest(transfer),
                "private_commit": commit,
            },
        )
        self.blocked = True
        pause = {
            "schema": 1,
            "execution_lock_sha256": self.plan["lock_sha"],
            "reviewed_commit": self.commit,
            "authorization": self.original["authorization"],
            "original_preflight": self.original["preflight"],
            "receipt": self.receipt,
            "manifest": self.manifest,
            "transfer": transfer,
            "private_commit": commit,
            "journal_tip": self.tip,
            "previous_instance": self.instance,
        }
        atomic_json(self.private / "pause.json", pause)
        self.close()  # Outcome-capable continuation ALWAYS needs a new signed grant/worker.
        return copy.deepcopy(pause)

    def resume(self, pause, continuation, signed_backup, report):
        if self.started or self.receipt is not None:
            raise Denied("Continuation requires a fresh operator")
        self.started = True
        if strict_json((self.private / "pause.json").read_bytes()) != pause:
            raise Denied("Private pause bytes changed")
        if (
            pause["execution_lock_sha256"] != self.plan["lock_sha"]
            or pause["reviewed_commit"] != self.commit
        ):
            raise Denied("Changed paused identity")
        if pause["previous_instance"] == self.instance:
            raise Denied("New operator instance required")
        original = {
            "authorization": pause["authorization"],
            "preflight": pause["original_preflight"],
        }
        if strict_json((self.private / "original-approval.json").read_bytes()) != original:
            raise Denied("Original authorization record changed")
        original_sha = approval.start(
            pause["authorization"],
            self.plan,
            self.commit,
            pause["original_preflight"],
            self.clock(),
            historical=True,
        )
        approval.continuation(
            continuation, self.plan, self.commit, pause, self.instance, report, self.clock()
        )
        self.active_window = (
            continuation["payload"]["not_before"],
            continuation["payload"]["expires_at"],
        )
        self._check()
        self.receipt = receipt_for(pause["authorization"]["payload"], original_sha)
        if self.receipt != pause["receipt"]:
            raise Denied("Changed original receipt")
        self.store.verify(self.receipt)  # NEVER claim, rescore, re-encrypt or republish.
        self._bind()
        self.tip, self.manifest = pause["journal_tip"], copy.deepcopy(pause["manifest"])
        events = self.journal.read(self.tip)
        if (
            not events
            or events[-1]["stage"] != "backup_published"
            or events[-1]["instance"] != pause["previous_instance"]
        ):
            raise Denied("Not at exact durable publication pause; audit only")
        if events[-1]["evidence"] != {
            "checkpoint_sha256": digest(self.manifest),
            "transfer_sha256": digest(pause["transfer"]),
            "private_commit": pause["private_commit"],
        }:
            raise Denied("Paused checkpoint differs from durable publication")
        self._checkpoint()
        if self.remote.commit() != pause["private_commit"]:
            raise Denied("Private backup commit changed")
        backup.verify_backup(
            self.predictions,
            self.manifest,
            self.private / "export/publish",
            pause["transfer"],
            signed_backup,
            self.remote,
            self.plan,
            self.commit,
            report,
            self.clock(),
        )
        self.backup = copy.deepcopy((pause["transfer"], signed_backup, report))
        self._append(
            "continuation_approved",
            {
                "approval": continuation,
                "preflight": report,
                "pause": pause,
            },
        )
        self.blocked = True
        atomic_json(
            self.private / "continuation-approval.json",
            {
                "approval": continuation,
                "preflight": report,
                "backup_attestation": signed_backup,
            },
        )
        self.resumed, self.blocked = True, False

    def seal(self, transfer, signed_mac_restore, fresh_report):
        if not self.resumed:
            raise Denied("New signed continuation and independent backup required")
        self._at("backup_published")
        self._checkpoint()
        if (transfer, signed_mac_restore, fresh_report) != self.backup:
            raise Denied("Changed continuation backup evidence")
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
        self.blocked = True
        atomic_json(
            self.private / "owner-backup-proof.json",
            {"transfer": transfer, "attestation": signed_mac_restore, "preflight": fresh_report},
        )
        self.blocked = False
        self._append(
            "predictions_sealed",
            {"checkpoint_sha256": digest(self.manifest), "backup_sha256": proof},
        )

    def recover(self, *args, **kwargs):
        raise Denied(
            "Legacy recovery disabled in child protocol; use exact publication continuation"
        )
