"""Separate start and continuation domains; old production signatures cannot activate this code."""

from datetime import UTC, datetime

from execution_safeguards.protocol import digest, verify_signed_payload
from stage_b_activation.authorization import draft
from stage_b_activation.preflight import validate, window

START_DOMAIN = b"marketing-uplift/resumable-stage-b-start/v1\x00"
CONTINUE_DOMAIN = b"marketing-uplift/resumable-stage-b-continue/v1\x00"


def start(envelope, plan, commit, report, now, historical=False):
    p = envelope.get("payload", {})
    if historical:
        now = datetime.fromisoformat(p["not_before"])
    report_sha = validate(report, plan, commit, now)
    # Admit only grants that can also be verified historically after a process restart.
    validate(report, plan, commit, datetime.fromisoformat(p["not_before"]))
    expected = {
        **draft(plan),
        "reviewed_commit": commit,
        "preflight_sha256": report_sha,
        "not_before": p.get("not_before"),
        "expires_at": p.get("expires_at"),
    }
    sha = verify_signed_payload(
        envelope, expected, plan["parent"]["config"]["public_key_base64"], START_DOMAIN
    )
    window(expected["not_before"], expected["expires_at"], now, 86400)
    return sha


def continuation_payload(plan, commit, pause, instance, report, not_before, expires_at):
    return {
        "schema": 1,
        "purpose": "resume-exact-published-checkpoint",
        "execution_lock_sha256": plan["lock_sha"],
        "reviewed_commit": commit,
        "model_manifest_sha256": plan["parent"]["model_manifest_sha256"],
        "dataset_sha256": plan["parent"]["dataset_sha256"],
        "holdout_sha256": plan["parent"]["holdout"]["sha256"],
        "owner": plan["parent"]["config"]["owner"],
        "execution_id": plan["parent"]["config"]["execution_id"],
        "pause_sha256": digest(pause),
        "original_authorization_sha256": digest(pause["authorization"]),
        "journal_sha256": pause["journal_tip"],
        "new_instance": instance,
        "previous_worker_terminated": True,
        "preflight_sha256": digest(report),
        "allowed_actions": ["seal", "evaluate"],
        "not_before": not_before,
        "expires_at": expires_at,
    }


def continuation(envelope, plan, commit, pause, instance, report, now=None, historical=False):
    p = envelope.get("payload", {})
    clock = now or datetime.now(UTC)
    if historical:
        clock = datetime.fromisoformat(p["not_before"])
    validate(report, plan, commit, clock)
    validate(report, plan, commit, datetime.fromisoformat(p["not_before"]))
    expected = continuation_payload(
        plan, commit, pause, instance, report, p.get("not_before"), p.get("expires_at")
    )
    sha = verify_signed_payload(
        envelope, expected, plan["parent"]["config"]["public_key_base64"], CONTINUE_DOMAIN
    )
    window(expected["not_before"], expected["expires_at"], clock, 86400)
    return sha
