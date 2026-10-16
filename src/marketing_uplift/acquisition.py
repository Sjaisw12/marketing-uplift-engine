"""Acquire compressed source bytes only; no schema, rows, or outcomes are inspected."""

import hashlib
import http.client
import json
import os
import re
import shutil
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

CHUNK_SIZE = 1024 * 1024
FILENAME = "criteo-research-uplift-v2.1.csv.gz"


class AcquisitionError(Exception):
    """An acquisition failed without publishing unverified bytes."""


class Redirects(urllib.request.HTTPRedirectHandler):
    """Retain destination hosts, never signed URLs or authentication headers."""

    def __init__(self):
        super().__init__()
        self.hosts = ["huggingface.co"]

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        if parsed.scheme != "https":
            raise AcquisitionError("Refusing a redirect outside HTTPS")
        self.hosts.append(parsed.hostname)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def verify(path: Path, expected_size: int, expected_sha256: str) -> tuple[int, str]:
    """Hash actual bytes from disk, including on every reuse."""
    size = path.stat().st_size
    if size != expected_size:
        raise AcquisitionError(f"Size mismatch: expected {expected_size}, observed {size} bytes")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    observed = digest.hexdigest()
    if observed != expected_sha256:
        raise AcquisitionError(f"SHA-256 mismatch: expected {expected_sha256}, observed {observed}")
    return size, observed


def acquire(config: dict) -> dict:
    """Download into a temporary file; publish only after disk-based verification."""
    data = config["data"]
    if data["filename"] != FILENAME:
        raise AcquisitionError(f"Expected corrected v2.1 basename {FILENAME}")
    if not re.fullmatch(r"[0-9a-f]{40}", data["revision"]):
        raise AcquisitionError("Source revision must be a full commit SHA")
    if not re.fullmatch(r"[0-9a-f]{64}", data["sha256"]):
        raise AcquisitionError("Expected SHA-256 must contain 64 lowercase hex digits")
    if not isinstance(data["size_bytes"], int) or data["size_bytes"] <= 0:
        raise AcquisitionError("Expected byte count must be positive")
    if not re.fullmatch(r"[\w-]+/[\w.-]+", data["repository"]):
        raise AcquisitionError("Invalid source repository")
    url = (
        f"https://huggingface.co/datasets/{data['repository']}/resolve/"
        f"{data['revision']}/{data['filename']}"
    )
    target = Path(data["raw_directory"]) / data["filename"]
    manifest_path = Path(data["manifest"])
    target.parent.mkdir(parents=True, exist_ok=True)
    redirects = Redirects()
    mode = "reverified_existing" if target.exists() else "downloaded"
    if not target.exists():
        free = shutil.disk_usage(target.parent).free
        required = data["size_bytes"] + CHUNK_SIZE
        if free < required:
            raise AcquisitionError(
                f"Insufficient disk space: {free} free, {required} required bytes"
            )
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=target.parent, prefix=target.name + ".", suffix=".part", delete=False
            ) as output:
                temporary = Path(output.name)
                request = urllib.request.Request(url, headers={"Accept-Encoding": "identity"})
                # The default opener preserves inherited proxy settings and TLS verification.
                opener = urllib.request.build_opener(redirects)
                with opener.open(request, timeout=60) as response:
                    if response.status != 200:
                        raise AcquisitionError(f"Unexpected HTTP status {response.status}")
                    count = 0
                    while chunk := response.read(CHUNK_SIZE):
                        count += len(chunk)
                        if count > data["size_bytes"]:
                            raise AcquisitionError("Download exceeds configured byte count")
                        output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
            size, digest = verify(temporary, data["size_bytes"], data["sha256"])
            temporary.replace(target)
        except urllib.error.HTTPError as error:
            host = urllib.parse.urlsplit(error.url).hostname
            raise AcquisitionError(f"HTTP {error.code} from destination host {host}") from None
        except urllib.error.URLError as error:
            reason = error.reason
            raise AcquisitionError(
                f"Network failure at destination host {redirects.hosts[-1]}: "
                f"{type(reason).__name__}, errno={getattr(reason, 'errno', None)}"
            ) from None
        except (TimeoutError, http.client.HTTPException) as error:
            raise AcquisitionError(
                f"Transfer failure at destination host {redirects.hosts[-1]}: "
                f"{type(error).__name__}"
            ) from None
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    else:
        size, digest = verify(target, data["size_bytes"], data["sha256"])

    manifest = {
        "manifest_version": 1,
        "verification_status": "compressed_bytes_verified",
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "acquisition_mode": mode,
        "source": {
            "repository": data["repository"],
            "revision": data["revision"],
            "filename": data["filename"],
            "url": url,
            "license": data["license"],
            "attribution": "Criteo AI Lab; Diemert et al., AdKDD & TargetAd, 2018",
        },
        "archive_path": target.as_posix(),
        "expected": {
            "size_bytes": data["size_bytes"],
            "sha256": data["sha256"],
            "row_count": data["rows"],
        },
        "observed": {"size_bytes": size, "sha256": digest, "row_count": None},
        "row_count_status": "not_measured; deferred to Phase 3",
        "destination_hosts_this_run": redirects.hosts if mode == "downloaded" else [],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_manifest = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", dir=manifest_path.parent, prefix="manifest.", suffix=".tmp", delete=False
        ) as stream:
            temporary_manifest = Path(stream.name)
            json.dump(manifest, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary_manifest.replace(manifest_path)
    finally:
        if temporary_manifest is not None:
            temporary_manifest.unlink(missing_ok=True)
    return manifest
