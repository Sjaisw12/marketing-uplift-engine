"""Create-only Git receipt protocol. Real GitHub writes are deliberately disabled."""

import re

from .protocol import Denied, canonical, cohort_ref, digest, strict_json


class AmbiguousWrite(Denied):
    pass


class GitHubTransport:
    """Create-only Git command adapter, inert unless a command runner is explicitly supplied.

    No live CLI or production runner is shipped. Tests inject a fake command runner.
    Future approved integration must test these commands against GitHub protections.
    The default cannot read or write a remote; it cannot authorize Stage B.
    """

    def __init__(self, reviewed_commit, runner=None, namespace="stage-b-receipts"):
        if not re.fullmatch(r"[0-9a-f]{40}", reviewed_commit):
            raise Denied("Expected reviewed Git commit")
        self.commit = reviewed_commit
        self.runner = runner
        cohort_ref("1" * 64, "2" * 64, namespace)
        self.namespace = namespace
        self.remote = "https://github.com/Sjaisw12/marketing-uplift-engine.git"

    def command(self, args, data=None):
        if self.runner is None:
            raise Denied("Live GitHub transport disabled; separate write-test approval required")
        # argv only, no shell, inherited proxy/TLS trust, no tokens in command arguments.
        return self.runner(["git", *args], data)

    def check_ref(self, ref):
        if not re.fullmatch(
            rf"refs/tags/{re.escape(self.namespace)}/[0-9a-f]{{64}}/[0-9a-f]{{64}}", ref
        ):
            raise Denied("Non-cohort receipt ref")
        if self.namespace != "stage-b-receipts" and ref != cohort_ref(
            "1" * 64, "2" * 64, self.namespace
        ):
            raise Denied("Synthetic transport requires exact fake cohort")

    def read(self, ref):
        self.check_ref(ref)
        response = self.command(["ls-remote", "--refs", self.remote, ref])
        if not response.strip():
            return None
        fields = response.strip().split()
        if len(fields) != 2 or fields[1] != ref or not re.fullmatch(r"[0-9a-f]{40}", fields[0]):
            raise Denied("Ambiguous remote ref")
        oid = fields[0]
        self.command(["fetch", "--no-tags", self.remote, ref])
        raw = self.command(["cat-file", "tag", oid])
        headers, separator, body = raw.partition("\n\n")
        if not separator or not headers.startswith(f"object {self.commit}\ntype commit\n"):
            raise Denied("Receipt tag targets wrong execution code")
        payload = strict_json(body)
        if cohort_ref(payload["dataset_sha256"], payload["holdout_sha256"], self.namespace) != ref:
            raise Denied("Receipt tag cohort mismatch")
        return payload

    def create(self, ref, payload):
        self.check_ref(ref)
        if cohort_ref(payload["dataset_sha256"], payload["holdout_sha256"], self.namespace) != ref:
            raise Denied("Receipt payload cohort mismatch")
        tag = ref.removeprefix("refs/tags/")
        body = (
            (
                f"object {self.commit}\ntype commit\ntag {tag}\n"
                "tagger Stage B receipt <receipt@invalid> 0 +0000\n\n"
            ).encode()
            + canonical(payload)
            + b"\n"
        )
        oid = self.command(["mktag"], body).strip()
        if not re.fullmatch(r"[0-9a-f]{40}", oid):
            raise Denied("Invalid receipt object identity")
        # Empty lease value requires the remote ref to be ABSENT, even under races.
        self.command(
            ["push", "--porcelain", f"--force-with-lease={ref}:", self.remote, f"{oid}:{ref}"]
        )


def receipt_for(authorization, authorization_sha256):
    return {
        "schema": 1,
        "authorization_sha256": authorization_sha256,
        **{
            k: authorization[k]
            for k in (
                "execution_lock_sha256",
                "model_manifest_sha256",
                "dataset_sha256",
                "holdout_sha256",
                "parameters_sha256",
                "owner",
                "execution_id",
            )
        },
    }


class ReceiptStore:
    """Transport.create must atomically reject existing refs, never update them.

    A receipt is non-secret canonical metadata in an annotated tag targeting the
    reviewed code commit. Production adapter remains blocked pending live approval.
    """

    def __init__(self, transport):
        self.transport = transport

    def ref(self, receipt):
        return cohort_ref(
            receipt["dataset_sha256"],
            receipt["holdout_sha256"],
            getattr(self.transport, "namespace", "stage-b-receipts"),
        )

    def claim(self, receipt):
        ref = self.ref(receipt)
        try:
            if self.transport.read(ref) is not None:
                raise Denied("Existing cohort claim; no duplicate or changed-owner execution")
            # Success is authoritative only after readback. A timeout remains ambiguous,
            # even if a remote write happened: explicit reviewed recovery is required.
            self.transport.create(ref, receipt)
            if self.transport.read(ref) != receipt:
                raise Denied("Receipt readback mismatch")
        except (OSError, TimeoutError) as exc:
            raise AmbiguousWrite(
                "Unknown receipt state; stop, never retry as new execution"
            ) from exc
        return digest(receipt)

    def verify(self, receipt):
        try:
            actual = self.transport.read(self.ref(receipt))
        except OSError as exc:
            raise Denied("Cannot verify durable receipt") from exc
        if actual != receipt:
            raise Denied("Receipt missing, tampered, or owned by another execution")
        return digest(receipt)
