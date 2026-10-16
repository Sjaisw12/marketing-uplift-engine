"""Read-only real-data preservation, selection and statistical decision gates."""

import json
import os
import tomllib
from pathlib import Path

import pytest

from marketing_uplift.decision_verification import verify_split
from marketing_uplift.decisions import protected

pytestmark = pytest.mark.full_data
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def actual(monkeypatch):
    monkeypatch.chdir(ROOT)
    config = tomllib.loads(Path("configs/project.toml").read_text())
    path = Path(os.environ.get("PHASE8_EVIDENCE", "reports/phase_8_metrics.json"))
    if not path.exists():
        path = Path("reports/phase_8_first_split.json")
    return config, json.loads(path.read_text())


def test_frozen_phase6_phase7_and_membership_artifacts(actual):
    config, report = actual
    assert protected(config) == report["protected_before"]
    assert report["protected_unchanged"]
    assert len(report["roles"]) == 5
    for role in report["roles"].values():
        assert role["selection_rows"] == 1188265
        assert role["assessment_rows"] == 1188266
        assert role["selection_ids_sha256"] != role["assessment_ids_sha256"]


def test_decisions_against_direct_rows_covariance_and_saved_applications(actual, record_property):
    config, report = actual
    for split in report["splits"]:
        result = verify_split(config, report, split)
        record_property(f"split_{split['seed']}", json.dumps(result))
        assert result["verified_coordinates_per_role"] == 360
        assert result["maximum_direct_mean_error"] < 2e-12
        assert result["maximum_direct_variance_error"] < 2e-12
        for app in split["applications"].values():
            for comparator in app["comparisons"]["equal_actual_spending"]:
                assert comparator["selected"] == app["ledger"]["selected"]
