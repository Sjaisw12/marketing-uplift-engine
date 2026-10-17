"""Private byte manifests and independent-backup verification; no data interpretation."""

from pathlib import Path, PurePosixPath

from .protocol import BACKUP_DOMAIN, Denied, digest, file_hash, verify_signed_payload


def checked_path(root, relative):
    part = PurePosixPath(relative)
    if part.is_absolute() or not part.parts or ".." in part.parts or str(part) != relative:
        raise Denied("Unsafe checkpoint path")
    root = Path(root).resolve()
    path = root.joinpath(*part.parts)
    if path.is_symlink() or not path.resolve().is_relative_to(root) or not path.is_file():
        raise Denied("Checkpoint absent or outside private root")
    return path


def snapshot(root, names, binding):
    if not names or len(set(names)) != len(names):
        raise Denied("Missing or duplicate checkpoint files")
    return {
        "schema": 1,
        "binding": binding,
        "files": {
            name: {"bytes": (p := checked_path(root, name)).stat().st_size, "sha256": file_hash(p)}
            for name in sorted(names)
        },
    }


def verify_files(root, manifest):
    actual = snapshot(root, list(manifest["files"]), manifest["binding"])
    if actual != manifest:
        raise Denied("Checkpoint hash/size mismatch")
    return digest(manifest)


def verify_backup(local_root, backup_root, manifest, attestation, trusted_public_key):
    """Copy hashes alone cannot prove off-cloud durability: require owner-signed attestation.

    The reviewed owner key validates the attestation against this EXACT payload.
    Real execution never calls this preparation-only primitive on holdout files.
    """
    if Path(local_root).resolve() == Path(backup_root).resolve():
        raise Denied("Backup is not a separate location")
    verify_files(local_root, manifest)
    verify_files(backup_root, manifest)
    expected = {
        "schema": 1,
        "purpose": "independent-private-backup",
        "manifest_sha256": digest(manifest),
        "binding": manifest["binding"],
    }
    verify_signed_payload(attestation, expected, trusted_public_key, BACKUP_DOMAIN)
    return digest(expected)
