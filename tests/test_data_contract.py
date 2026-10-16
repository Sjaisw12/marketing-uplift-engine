"""Small fixtures exercise strict contract failures without touching the real archive."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from marketing_uplift import data_contract as dc
from marketing_uplift.acquisition import acquire

ROOT = Path(__file__).resolve().parents[1]


def test_full_contract_and_independent_row_mapping(source):
    config, rows, _ = source
    report = dc.validate(config, full=True)
    assert report["status"] == "passed"
    assert report["observed_rows"] == len(rows)
    assert all(v == 0 for checks in report["quality_counts"].values() for v in checks.values())
    # Independent, simple Python parser provides a golden row-to-ID mapping.
    canonical = np.empty(len(rows), dtype=dc.DTYPE)
    canonical["row_id"] = np.arange(len(rows))
    for j, col in enumerate(dc.COLUMNS):
        canonical[col] = [float(row[j]) for row in rows]
    assert report["row_mapping"]["sha256"] == hashlib.sha256(canonical.tobytes()).hexdigest()
    config["resources"]["batch_rows"] = 7
    assert dc.validate(config, full=True)["row_mapping"] == report["row_mapping"]


@pytest.mark.parametrize(
    "column,value",
    [
        ("f0", "nonsense"),
        ("f2", ""),
        ("f3", "NaN"),
        ("f4", "inf"),
        ("visit", "2"),
        ("exposure", "1.0"),
    ],
)
def test_anomalies_stop_with_counts_and_no_pass_artifact(source, column, value):
    _, rows, write = source
    rows[0][dc.COLUMNS.index(column)] = value
    config = write(rows)
    with pytest.raises(dc.ContractError, match="Validation stopped"):
        dc.validate(config, full=True)
    assert not dc.VALIDATION.exists()
    evidence = list(Path("reports/contract_failures").glob("*.json"))
    assert len(evidence) == 1
    assert json.loads(evidence[0].read_text())["status"] == "failed"


@pytest.mark.parametrize("problem", ["header", "duplicate", "row_count", "rate", "short_record"])
def test_schema_rows_and_rate_contract(source, problem):
    config, rows, write = source
    if problem == "header":
        config = write(header=dc.COLUMNS[:-1])
    elif problem == "duplicate":
        config = write(header=dc.COLUMNS[:-1] + ["visit"])
    elif problem == "row_count":
        config["data"]["rows"] += 1
    elif problem == "rate":
        config["contract"]["visit_rate_bounds"] = [0.01, 0.02]
    else:
        rows[0].pop()
        config = write(rows)
    with pytest.raises(dc.ContractError):
        dc.validate(config, full=True)
    assert not dc.VALIDATION.exists()


def test_acquisition_rerun_cannot_erase_validated_rows(source):
    config, _, _ = source
    dc.validate(config, full=True)
    before = dc.VALIDATION.read_bytes()
    acquire(config)
    assert dc.VALIDATION.read_bytes() == before
    assert json.loads(dc.VALIDATION.read_text())["observed_rows"] == 80
    assert json.loads(Path(config["data"]["manifest"]).read_text())["observed"]["row_count"] is None


def test_no_sampled_contract_pass(source):
    with pytest.raises(dc.ContractError, match="--full"):
        dc.validate(source[0])


def test_blank_record_cannot_be_silently_skipped(source):
    config, rows, write = source
    config = write(rows + [[]])
    config["data"]["rows"] = len(rows)  # A skipping parser would otherwise accept this.
    with pytest.raises(dc.ContractError, match="Independent CSV"):
        dc.validate(config, full=True)


def test_bad_checksum_preserves_failure_evidence(source):
    config = source[0]
    config["data"]["sha256"] = "0" * 64
    with pytest.raises(dc.ContractError):
        dc.validate(config, full=True)
    assert list(Path("reports/contract_failures").glob("*.json"))
