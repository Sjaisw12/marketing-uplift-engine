"""Pre-outcome proof checks. This verifies private bytes; it never opens outcomes."""

from execution_safeguards.checkpoints import verify_backup
from execution_safeguards.protocol import Denied, digest

from .scoring import read_seal


def verify_boundary(
    root,
    manifest,
    expected_binding,
    expected_ids_sha,
    backup_root,
    attestation,
    public_key,
    receipt_store,
    receipt,
    journal,
    tip,
    instance,
):
    receipt_sha = receipt_store.verify(receipt)
    core = {
        "receipt_sha256": receipt_sha,
        "execution_lock_sha256": receipt["execution_lock_sha256"],
        "owner": receipt["owner"],
        "execution_id": receipt["execution_id"],
    }
    if journal.binding != core or any(expected_binding.get(k) != v for k, v in core.items()):
        raise Denied("Receipt/journal/prediction execution binding mismatch")
    events = journal.read(tip)
    functional = [e for e in events if e["stage"] != "recovery_approved"]
    if (
        not functional
        or functional[-1]["stage"] != "predictions_sealed"
        or events[-1]["instance"] != instance
        or functional[-1]["evidence"]["checkpoint_sha256"] != digest(manifest)
    ):
        raise Denied("No current owned durable prediction seal")
    sealed = read_seal(root, manifest, expected_binding, expected_ids_sha)
    proof = verify_backup(root, backup_root, manifest, attestation, public_key)
    if functional[-1]["evidence"]["backup_sha256"] != proof:
        raise Denied("Backup verification does not match durable journal seal")
    return sealed
