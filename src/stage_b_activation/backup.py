"""Encrypted export and exact owner-signed Mac-restore proof; no private key handling."""

import hashlib
import os
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from execution_safeguards.bundle import atomic_json
from execution_safeguards.checkpoints import verify_files
from execution_safeguards.protocol import (
    Denied,
    digest,
    file_hash,
    strict_json,
    verify_signed_payload,
)
from production_adapter.export import export_chunks

from .authorization import BACKUP_DOMAIN
from .preflight import validate, window


def encrypt(binary, config, archive, ciphertext):
    binary = Path(binary)
    if file_hash(binary) != config["age_tool"]["binary_sha256"]:
        raise Denied("Unverified official age binary")
    if Path(ciphertext).exists():
        raise Denied("Encryption output already exists; no overwrite or automatic retry")
    try:
        result = subprocess.run(
            [
                str(binary),
                "--encrypt",
                "--recipient",
                config["age_recipient"],
                "--output",
                str(ciphertext),
                str(archive),
            ],
            capture_output=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Denied("Encryption interrupted; stop without overwrite") from exc
    if result.returncode:
        raise Denied("age encryption failed; no publication")
    prefix = b"age-encryption.org/v1\n-> X25519 "
    with Path(ciphertext).open("rb") as stream:
        if stream.read(len(prefix)) != prefix:
            raise Denied("Unexpected age native X25519 output")


def export_checkpoint(root, manifest, destination, config, binary, encryptor=encrypt):
    """Caller must hold authorization and own features_scored; never called in preparation."""
    root, destination = Path(root), Path(destination)
    verify_files(root, manifest)
    nbytes = sum(f["bytes"] for f in manifest["files"].values())
    ancestor = destination.parent
    while not ancestor.exists():
        ancestor = ancestor.parent
    if shutil.disk_usage(ancestor).free < config.get("disk_reserve_bytes", 8589934592) + 8 * nbytes:
        raise Denied("Insufficient encrypted export/clone/restore staging disk")
    destination.mkdir(exist_ok=False, parents=True)
    catalog = export_chunks(
        root,
        manifest,
        destination / "plaintext-parts",
        chunk_bytes=config["ciphertext_chunk_bytes"],
        reserve_bytes=config.get("disk_reserve_bytes", 8589934592),
    )
    archive = destination / "checkpoint.tar"
    h = hashlib.sha256()
    with archive.open("xb") as out:
        for part in catalog["parts"]:
            path = destination / "plaintext-parts" / part["name"]
            if path.stat().st_size != part["bytes"] or file_hash(path) != part["sha256"]:
                raise Denied("Plain export part integrity failed")
            with path.open("rb") as inp:
                for block in iter(lambda: inp.read(1048576), b""):
                    out.write(block)
                    h.update(block)
        out.flush()
        os.fsync(out.fileno())
    if (
        h.hexdigest() != catalog["archive_sha256"]
        or archive.stat().st_size != catalog["archive_bytes"]
    ):
        raise Denied("Archive integrity failed before encryption")
    cipher = destination / "checkpoint.tar.age"
    encryptor(binary, config, archive, cipher)
    public = destination / "publish"
    (public / "encrypted").mkdir(parents=True)
    parts, reconstructed = [], hashlib.sha256()
    with cipher.open("rb") as inp:
        while block := inp.read(config["ciphertext_chunk_bytes"]):
            name = f"encrypted/part-{len(parts):06d}.bin"
            with (public / name).open("xb") as out:
                out.write(block)
                out.flush()
                os.fsync(out.fileno())
            parts.append(
                {"path": name, "bytes": len(block), "sha256": hashlib.sha256(block).hexdigest()}
            )
    # Compare the actual persisted bytes, not the just-written input buffers.
    with cipher.open("rb") as original:
        for part in parts:
            with (public / part["path"]).open("rb") as inp:
                while block := inp.read(1048576):
                    if block != original.read(len(block)):
                        raise Denied("Encrypted reconstruction byte mismatch")
                    reconstructed.update(block)
        if original.read(1):
            raise Denied("Truncated ciphertext parts")
    if not parts or reconstructed.hexdigest() != file_hash(cipher):
        raise Denied("Ciphertext reconstruction hash mismatch")
    transfer = {
        "schema": 1,
        "binding": manifest["binding"],
        "checkpoint_sha256": digest(manifest),
        "catalog_sha256": digest(catalog),
        "archive_sha256": catalog["archive_sha256"],
        "archive_bytes": catalog["archive_bytes"],
        "ciphertext_sha256": file_hash(cipher),
        "ciphertext_bytes": cipher.stat().st_size,
        "recipient_sha256": config["age_recipient_sha256"],
        "age_binary_sha256": config["age_tool"]["binary_sha256"],
        "encryption": "age-native-X25519",
        "repository": config["backup_repository"],
        "branch": config["backup_branch"],
        "parts": parts,
    }
    atomic_json(public / "catalog.json", catalog)
    atomic_json(public / "transfer.json", transfer)
    return transfer


def verify_transfer(directory, manifest, transfer, config):
    directory = Path(directory)
    if strict_json((directory / "transfer.json").read_bytes()) != transfer:
        raise Denied("Transfer metadata changed")
    catalog = strict_json((directory / "catalog.json").read_bytes())
    if (
        transfer["binding"] != manifest["binding"]
        or transfer["checkpoint_sha256"] != digest(manifest)
        or catalog["manifest"] != manifest
        or catalog["manifest_sha256"] != digest(manifest)
        or digest(catalog) != transfer["catalog_sha256"]
        or catalog["archive_sha256"] != transfer["archive_sha256"]
        or catalog["archive_bytes"] != transfer["archive_bytes"]
        or transfer["recipient_sha256"] != config["age_recipient_sha256"]
        or transfer["age_binary_sha256"] != config["age_tool"]["binary_sha256"]
        or transfer["encryption"] != "age-native-X25519"
        or transfer["repository"] != config["backup_repository"]
        or transfer["branch"] != config["backup_branch"]
    ):
        raise Denied("Backup does not bind exact prediction seal/encryption/destination")
    h, total = hashlib.sha256(), 0
    for number, part in enumerate(transfer["parts"]):
        if part["path"] != f"encrypted/part-{number:06d}.bin":
            raise Denied("Transfer parts reordered/missing/duplicated")
        path = directory / part["path"]
        if (
            path.is_symlink()
            or path.stat().st_size != part["bytes"]
            or file_hash(path) != part["sha256"]
        ):
            raise Denied("Transfer part tampered")
        if not 0 < part["bytes"] <= config["ciphertext_chunk_bytes"]:
            raise Denied("Invalid encrypted part size")
        with path.open("rb") as inp:
            for block in iter(lambda: inp.read(1048576), b""):
                h.update(block)
                total += len(block)
    if (
        not total
        or h.hexdigest() != transfer["ciphertext_sha256"]
        or total != transfer["ciphertext_bytes"]
    ):
        raise Denied("Combined encrypted checkpoint integrity mismatch")


def backup_payload(manifest, transfer, commit, preflight_sha, not_before, expires_at):
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise Denied("Exact private checkpoint commit required")
    return {
        "schema": 1,
        "purpose": "independent-encrypted-off-workspace-restore",
        "binding": manifest["binding"],
        "checkpoint_sha256": digest(manifest),
        "transfer_sha256": digest(transfer),
        "catalog_sha256": transfer["catalog_sha256"],
        "archive_sha256": transfer["archive_sha256"],
        "archive_bytes": transfer["archive_bytes"],
        "ciphertext_sha256": transfer["ciphertext_sha256"],
        "ciphertext_bytes": transfer["ciphertext_bytes"],
        "recipient_sha256": transfer["recipient_sha256"],
        "repository": transfer["repository"],
        "branch": transfer["branch"],
        "commit": commit,
        "owner_confirms_mac_decryption_and_restore": True,
        "restored_checkpoint_sha256": digest(manifest),
        "preflight_sha256": preflight_sha,
        "not_before": not_before,
        "expires_at": expires_at,
    }


def verify_backup(
    root, manifest, directory, transfer, envelope, remote, plan, commit, report, now=None
):
    verify_files(root, manifest)
    verify_transfer(directory, manifest, transfer, plan["config"])
    clock = now or datetime.now(UTC)
    report_sha = validate(report, plan, commit, clock)
    # Git access is checked now; privacy is attested in the signed API report.
    remote.access()
    private_commit = remote.commit()
    p = envelope.get("payload", {})
    expected = backup_payload(
        manifest, transfer, private_commit, report_sha, p.get("not_before"), p.get("expires_at")
    )
    proof = verify_signed_payload(
        envelope, expected, plan["parent"]["config"]["public_key_base64"], BACKUP_DOMAIN
    )
    window(
        expected["not_before"],
        expected["expires_at"],
        clock,
        plan["config"]["maximum_authorization_seconds"],
    )
    return proof
