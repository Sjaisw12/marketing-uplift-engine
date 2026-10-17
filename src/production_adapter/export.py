"""Bounded private export chunks and restore; deliberately no network transport."""

import hashlib
import os
import shutil
import tempfile
from pathlib import Path

from execution_safeguards.bundle import atomic_json, export_bundle, restore_bundle
from execution_safeguards.checkpoints import verify_files
from execution_safeguards.protocol import Denied, digest, file_hash, strict_json


def export_chunks(root, manifest, destination, chunk_bytes=67108864, reserve_bytes=8589934592):
    if not 1 <= chunk_bytes <= 67108864:
        raise Denied("Invalid bounded export chunk size")
    verify_files(root, manifest)
    destination = Path(destination)
    ancestor = destination.parent
    while not ancestor.exists():
        ancestor = ancestor.parent
    total = sum(v["bytes"] for v in manifest["files"].values())
    # One tar plus chunks exist temporarily; never allocate a whole bundle in memory.
    if shutil.disk_usage(ancestor).free < reserve_bytes + 2 * total + 1048576:
        raise Denied("Insufficient disk for export staging")
    destination.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(dir=destination) as temp:
        archive = Path(temp) / "private-checkpoint.tar"
        export_bundle(root, manifest, archive)
        parts = []
        whole = hashlib.sha256()
        with archive.open("rb") as stream:
            while block := stream.read(chunk_bytes):
                name = f"part-{len(parts):06d}.bin"
                with (destination / name).open("xb") as out:
                    out.write(block)
                    out.flush()
                    os.fsync(out.fileno())
                whole.update(block)
                parts.append(
                    {"name": name, "bytes": len(block), "sha256": hashlib.sha256(block).hexdigest()}
                )
        catalog = {
            "schema": 1,
            "manifest": manifest,
            "manifest_sha256": digest(manifest),
            "archive_bytes": archive.stat().st_size,
            "archive_sha256": whole.hexdigest(),
            "chunk_bytes": chunk_bytes,
            "parts": parts,
        }
        atomic_json(destination / "catalog.json", catalog)
    return catalog


def restore_chunks(directory, destination, expected_catalog_sha256, max_bytes):
    directory = Path(directory)
    catalog = strict_json((directory / "catalog.json").read_bytes())
    if (
        digest(catalog) != expected_catalog_sha256
        or digest(catalog["manifest"]) != catalog["manifest_sha256"]
        or catalog["archive_bytes"] > max_bytes
    ):
        raise Denied("Unreviewed/corrupted catalog or restore size limit")
    with tempfile.TemporaryDirectory(dir=directory) as temp:
        archive = Path(temp) / "checkpoint.tar"
        h = hashlib.sha256()
        size = 0
        with archive.open("xb") as out:
            for number, part in enumerate(catalog["parts"]):
                if part["name"] != f"part-{number:06d}.bin":
                    raise Denied("Missing, duplicated or reordered export part")
                path = directory / part["name"]
                if (
                    path.is_symlink()
                    or path.stat().st_size != part["bytes"]
                    or file_hash(path) != part["sha256"]
                ):
                    raise Denied("Corrupted export part")
                with path.open("rb") as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        out.write(block)
                        h.update(block)
                        size += len(block)
                        if size > max_bytes:
                            raise Denied("Restore exceeds disk limit")
        if h.hexdigest() != catalog["archive_sha256"] or size != catalog["archive_bytes"]:
            raise Denied("Reassembled archive mismatch")
        return restore_bundle(archive, destination, catalog["manifest_sha256"], max_bytes)
