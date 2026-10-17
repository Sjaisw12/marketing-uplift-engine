"""Bounded, path-safe private checkpoint archive. No upload/download credentials."""

import os
import shutil
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

from .checkpoints import checked_path, verify_files
from .protocol import Denied, canonical, digest, strict_json


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(path, value):
    path = Path(path)
    with path.open("xb") as stream:
        stream.write(canonical(value))
        stream.flush()
        os.fsync(stream.fileno())
    sync_directory(path.parent)


def export_bundle(root, manifest, destination):
    verify_files(root, manifest)
    # Exclusive creation: never replace a previous checkpoint archive.
    with Path(destination).open("xb") as stream:
        with tarfile.open(fileobj=stream, mode="w") as archive:
            with tempfile.TemporaryDirectory() as tmp:
                metadata = Path(tmp) / "manifest.json"
                metadata.write_bytes(canonical(manifest))
                archive.add(metadata, arcname="manifest.json", recursive=False)
            for name in manifest["files"]:
                archive.add(checked_path(root, name), arcname="files/" + name, recursive=False)
        stream.flush()
        os.fsync(stream.fileno())
    sync_directory(Path(destination).parent)
    return digest(manifest)


def restore_bundle(archive_path, destination, expected_manifest_sha256, max_bytes):
    destination = Path(destination)
    if destination.exists() or max_bytes <= 0:
        raise Denied("Restore requires absent destination and explicit byte limit")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
        root = Path(tmp)
        total, seen = 0, set()
        with tarfile.open(archive_path, "r:") as archive:
            for item in archive:
                part = PurePosixPath(item.name)
                if (
                    not item.isfile()
                    or item.name in seen
                    or part.is_absolute()
                    or ".." in part.parts
                    or str(part) != item.name
                    or (item.name != "manifest.json" and not item.name.startswith("files/"))
                ):
                    raise Denied("Unsafe, duplicate or unsupported bundle member")
                total += item.size
                if total > max_bytes or len(seen) >= 1024 or len(item.name) > 512:
                    raise Denied("Bundle exceeds approved restore byte limit")
                seen.add(item.name)
                target = root.joinpath(*part.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(item) as source, target.open("xb") as out:
                    shutil.copyfileobj(source, out, length=1024 * 1024)
                    out.flush()
                    os.fsync(out.fileno())
        manifest = strict_json((root / "manifest.json").read_bytes())
        if digest(manifest) != expected_manifest_sha256:
            raise Denied("Restore manifest identity mismatch")
        if seen != {"manifest.json", *["files/" + n for n in manifest["files"]]}:
            raise Denied("Bundle has missing or undeclared files")
        if "restored-manifest.json" in manifest["files"]:
            raise Denied("Reserved restore metadata filename")
        verify_files(root / "files", manifest)
        # Destination is new: no merging with stale files or overwrite recovery.
        (root / "files").rename(destination)
        atomic_json(destination / "restored-manifest.json", manifest)
        sync_directory(destination.parent)
    return manifest
