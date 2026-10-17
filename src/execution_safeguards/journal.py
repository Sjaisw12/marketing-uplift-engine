"""Fixed-sequence create-only journal; no live command runner is configured."""

import re

from .protocol import (
    RECOVERY_DOMAIN,
    Denied,
    canonical,
    digest,
    sha,
    strict_json,
    verify_signed_payload,
)
from .receipt import AmbiguousWrite, GitHubTransport

STAGES = (
    "receipt_verified",
    "feature_scoring_started",
    "features_scored",
    "predictions_sealed",
    "outcome_access_started",
    "completed",
)
EVIDENCE = {
    "receipt_verified": {"authorization_sha256", "receipt_sha256"},
    "feature_scoring_started": {"source_sha256"},
    "features_scored": {"checkpoint_sha256"},
    "predictions_sealed": {"checkpoint_sha256", "backup_sha256"},
    "outcome_access_started": {"checkpoint_sha256"},
    "completed": {"result_manifest_sha256"},
}


class GitJournalTransport(GitHubTransport):
    def __init__(self, reviewed_commit, dataset_sha, holdout_sha, runner=None):
        super().__init__(reviewed_commit, runner)
        self.prefix = f"refs/tags/stage-b-journal/{sha(dataset_sha)}/{sha(holdout_sha)}/"

    def check_ref(self, ref):
        if not re.fullmatch(re.escape(self.prefix) + r"[0-9]{6}", ref):
            raise Denied("Journal ref outside the fixed campaign")

    def list(self):
        output = self.command(["ls-remote", "--refs", self.remote, self.prefix + "*"])
        refs = []
        for line in output.splitlines():
            oid, ref = line.split()
            self.check_ref(ref)
            if not re.fullmatch(r"[0-9a-f]{40}", oid):
                raise Denied("Invalid journal object")
            refs.append(ref)
        return sorted(refs)

    def read(self, ref):
        self.check_ref(ref)
        value = self.command(["ls-remote", "--refs", self.remote, ref]).split()
        if not value:
            return None
        if len(value) != 2 or value[1] != ref or not re.fullmatch(r"[0-9a-f]{40}", value[0]):
            raise Denied("Ambiguous journal reference")
        self.command(["fetch", "--no-tags", self.remote, ref])
        raw = self.command(["cat-file", "tag", value[0]])
        header, separator, body = raw.partition("\n\n")
        if not separator or not header.startswith(f"object {self.commit}\ntype commit\n"):
            raise Denied("Journal code commit mismatch")
        return strict_json(body)

    def create(self, ref, payload):
        self.check_ref(ref)
        body = (
            f"object {self.commit}\ntype commit\ntag {ref[10:]}\n"
            "tagger Execution journal <journal@invalid> 0 +0000\n\n"
        ).encode()
        oid = self.command(["mktag"], body + canonical(payload) + b"\n").strip()
        if not re.fullmatch(r"[0-9a-f]{40}", oid):
            raise Denied("Invalid journal tag identity")
        output = self.command(
            ["push", "--porcelain", f"--force-with-lease={ref}:", self.remote, f"{oid}:{ref}"]
        )
        if "\t[new tag]" not in output:
            raise AmbiguousWrite("No confirmed NEW journal tag; stop for read-only reconciliation")


class Journal:
    def __init__(self, transport, binding, public_key=None):
        self.transport = transport
        self.binding = dict(binding)
        self.public_key = public_key

    def read(self, expected_tip=None):
        refs = self.transport.list()
        if len(refs) > 128:
            raise Denied("Journal exceeds bounded campaign history; review required")
        events, index, writer = [], 0, None
        for number, ref in enumerate(refs):
            if ref != self.transport.prefix + f"{number:06d}":
                raise Denied("Journal gap or unexpected ref")
            event = self.transport.read(ref)
            if (
                not isinstance(event, dict)
                or event.get("binding") != self.binding
                or type(event.get("sequence")) is not int
                or event.get("sequence") != number
                or event.get("previous_sha256") != (digest(events[-1]) if events else None)
                or set(event)
                != {"binding", "sequence", "previous_sha256", "stage", "instance", "evidence"}
            ):
                raise Denied("Journal tampered or different execution")
            if event["stage"] == "recovery_approved":
                if not events or index not in {3, 4}:
                    raise Denied("Recovery outside an interrupted campaign")
                if set(event["evidence"]) != {"signed_recovery"} or self.public_key is None:
                    raise Denied("Recovery evidence missing")
                signed = event["evidence"]["signed_recovery"]
                p = signed.get("payload", {})
                expected = {
                    "schema": 1,
                    "purpose": "same-campaign-recovery",
                    "binding": self.binding,
                    "journal_sha256": digest(events),
                    "new_instance": event["instance"],
                    "previous_worker_terminated": True,
                    "not_before": p.get("not_before"),
                    "expires_at": p.get("expires_at"),
                }
                verify_signed_payload(signed, expected, self.public_key, RECOVERY_DOMAIN)
                writer = event["instance"]
            else:
                if index >= len(STAGES) or event["stage"] != STAGES[index]:
                    raise Denied("Journal stage out of order")
                if writer is not None and writer != event["instance"]:
                    raise Denied("Changed journal writer without recovery authorization")
                if set(event["evidence"]) != EVIDENCE[event["stage"]]:
                    raise Denied("Missing required journal checkpoint evidence")
                for value in event["evidence"].values():
                    sha(value)
                if event["stage"] == "receipt_verified" and (
                    event["evidence"]["receipt_sha256"] != self.binding["receipt_sha256"]
                ):
                    raise Denied("Receipt evidence differs from campaign")
                if event["stage"] in {"predictions_sealed", "outcome_access_started"}:
                    previous = next(
                        e["evidence"]["checkpoint_sha256"]
                        for e in reversed(events)
                        if "checkpoint_sha256" in e["evidence"]
                    )
                    if previous != event["evidence"]["checkpoint_sha256"]:
                        raise Denied("Checkpoint changed after prediction seal")
                writer = event["instance"]
                index += 1
            if not isinstance(event["instance"], str) or not re.fullmatch(
                r"[A-Za-z0-9_.-]{1,128}", event["instance"]
            ):
                raise Denied("Invalid executor instance")
            events.append(event)
        if expected_tip is not None and digest(events) != expected_tip:
            raise Denied("Journal truncated, advanced or changed")
        return events

    def append(self, stage, evidence, instance, expected_tip):
        events = self.read(expected_tip)
        event = {
            "binding": self.binding,
            "sequence": len(events),
            "previous_sha256": digest(events[-1]) if events else None,
            "stage": stage,
            "instance": instance,
            "evidence": evidence,
        }
        ref = self.transport.prefix + f"{len(events):06d}"

        # Validate the proposed sequence before any write using an in-memory view.
        class View:
            prefix = self.transport.prefix

            def list(_):
                return [_.prefix + f"{i:06d}" for i in range(len(events) + 1)]

            def read(_, name):
                return [*events, event][int(name.rsplit("/", 1)[1])]

        Journal(View(), self.binding, self.public_key).read()
        try:
            self.transport.create(ref, event)
            if self.transport.read(ref) != event:
                raise AmbiguousWrite("Journal readback mismatch; stop")
        except OSError as exc:
            raise AmbiguousWrite("Unknown journal write; no retry or takeover") from exc
        return digest([*events, event])
