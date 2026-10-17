"""Hash-chained synthetic state machine; no real feature/outcome reader or activation path."""

from .protocol import Denied, digest, sha

STAGES = (
    "authorization_verified",
    "receipt_created",
    "features_scored",
    "predictions_sealed",
    "outcome_access_started",
    "completed",
)
EVIDENCE = {
    "authorization_verified": {"authorization_sha256"},
    "receipt_created": {"receipt_sha256"},
    "features_scored": {"alignment_sha256"},
    "predictions_sealed": {"prediction_manifest_sha256", "backup_verification_sha256"},
    "outcome_access_started": {"prediction_manifest_sha256"},
    "completed": {"result_manifest_sha256"},
}


def append_event(events, receipt_sha256, stage, evidence):
    sha(receipt_sha256)
    if len(events) >= len(STAGES) or stage != STAGES[len(events)]:
        raise Denied("Illegal stage order or duplicate transition")
    if set(evidence) != EVIDENCE[stage]:
        raise Denied("Missing stage evidence")
    for value in evidence.values():
        sha(value)
    if stage == "receipt_created" and evidence["receipt_sha256"] != receipt_sha256:
        raise Denied("Stage evidence refers to a different receipt")
    if stage == "outcome_access_started":
        if (
            evidence["prediction_manifest_sha256"]
            != events[-1]["evidence"]["prediction_manifest_sha256"]
        ):
            raise Denied("Predictions changed after sealing")
    event = {
        "sequence": len(events),
        "receipt_sha256": receipt_sha256,
        "stage": stage,
        "previous_sha256": digest(events[-1]) if events else None,
        "evidence": evidence,
    }
    return [*events, event]


def verify_journal(events, receipt_sha256):
    verified = []
    for event in events:
        expected = append_event(verified, receipt_sha256, event["stage"], event["evidence"])
        if expected[-1] != event:
            raise Denied("Journal chain or receipt mismatch")
        verified = expected
    return digest(verified)


def recovery_check(store, receipt, events, expected_journal_sha256, saved_lock_sha256):
    """Integrity check only; never grants takeover or authorizes an automatic resume."""
    receipt_sha256 = store.verify(receipt)
    if receipt["execution_lock_sha256"] != saved_lock_sha256:
        raise Denied("Recovery changed the execution lock")
    if verify_journal(events, receipt_sha256) != expected_journal_sha256:
        raise Denied("Journal truncated or changed")
    return {
        "integrity_verified": True,
        "resume_authorized": False,
        "reason": "Separate owner recovery approval and terminated-worker proof required",
    }


def score_real_holdout(*args, **kwargs):
    raise Denied("Stage B disabled: no approved live receipt backend or production signer")


def evaluate_real_holdout(*args, **kwargs):
    raise Denied("Stage B disabled: no verified independent backup or execution authorization")
