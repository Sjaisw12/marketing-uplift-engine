"""Same fixed Git namespace, with publication and independently signed continuation stages."""

from execution_safeguards.journal import EVIDENCE
from execution_safeguards.protocol import Denied, digest, sha
from execution_safeguards.receipt import AmbiguousWrite

from .approval import continuation

STAGES = (
    "receipt_verified",
    "feature_scoring_started",
    "features_scored",
    "backup_published",
    "predictions_sealed",
    "outcome_access_started",
    "completed",
)


class Journal:
    def __init__(self, transport, binding, plan, commit):
        self.transport, self.binding = transport, dict(binding)
        self.plan, self.commit = plan, commit

    def read(self, expected_tip=None):
        refs = self.transport.list()
        if len(refs) > 128:
            raise Denied("Oversized journal")
        events, index, writer, continued = [], 0, None, False
        for number, ref in enumerate(refs):
            if ref != self.transport.prefix + f"{number:06d}":
                raise Denied("Journal gap or unexpected ref")
            e = self.transport.read(ref)
            if (
                not isinstance(e, dict)
                or set(e)
                != {"binding", "sequence", "previous_sha256", "stage", "instance", "evidence"}
                or e["binding"] != self.binding
                or type(e["sequence"]) is not int
                or e["sequence"] != number
                or e["previous_sha256"] != (digest(events[-1]) if events else None)
            ):
                raise Denied("Changed journal identity/hash chain")
            import re

            if not isinstance(e["instance"], str) or not re.fullmatch(
                r"[A-Za-z0-9_.-]{1,128}", e["instance"]
            ):
                raise Denied("Invalid journal worker")
            if e["stage"] == "continuation_approved":
                if index != 4 or continued or e["instance"] == writer:
                    raise Denied("Continuation outside exact publication pause")
                if set(e["evidence"]) != {"approval", "preflight", "pause"}:
                    raise Denied("Missing continuation evidence")
                v = e["evidence"]
                if (
                    v["pause"]["journal_tip"] != digest(events)
                    or v["pause"]["previous_instance"] != writer
                    or v["pause"]["receipt"] is None
                    or digest(v["pause"]["receipt"]) != self.binding["receipt_sha256"]
                ):
                    raise Denied("Continuation journal/receipt binding changed")
                publication = events[-1]["evidence"]
                if publication != {
                    "checkpoint_sha256": digest(v["pause"]["manifest"]),
                    "transfer_sha256": digest(v["pause"]["transfer"]),
                    "private_commit": v["pause"]["private_commit"],
                }:
                    raise Denied("Continuation checkpoint differs from published journal")
                continuation(
                    v["approval"],
                    self.plan,
                    self.commit,
                    v["pause"],
                    e["instance"],
                    v["preflight"],
                    historical=True,
                )
                continued = True
            else:
                if index >= len(STAGES) or e["stage"] != STAGES[index]:
                    raise Denied("Out-of-order journal stage; no replay")
                if writer is not None and e["instance"] != writer:
                    raise Denied("Unapproved journal worker")
                if index >= 4 and not continued:
                    raise Denied("New signed continuation required before sealing/outcomes")
                required = EVIDENCE.get(
                    e["stage"], {"checkpoint_sha256", "transfer_sha256", "private_commit"}
                )
                if set(e["evidence"]) != required:
                    raise Denied("Missing journal evidence")
                for k, value in e["evidence"].items():
                    if k == "private_commit":
                        if not re.fullmatch(r"[0-9a-f]{40}", value):
                            raise Denied("Invalid private commit")
                    else:
                        sha(value)
                if index == 0 and e["evidence"]["receipt_sha256"] != self.binding["receipt_sha256"]:
                    raise Denied("Changed receipt evidence")
                if index in {3, 4, 5}:
                    previous = next(
                        x["evidence"]["checkpoint_sha256"]
                        for x in reversed(events)
                        if "checkpoint_sha256" in x["evidence"]
                    )
                    if previous != e["evidence"]["checkpoint_sha256"]:
                        raise Denied("Changed prediction seal")
                index += 1
            writer = e["instance"]
            events.append(e)
        if expected_tip is not None and digest(events) != expected_tip:
            raise Denied("Journal advanced, truncated or changed")
        return events

    def append(self, stage, evidence, instance, expected_tip):
        events = self.read(expected_tip)
        e = {
            "binding": self.binding,
            "sequence": len(events),
            "previous_sha256": digest(events[-1]) if events else None,
            "stage": stage,
            "instance": instance,
            "evidence": evidence,
        }
        transport = self.transport

        class View:
            prefix = transport.prefix

            def list(self):
                return [self.prefix + f"{i:06d}" for i in range(len(events) + 1)]

            def read(self, ref):
                return [*events, e][int(ref.rsplit("/", 1)[1])]

        Journal(View(), self.binding, self.plan, self.commit).read()
        ref = transport.prefix + f"{len(events):06d}"
        try:
            transport.create(ref, e)
            if transport.read(ref) != e:
                raise AmbiguousWrite("Journal readback differs; read-only reconciliation required")
        except OSError as exc:
            raise AmbiguousWrite("Unknown journal write; no retry") from exc
        return digest([*events, e])
