"""Opaque synthetic checkpoint bytes and simulated state transitions only."""

import base64
import shutil

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from execution_safeguards.checkpoints import snapshot, verify_backup, verify_files
from execution_safeguards.protocol import BACKUP_DOMAIN, Denied, canonical, digest
from execution_safeguards.receipt import ReceiptStore
from execution_safeguards.state import (
    EVIDENCE,
    STAGES,
    append_event,
    evaluate_real_holdout,
    recovery_check,
    score_real_holdout,
    verify_journal,
)

from .test_receipt import MemoryTransport, sample


def backup_fixture(tmp_path):
    local, backup = tmp_path / "local", tmp_path / "backup"
    local.mkdir()
    (local / "predictions.bin").write_bytes(b"synthetic predictions only")
    (local / "membership.bin").write_bytes(b"synthetic policy membership only")
    shutil.copytree(local, backup)
    manifest = snapshot(
        local,
        ["predictions.bin", "membership.bin"],
        {"receipt_sha256": "a" * 64, "execution_lock_sha256": "b" * 64},
    )
    key = Ed25519PrivateKey.generate()
    public = base64.b64encode(key.public_key().public_bytes_raw()).decode()
    payload = {
        "schema": 1,
        "purpose": "independent-private-backup",
        "manifest_sha256": digest(manifest),
        "binding": manifest["binding"],
    }
    attestation = {
        "payload": payload,
        "signature": base64.b64encode(key.sign(BACKUP_DOMAIN + canonical(payload))).decode(),
    }
    return local, backup, manifest, attestation, public


def test_private_backup_hashes_attestation_and_tampering(tmp_path):
    local, backup, manifest, attestation, public = backup_fixture(tmp_path)
    assert verify_backup(local, backup, manifest, attestation, public)
    with pytest.raises(Denied):
        verify_backup(local, local, manifest, attestation, public)
    wrong = dict(attestation, signature=base64.b64encode(b"\0" * 64).decode())
    with pytest.raises(Denied):
        verify_backup(local, backup, manifest, wrong, public)
    (backup / "predictions.bin").write_bytes(b"changed")
    with pytest.raises(Denied):
        verify_backup(local, backup, manifest, attestation, public)


@pytest.mark.parametrize("name", ["../escape", "/absolute", "a/../predictions.bin", "missing"])
def test_checkpoint_path_restrictions(tmp_path, name):
    with pytest.raises(Denied):
        snapshot(tmp_path, [name], {})


def test_checkpoint_symlink_and_empty_manifest(tmp_path):
    outside = tmp_path / "outside"
    outside.write_bytes(b"synthetic")
    root = tmp_path / "root"
    root.mkdir()
    (root / "link").symlink_to(outside)
    with pytest.raises(Denied):
        snapshot(root, ["link"], {})
    with pytest.raises(Denied):
        snapshot(root, [], {})


def events_until(count):
    events = []
    for stage in STAGES[:count]:
        evidence = dict.fromkeys(EVIDENCE[stage], "a" * 64)
        if stage == "receipt_created":
            evidence["receipt_sha256"] = "b" * 64
        events = append_event(events, "b" * 64, stage, evidence)
    return events


def test_stage_order_sealing_and_chain():
    with pytest.raises(Denied):
        append_event([], "b" * 64, "outcome_access_started", {})
    events = events_until(4)
    with pytest.raises(Denied):
        append_event(
            events, "b" * 64, "outcome_access_started", {"prediction_manifest_sha256": "c" * 64}
        )
    complete = events_until(6)
    assert verify_journal(complete, "b" * 64)
    with pytest.raises(Denied):
        append_event(complete, "b" * 64, "completed", {"result_manifest_sha256": "a" * 64})
    complete[1]["previous_sha256"] = "0" * 64
    with pytest.raises(Denied):
        verify_journal(complete, "b" * 64)


@pytest.mark.parametrize("count", range(7))
def test_crash_at_each_boundary_preserves_claim_and_denies_automatic_recovery(count):
    store = ReceiptStore(MemoryTransport())
    receipt = sample()
    receipt_sha = store.claim(receipt)
    events = []
    for stage in STAGES[:count]:
        evidence = dict.fromkeys(EVIDENCE[stage], "a" * 64)
        if stage == "receipt_created":
            evidence["receipt_sha256"] = receipt_sha
        events = append_event(events, receipt_sha, stage, evidence)
    check = recovery_check(store, receipt, events, digest(events), receipt["execution_lock_sha256"])
    assert check["integrity_verified"] and not check["resume_authorized"]
    with pytest.raises(Denied):
        store.claim(receipt)
    with pytest.raises(Denied):
        recovery_check(store, receipt, events, "0" * 64, receipt["execution_lock_sha256"])
    with pytest.raises(Denied):
        recovery_check(store, receipt, events, digest(events), "0" * 64)


def test_real_access_always_disabled_before_io(monkeypatch):
    import builtins

    def forbidden(*args, **kwargs):
        pytest.fail("Real access attempted I/O")

    monkeypatch.setattr(builtins, "open", forbidden)
    for function in (score_real_holdout, evaluate_real_holdout):
        with pytest.raises(Denied, match="Stage B disabled"):
            function(approved=True, backup_verified=True, receipt="claimed", path="anything")


def test_synthetic_full_stage_sequence_and_checkpoint_reverification(tmp_path):
    local, backup, manifest, attestation, public = backup_fixture(tmp_path)
    store = ReceiptStore(MemoryTransport())
    receipt_sha = store.claim(sample())
    events = []
    evidence = [
        {"authorization_sha256": "a" * 64},
        {"receipt_sha256": receipt_sha},
        {"alignment_sha256": "c" * 64},
        {
            "prediction_manifest_sha256": digest(manifest),
            "backup_verification_sha256": verify_backup(
                local, backup, manifest, attestation, public
            ),
        },
        {"prediction_manifest_sha256": verify_files(local, manifest)},
        {"result_manifest_sha256": "d" * 64},
    ]
    for stage, item in zip(STAGES, evidence, strict=True):
        events = append_event(events, receipt_sha, stage, item)
    assert verify_journal(events, receipt_sha)
