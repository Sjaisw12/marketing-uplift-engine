"""Explicit full-data integration gates; missing artifacts fail rather than skip."""

import hashlib
import json
import tomllib
from pathlib import Path

import pytest

from marketing_uplift import data_contract as dc
from marketing_uplift.ingestion import inspect_parquet, parquet_path, require_ingestion
from marketing_uplift.splits import split

pytestmark = pytest.mark.full_data
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def full_config(monkeypatch):
    monkeypatch.chdir(ROOT)
    return tomllib.loads((ROOT / "configs/project.toml").read_text())


def test_actual_source_identity_and_full_contract(full_config):
    dc.verified_source(full_config)
    result = dc.require_validation(full_config)
    assert result["observed_rows"] == 13979592
    assert result["independent_csv_audit"]["records"] == 13979592
    assert result["independent_csv_audit"]["wrong_field_count"] == 0
    assert all(v == 0 for checks in result["quality_counts"].values() for v in checks.values())


def test_full_parquet_mapping_matches_source(full_config):
    evidence = require_ingestion(full_config)
    with dc.connection(full_config) as con:
        observed = inspect_parquet(con, parquet_path(full_config))
    assert observed == evidence["row_mapping"] == dc.require_validation(full_config)["row_mapping"]


def test_all_frozen_splits_reconstruct_without_registry_changes(full_config):
    path = Path(full_config["experiment"]["split_registry"])
    before = path.read_bytes()
    registry = split(full_config, reconstruct_missing=True)
    assert registry["state"] == "complete"
    assert len(registry["development_splits"]) == 5
    assert path.read_bytes() == before
    evidence = json.loads(Path("reports/split_reconstruction.json").read_text())
    assert evidence["memberships_reconstructed_and_hash_matched"] == 12
    assert evidence["registry_sha256"] == hashlib.sha256(before).hexdigest()
