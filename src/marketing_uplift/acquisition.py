"""Pinned, streaming archive verification and atomic acquisition receipts."""

import hashlib
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SOURCE = {
    "repository": "criteo/criteo-uplift",
    "filename": "criteo-research-uplift-v2.1.csv.gz",
    "revision": "82811785048bb633de2d55c02bab4e57066e6423",
    "sha256": "2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc",
    "size_bytes": 311_422_618,
    "rows": 13_979_592,
    "license": "CC-BY-NC-SA-4.0",
}


class AcquisitionError(ValueError):
    """Acquisition cannot certify the authoritative archive."""


def source_url() -> str:
    return (
        f"https://huggingface.co/datasets/{SOURCE['repository']}/resolve/"
        f"{SOURCE['revision']}/{SOURCE['filename']}"
    )


def verify_archive(path: Path) -> dict[str, Any]:
    """Read compressed bytes only; never inspect outcomes or trust a prior receipt."""
    if path.name != SOURCE["filename"]:
        raise AcquisitionError("Archive basename is not the corrected v2.1 filename.")
    size = path.stat().st_size
    if size != SOURCE["size_bytes"]:
        raise AcquisitionError(f"Archive size mismatch: {size}; expected {SOURCE['size_bytes']}.")
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != SOURCE["sha256"]:
        raise AcquisitionError(f"SHA-256 mismatch: {digest}; expected {SOURCE['sha256']}.")
    return {"sha256": digest, "size_bytes": size}


def download_archive(directory: Path) -> Path:
    """Use the public official endpoint and immutable revision, without a token."""
    from huggingface_hub import hf_hub_download

    try:
        return Path(
            hf_hub_download(
                repo_id=SOURCE["repository"],
                filename=SOURCE["filename"],
                repo_type="dataset",
                revision=SOURCE["revision"],
                endpoint="https://huggingface.co",
                token=False,
                local_dir=directory,
                cache_dir=directory / ".hub-cache",
            )
        )
    except Exception as error:
        # SDK messages can contain temporary signed URLs; do not log those.
        raise AcquisitionError(
            f"Official Hugging Face download failed ({type(error).__name__}); "
            "check network access to huggingface.co and its storage redirects."
        ) from None


def _write_receipt(path: Path, receipt: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(receipt, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def acquire(config: dict[str, Any], root: Path) -> dict[str, Any]:
    """Verify existing bytes or promote a verified download, then record provenance."""
    data = config["data"]
    for key, expected in SOURCE.items():
        if data[key] != expected:
            raise AcquisitionError(f"Configured {key} differs from the authoritative source lock.")
    raw = root / data["raw_directory"]
    archive = raw / SOURCE["filename"]
    manifest = root / data["manifest"]
    previous: dict[str, Any] = {}
    if manifest.exists():
        try:
            previous = json.loads(manifest.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise AcquisitionError(
                "Existing manifest is unreadable; refusing to overwrite it."
            ) from None
        identity = {
            "repository": SOURCE["repository"],
            "revision": SOURCE["revision"],
            "filename": SOURCE["filename"],
            "sha256": SOURCE["sha256"],
            "size_bytes": SOURCE["size_bytes"],
        }
        if not isinstance(previous, dict) or any(
            previous.get(key) != value for key, value in identity.items()
        ):
            raise AcquisitionError(
                "Existing manifest identifies a different archive; refusing overwrite."
            )
    downloaded = False
    if archive.exists():
        verified = verify_archive(archive)
    else:
        raw.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".acquire-", dir=raw) as staging:
            candidate = download_archive(Path(staging))
            verified = verify_archive(candidate)
            try:
                # Hard-link promotion is atomic and cannot replace an existing raw archive.
                os.link(candidate, archive)
                downloaded = True
            except FileExistsError:
                verified = verify_archive(archive)
            archive.chmod(0o444)
    now = datetime.now(UTC).isoformat()
    receipt = {
        **previous,
        "manifest_version": 1,
        "repository": SOURCE["repository"],
        "revision": SOURCE["revision"],
        "filename": SOURCE["filename"],
        "source_url": source_url(),
        "license": SOURCE["license"],
        "citation": (
            "Diemert, Betlei, Renaudin and Amini (2018). "
            "A Large Scale Benchmark for Uplift Modeling. AdKDD & TargetAd."
        ),
        "archive_path": archive.relative_to(root).as_posix(),
        **verified,
        "acquired_at_utc": previous.get("acquired_at_utc", now if downloaded else None),
        "first_verified_at_utc": previous.get("first_verified_at_utc", now),
        "last_verified_at_utc": now,
        "acquisition_method": previous.get(
            "acquisition_method",
            "huggingface_hub.hf_hub_download" if downloaded else "existing_local_archive",
        ),
        "expected_row_count": SOURCE["rows"],
        "row_count": previous.get("row_count"),
        "schema_validated": previous.get("schema_validated", False),
        "archive_verified": True,
    }
    _write_receipt(manifest, receipt)
    return receipt
