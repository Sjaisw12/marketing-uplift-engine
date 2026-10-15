"""Failure-path and integrity tests use a tiny local gzip; no network or real rows."""

import gzip
import hashlib
import json
import tomllib
from pathlib import Path

import pytest

from marketing_uplift import acquisition
from marketing_uplift.acquisition import AcquisitionError
from marketing_uplift.cli import main


@pytest.fixture
def fixture_archive(tmp_path, monkeypatch):
    config_path = Path(__file__).resolve().parents[1] / "configs/project.toml"
    with config_path.open("rb") as stream:
        config = tomllib.load(stream)
    payload = gzip.compress(b"fixture bytes; no outcome analysis\n", mtime=0)
    identity = {
        **acquisition.SOURCE,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size_bytes": len(payload),
    }
    monkeypatch.setattr(acquisition, "SOURCE", identity)
    config["data"].update(identity)
    downloads = []

    def download(directory):
        downloads.append(directory)
        path = directory / identity["filename"]
        path.write_bytes(payload)
        return path

    monkeypatch.setattr(acquisition, "download_archive", download)
    return config, payload, downloads


def test_acquisition_and_cached_reverification_preserve_provenance(tmp_path, fixture_archive):
    config, payload, downloads = fixture_archive
    first = acquisition.acquire(config, tmp_path)
    archive = tmp_path / first["archive_path"]
    assert archive.read_bytes() == payload
    assert archive.stat().st_mode & 0o222 == 0
    assert first["row_count"] is None
    assert first["schema_validated"] is False
    assert first["archive_verified"] is True
    assert first["acquired_at_utc"] is not None
    assert len(downloads) == 1
    assert not downloads[0].exists()
    second = acquisition.acquire(config, tmp_path)
    assert len(downloads) == 1
    assert second["acquired_at_utc"] == first["acquired_at_utc"]
    assert second["first_verified_at_utc"] == first["first_verified_at_utc"]
    assert second["last_verified_at_utc"] >= first["last_verified_at_utc"]
    assert json.loads((tmp_path / "data/manifest.json").read_text()) == second


@pytest.mark.parametrize("damage", ["truncate", "same_size"])
def test_cached_bytes_are_rehashed_and_never_replaced(tmp_path, fixture_archive, damage):
    config, payload, downloads = fixture_archive
    first = acquisition.acquire(config, tmp_path)
    archive = tmp_path / first["archive_path"]
    manifest = tmp_path / "data/manifest.json"
    receipt_before = manifest.read_bytes()
    archive.chmod(0o644)
    damaged = payload[:-1] if damage == "truncate" else bytes([payload[0] ^ 1]) + payload[1:]
    archive.write_bytes(damaged)
    with pytest.raises(AcquisitionError, match="mismatch"):
        acquisition.acquire(config, tmp_path)
    assert archive.read_bytes() == damaged
    assert manifest.read_bytes() == receipt_before
    assert len(downloads) == 1


def test_bad_download_never_becomes_final_archive(tmp_path, fixture_archive, monkeypatch):
    config, payload, _ = fixture_archive

    def download(directory):
        path = directory / acquisition.SOURCE["filename"]
        path.write_bytes(bytes([payload[0] ^ 1]) + payload[1:])
        return path

    monkeypatch.setattr(acquisition, "download_archive", download)
    with pytest.raises(AcquisitionError, match="SHA-256 mismatch"):
        acquisition.acquire(config, tmp_path)
    assert not (tmp_path / "data/manifest.json").exists()
    assert list((tmp_path / "data/raw").iterdir()) == []


def test_wrong_filename_rejected_even_for_identical_bytes(tmp_path, fixture_archive):
    _, payload, _ = fixture_archive
    wrong_name = tmp_path / "old-version.csv.gz"
    wrong_name.write_bytes(payload)
    with pytest.raises(AcquisitionError, match="basename"):
        acquisition.verify_archive(wrong_name)


@pytest.mark.parametrize("field", ["filename", "revision", "sha256", "size_bytes", "repository"])
def test_config_cannot_redefine_authoritative_identity(tmp_path, fixture_archive, field):
    config, _, downloads = fixture_archive
    config["data"][field] = "incorrect"
    with pytest.raises(AcquisitionError, match="authoritative source lock"):
        acquisition.acquire(config, tmp_path)
    assert not downloads
    assert list(tmp_path.iterdir()) == []


def test_conflicting_manifest_is_not_overwritten(tmp_path, fixture_archive):
    config, _, downloads = fixture_archive
    manifest = tmp_path / "data/manifest.json"
    manifest.parent.mkdir()
    manifest.write_text('{"sha256": "unrelated"}')
    before = manifest.read_bytes()
    with pytest.raises(AcquisitionError, match="different archive"):
        acquisition.acquire(config, tmp_path)
    assert manifest.read_bytes() == before
    assert not downloads


def test_network_failure_does_not_create_a_receipt(tmp_path, fixture_archive, monkeypatch):
    config, _, _ = fixture_archive

    def blocked(directory):
        raise AcquisitionError("Network access unavailable")

    monkeypatch.setattr(acquisition, "download_archive", blocked)
    with pytest.raises(AcquisitionError, match="Network access"):
        acquisition.acquire(config, tmp_path)
    assert not (tmp_path / "data/manifest.json").exists()
    assert list((tmp_path / "data/raw").iterdir()) == []


def test_sdk_uses_official_immutable_public_source(tmp_path, monkeypatch):
    import huggingface_hub

    observed = {}

    def fake_download(**kwargs):
        observed.update(kwargs)
        return str(tmp_path / acquisition.SOURCE["filename"])

    monkeypatch.setattr(huggingface_hub, "hf_hub_download", fake_download)
    acquisition.download_archive(tmp_path)
    assert observed["repo_id"] == "criteo/criteo-uplift"
    assert observed["revision"] == "82811785048bb633de2d55c02bab4e57066e6423"
    assert observed["repo_type"] == "dataset"
    assert observed["endpoint"] == "https://huggingface.co"
    assert observed["token"] is False


def test_cli_failure_reports_no_success(tmp_path, monkeypatch, capsys):
    config = Path(__file__).resolve().parents[1] / "configs/project.toml"
    monkeypatch.chdir(tmp_path)

    def blocked(config, root):
        raise AcquisitionError("Network access unavailable")

    monkeypatch.setattr("marketing_uplift.cli.acquire", blocked)
    with pytest.raises(SystemExit) as error:
        main(["--config", str(config), "acquire"])
    assert error.value.code == 2
    output = capsys.readouterr()
    assert not output.out
    assert "Network access unavailable" in output.err
    assert list(tmp_path.iterdir()) == []
