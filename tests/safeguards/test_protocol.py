"""Synthetic signing keys only. No production key or real holdout access."""

import base64
import copy
import hashlib
from datetime import UTC, datetime

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from execution_safeguards.protocol import (
    DOMAIN,
    Denied,
    canonical,
    cohort_ref,
    strict_json,
    verify_authorization,
    verify_signed_payload,
)


@pytest.fixture
def signing():
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes_raw()
    expected = {
        "schema": 1,
        "purpose": "one-final-holdout-evaluation",
        "execution_lock_sha256": "a" * 64,
        "model_manifest_sha256": "b" * 64,
        "dataset_sha256": "c" * 64,
        "holdout_sha256": "d" * 64,
        "parameters_sha256": "e" * 64,
        "owner": "synthetic-owner",
        "execution_id": "fixture-1",
        "public_key_sha256": hashlib.sha256(public).hexdigest(),
        "not_before": "2026-01-01T00:00:00+00:00",
        "expires_at": "2027-01-01T00:00:00+00:00",
    }

    def sign(payload, domain=DOMAIN):
        return {
            "payload": payload,
            "signature": base64.b64encode(key.sign(domain + canonical(payload))).decode(),
        }

    return expected, base64.b64encode(public).decode(), sign


def verify(envelope, expected, public):
    return verify_authorization(envelope, expected, public, datetime(2026, 10, 17, tzinfo=UTC))


def test_valid_signature_and_stable_canonicalization(signing):
    expected, public, sign = signing
    assert verify(sign(expected), expected, public)
    assert canonical({"b": 2, "a": 1}) == b'{"a":1,"b":2}'


@pytest.mark.parametrize(
    "field",
    [
        "execution_lock_sha256",
        "model_manifest_sha256",
        "dataset_sha256",
        "holdout_sha256",
        "parameters_sha256",
        "owner",
        "execution_id",
    ],
)
def test_every_authorization_binding_is_signed(signing, field):
    expected, public, sign = signing
    forged = copy.deepcopy(sign(expected))
    forged["payload"] = dict(expected, **{field: "f" * 64})
    with pytest.raises(Denied):
        verify(forged, forged["payload"], public)
    with pytest.raises(Denied):
        verify(forged, expected, public)


def test_forgery_wrong_key_and_domain(signing):
    expected, public, sign = signing
    with pytest.raises(Denied):
        verify(sign(expected, b"wrong-domain"), expected, public)
    fake_public = base64.b64encode(Ed25519PrivateKey.generate().public_key().public_bytes_raw())
    with pytest.raises(Denied):
        verify(sign(expected), expected, fake_public)
    envelope = sign(expected)
    envelope["signature"] = base64.b64encode(b"\0" * 64).decode()
    with pytest.raises(Denied):
        verify(envelope, expected, public)


@pytest.mark.parametrize(
    "change",
    [
        {"expires_at": "2025-01-01T00:00:00+00:00"},
        {"not_before": "2028-01-01T00:00:00+00:00"},
        {"not_before": "2026-01-01T00:00:00"},
        {"extra": True},
        {"purpose": "recovery"},
    ],
)
def test_invalid_or_expired_authorization(signing, change):
    expected, public, sign = signing
    changed = dict(expected, **change)
    with pytest.raises(Denied):
        verify(sign(changed), changed, public)


@pytest.mark.parametrize("raw", ['{"a":1,"a":2}', '{"a":NaN}', "not json"])
def test_strict_json(raw):
    with pytest.raises(Denied):
        strict_json(raw)


def test_standard_rfc8032_ed25519_reference():
    # RFC8032 section7.1 test1: empty message, fixed public key and signature.
    # This verifies the primitive independently of our generated-key round trips.
    public = bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
    signature = bytes.fromhex(
        "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555f"
        "b8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"
    )
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    Ed25519PublicKey.from_public_bytes(public).verify(signature, b"")


def test_ref_has_no_run_owner_or_lock(signing):
    p, _, _ = signing
    ref = cohort_ref(p["dataset_sha256"], p["holdout_sha256"])
    assert ref == cohort_ref(p["dataset_sha256"], p["holdout_sha256"])
    assert p["owner"] not in ref and p["execution_id"] not in ref
    with pytest.raises(Denied):
        cohort_ref("../bad", p["holdout_sha256"])


def test_generic_payload_requires_exact_fields(signing):
    expected, public, sign = signing
    with pytest.raises(Denied):
        verify_signed_payload(sign(expected), {"changed": True}, public, DOMAIN)


def test_signed_authorization_receipt_and_stage_binding(signing):
    from execution_safeguards.protocol import digest
    from execution_safeguards.receipt import ReceiptStore, receipt_for
    from execution_safeguards.state import append_event, verify_journal

    from .test_receipt import MemoryTransport

    expected, public, sign = signing
    auth_sha = verify(sign(expected), expected, public)
    receipt = receipt_for(expected, auth_sha)
    store = ReceiptStore(MemoryTransport())
    receipt_sha = store.claim(receipt)
    events = append_event(
        [], receipt_sha, "authorization_verified", {"authorization_sha256": auth_sha}
    )
    events = append_event(events, receipt_sha, "receipt_created", {"receipt_sha256": receipt_sha})
    assert verify_journal(events, receipt_sha) == digest(events)
    with pytest.raises(Denied):
        append_event(events[:1], receipt_sha, "receipt_created", {"receipt_sha256": "0" * 64})
