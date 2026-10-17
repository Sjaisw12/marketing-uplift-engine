"""Owner-only activation permission; null draft fields are deliberately non-signable."""

import re
from datetime import UTC, datetime

from execution_safeguards.protocol import Denied, digest, verify_signed_payload

from .preflight import validate, window

DOMAIN = b"marketing-uplift/stage-b-activation-integration/v1\x00"
BACKUP_DOMAIN = b"marketing-uplift/encrypted-mac-backup/v1\x00"


def draft(plan):
    p, c = plan["parent"], plan["parent"]["config"]
    return {
        "schema": 1,
        "purpose": "one-final-holdout-evaluation",
        "execution_lock_sha256": plan["lock_sha"],
        "model_manifest_sha256": p["model_manifest_sha256"],
        "dataset_sha256": p["dataset_sha256"],
        "holdout_sha256": p["holdout"]["sha256"],
        "parameters_sha256": digest(
            {"settings": p["settings"], "policies": p["policies"], "integration": plan["config"]}
        ),
        "owner": c["owner"],
        "execution_id": c["execution_id"],
        "public_key_sha256": c["public_key_sha256"],
        "reviewed_commit": None,
        "preflight_sha256": None,
        "not_before": None,
        "expires_at": None,
    }


def authorize(envelope, plan, commit, report, now=None, historical=False):
    if not isinstance(envelope, dict) or not isinstance(envelope.get("payload"), dict):
        raise Denied("Separate signed owner execution approval missing")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise Denied("Exact reviewed Git commit required")
    p = envelope["payload"]
    clock = now or datetime.now(UTC)
    # Recovery verifies the ORIGINAL grant at its original start time, then separately
    # requires a fresh recovery signature. It never changes the consumed receipt.
    if historical:
        try:
            clock = datetime.fromisoformat(p["not_before"])
        except (ValueError, TypeError, KeyError) as exc:
            raise Denied("Original grant validity missing") from exc
    report_sha = validate(report, plan, commit, clock)
    expected = {
        **draft(plan),
        "reviewed_commit": commit,
        "preflight_sha256": report_sha,
        "not_before": p.get("not_before"),
        "expires_at": p.get("expires_at"),
    }
    signature_sha = verify_signed_payload(
        envelope, expected, plan["parent"]["config"]["public_key_base64"], DOMAIN
    )
    window(
        expected["not_before"],
        expected["expires_at"],
        clock,
        plan["config"]["maximum_authorization_seconds"],
    )
    return signature_sha
