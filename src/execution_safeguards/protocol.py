"""Strict canonical authorization with Ed25519; verification only, never key generation."""

import base64
import hashlib
import json
import re
from datetime import UTC, datetime

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

DOMAIN = b"marketing-uplift/stage-b-authorization/v1\x00"
BACKUP_DOMAIN = b"marketing-uplift/private-backup/v1\x00"


class Denied(RuntimeError):
    """Fail closed: no side effects or access may follow this error."""


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise Denied("Duplicate JSON key")
            result[key] = value
        return result

    def nonfinite(_):
        raise Denied("Nonfinite JSON")

    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)
    except (ValueError, TypeError) as exc:
        raise Denied("Invalid JSON") from exc


def sha(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise Denied("Expected SHA-256")
    return value


def cohort_ref(dataset_sha256, holdout_sha256, namespace="stage-b-receipts"):
    # Fixed across runs, owners, locks and recovery; never derive a new claim from a run ID.
    if namespace not in {"stage-b-receipts", "stage-b-synthetic/receipt-integration-v1"}:
        raise Denied("Unreviewed receipt namespace")
    return f"refs/tags/{namespace}/{sha(dataset_sha256)}/{sha(holdout_sha256)}"


def verify_signed_payload(envelope, expected, trusted_public_key, domain):
    if set(envelope) != {"payload", "signature"} or envelope["payload"] != expected:
        raise Denied("Signed payload binding mismatch")
    try:
        public = base64.b64decode(trusted_public_key, validate=True)
        signature = base64.b64decode(envelope["signature"], validate=True)
        if len(public) != 32 or len(signature) != 64:
            raise Denied("Invalid Ed25519 length")
        Ed25519PublicKey.from_public_bytes(public).verify(signature, domain + canonical(expected))
    except (ValueError, TypeError, InvalidSignature) as exc:
        raise Denied("Invalid Ed25519 signature") from exc
    return digest(envelope)


def verify_authorization(envelope, expected, trusted_public_key, now=None):
    """Verify exact predeclared payload; trust key must come from reviewed config, not envelope."""
    if set(envelope) != {"payload", "signature"}:
        raise Denied("Authorization envelope fields")
    if envelope["payload"] != expected:
        raise Denied("Authorization binding mismatch")
    required = {
        "schema",
        "purpose",
        "execution_lock_sha256",
        "model_manifest_sha256",
        "dataset_sha256",
        "holdout_sha256",
        "parameters_sha256",
        "owner",
        "execution_id",
        "public_key_sha256",
        "not_before",
        "expires_at",
    }
    if set(expected) != required or expected["schema"] != 1:
        raise Denied("Authorization schema")
    if expected["purpose"] != "one-final-holdout-evaluation":
        raise Denied("Authorization purpose")
    for key in required:
        if key.endswith("sha256"):
            sha(expected[key])
    for key in ("owner", "execution_id"):
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", expected[key]):
            raise Denied("Invalid execution identity")
    try:
        public = base64.b64decode(trusted_public_key, validate=True)
        signature = base64.b64decode(envelope["signature"], validate=True)
        if len(public) != 32 or len(signature) != 64:
            raise Denied("Invalid Ed25519 length")
        if hashlib.sha256(public).hexdigest() != expected["public_key_sha256"]:
            raise Denied("Wrong trusted signer")
        Ed25519PublicKey.from_public_bytes(public).verify(signature, DOMAIN + canonical(expected))
        start = datetime.fromisoformat(expected["not_before"])
        end = datetime.fromisoformat(expected["expires_at"])
        clock = now or datetime.now(UTC)
        if start.utcoffset() is None or end.utcoffset() is None or clock.utcoffset() is None:
            raise Denied("Timezone required")
        if not start <= clock < end:
            raise Denied("Authorization outside validity window")
    except (ValueError, TypeError, InvalidSignature) as exc:
        raise Denied("Invalid authorization signature or validity") from exc
    return digest(envelope)
