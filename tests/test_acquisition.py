"""Offline failure tests use tiny byte fixtures, never the production archive."""

import hashlib
import http.client
import io
import json
import socket
import urllib.error
from types import SimpleNamespace

import pytest

from marketing_uplift import acquisition
from marketing_uplift.cli import main

PAYLOAD = b"tiny compressed-byte fixture\n"


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = {
        "data": {
            "repository": "criteo/criteo-uplift",
            "filename": acquisition.FILENAME,
            "revision": "a" * 40,
            "sha256": hashlib.sha256(PAYLOAD).hexdigest(),
            "size_bytes": len(PAYLOAD),
            "rows": 13979592,
            "license": "CC-BY-NC-SA-4.0",
            "raw_directory": "data/raw",
            "manifest": "data/manifest.json",
        }
    }
    target = tmp_path / "data/raw" / acquisition.FILENAME
    manifest = tmp_path / "data/manifest.json"
    return config, target, manifest


def serve(monkeypatch, payload=PAYLOAD, failure=None):
    class Response(io.BytesIO):
        status = 200

        def read(self, size):
            if failure:
                if self.tell() == 0:
                    return super().read(5)
                raise failure
            return super().read(size)

    def open_request(request, timeout):
        assert request.full_url.endswith(f"/resolve/{'a' * 40}/{acquisition.FILENAME}")
        assert request.get_header("Accept-encoding") == "identity"
        assert timeout == 60
        return Response(payload)

    monkeypatch.setattr(
        acquisition.urllib.request,
        "build_opener",
        lambda handler: SimpleNamespace(open=open_request),
    )


def test_verified_download_and_provenance(setup, monkeypatch):
    config, target, manifest = setup
    serve(monkeypatch)
    result = acquisition.acquire(config)
    assert target.read_bytes() == PAYLOAD
    assert json.loads(manifest.read_text()) == result
    assert result["observed"]["sha256"] == hashlib.sha256(target.read_bytes()).hexdigest()
    assert result["observed"]["size_bytes"] == len(PAYLOAD)
    assert result["observed"]["row_count"] is None
    assert result["expected"]["row_count"] == 13979592
    assert result["source"]["revision"] == "a" * 40
    assert not list(target.parent.glob("*.part"))


def test_existing_copy_is_rehashed_without_network(setup, monkeypatch):
    config, target, manifest = setup
    serve(monkeypatch)
    acquisition.acquire(config)
    monkeypatch.setattr(
        acquisition.urllib.request,
        "build_opener",
        lambda *_: pytest.fail("Existing file must not use network"),
    )
    assert acquisition.acquire(config)["acquisition_mode"] == "reverified_existing"
    target.write_bytes(b"X" * len(PAYLOAD))
    previous_manifest = manifest.read_bytes()
    with pytest.raises(acquisition.AcquisitionError, match="SHA-256 mismatch"):
        acquisition.acquire(config)
    assert manifest.read_bytes() == previous_manifest  # Historical verification is not rewritten.


@pytest.mark.parametrize(
    "payload,message",
    [
        (PAYLOAD[:-1], "Size mismatch"),
        (b"X" * len(PAYLOAD), "SHA-256 mismatch"),
        (PAYLOAD + b"extra", "exceeds configured byte count"),
    ],
)
def test_invalid_download_is_never_published(setup, monkeypatch, payload, message):
    config, target, manifest = setup
    serve(monkeypatch, payload)
    with pytest.raises(acquisition.AcquisitionError, match=message):
        acquisition.acquire(config)
    assert not target.exists()
    assert not manifest.exists()
    assert not list(target.parent.glob("*.part"))


def test_interrupted_response_removes_partial_file(setup, monkeypatch):
    config, target, manifest = setup
    serve(monkeypatch, failure=http.client.IncompleteRead(b"partial", 100))
    with pytest.raises(acquisition.AcquisitionError, match="IncompleteRead"):
        acquisition.acquire(config)
    assert not target.exists()
    assert not manifest.exists()
    assert not list(target.parent.glob("*.part"))


@pytest.mark.parametrize(
    "failure, message",
    [
        (
            urllib.error.HTTPError(
                "https://us.aws.cdn.hf.co/file?secret=hidden", 403, "Forbidden", {}, None
            ),
            "HTTP 403.*us.aws.cdn.hf.co",
        ),
        (urllib.error.URLError(socket.gaierror(-3, "DNS failed")), "gaierror, errno=-3"),
        (
            urllib.error.URLError(ConnectionRefusedError(111, "proxy failed")),
            "ConnectionRefusedError, errno=111",
        ),
    ],
)
def test_network_errors_are_safe_and_fail_closed(setup, monkeypatch, failure, message):
    config, target, manifest = setup
    serve(monkeypatch, failure=failure)
    with pytest.raises(acquisition.AcquisitionError, match=message) as caught:
        acquisition.acquire(config)
    assert "secret" not in str(caught.value)
    assert "hidden" not in str(caught.value)
    assert not target.exists()
    assert not manifest.exists()
    assert not list(target.parent.glob("*.part"))


def test_disk_shortage_stops_before_network(setup, monkeypatch):
    config, target, manifest = setup
    monkeypatch.setattr(acquisition.shutil, "disk_usage", lambda _: SimpleNamespace(free=0))
    monkeypatch.setattr(
        acquisition.urllib.request,
        "build_opener",
        lambda *_: pytest.fail("Must check disk before network"),
    )
    with pytest.raises(acquisition.AcquisitionError, match="Insufficient disk"):
        acquisition.acquire(config)
    assert not target.exists()
    assert not manifest.exists()


def test_wrong_basename_is_rejected_before_writes(setup):
    config, target, manifest = setup
    config["data"]["filename"] = "criteo-uplift-v2.csv.gz"
    with pytest.raises(acquisition.AcquisitionError, match="basename"):
        acquisition.acquire(config)
    assert not target.parent.exists()
    assert not manifest.exists()


def test_cli_acquire_executes_implementation(setup, monkeypatch, capsys):
    config, target, _ = setup
    serve(monkeypatch)
    monkeypatch.setattr("marketing_uplift.cli.tomllib.load", lambda _: config)
    # An empty readable file is sufficient because parsing is isolated above.
    from pathlib import Path

    Path("project.toml").touch()
    assert main(["--config", "project.toml", "acquire"]) == 0
    assert json.loads(capsys.readouterr().out)["verification_status"] == "compressed_bytes_verified"
    assert target.exists()
