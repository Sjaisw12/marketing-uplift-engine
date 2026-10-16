"""Read-only full-data checks of counts, independent CI values and frozen assets."""

import json
import tomllib
from pathlib import Path

import pytest

from marketing_uplift.data_contract import connection
from marketing_uplift.development_ate import REFERENCE_FILE, analysis_snapshot
from marketing_uplift.features import development_relation
from marketing_uplift.ingestion import file_sha256
from marketing_uplift.splits import verify_registry

pytestmark = pytest.mark.full_data
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def actual_ate(monkeypatch):
    monkeypatch.chdir(ROOT)
    config = tomllib.loads(Path("configs/project.toml").read_text())
    result = json.loads(Path("reports/development_ate.json").read_text())
    registry = json.loads(Path("artifacts/splits.json").read_text())
    return config, result, registry


def test_actual_counts_rates_and_external_interval_reference(actual_ate):
    _, result, _ = actual_ate
    s = result["statistics"]
    assert result["development_rows"] == 11882653
    assert (s["treatment"]["records"], s["treatment"]["visits"]) == (10100257, 490301)
    assert (s["control"]["records"], s["control"]["visits"]) == (1782396, 68089)
    assert s["treatment"]["visit_probability"] == 490301 / 10100257
    assert s["control"]["visit_probability"] == 68089 / 1782396
    reference = json.loads(REFERENCE_FILE.read_text())
    case = next(case for case in reference["cases"] if case["name"] == "development_counts")
    for key in ("statsmodels_interval", "decimal_interval"):
        assert s["interval_probability"] == pytest.approx(
            [float(x) for x in case[key]], rel=0, abs=1e-12
        )
    assert s["difference_percentage_points"] == 100 * s["difference_probability"]
    assert s["difference_per_1000_assignments"] == 1000 * s["difference_probability"]
    assert result["interval_method"]["reference_fixture_sha256"] == file_sha256(REFERENCE_FILE)
    assert result["interval_method"]["confidence_level"] == 0.95


def test_actual_counts_rechecked_through_frozen_development_boundary(actual_ate):
    config, result, registry = actual_ate
    with connection(config) as con:
        development_relation(con, config).project("row_id,treatment,visit").create_view(
            "development_check"
        )
        rows = con.execute("""SELECT treatment,visit,count(*) FROM development_check
                            GROUP BY treatment,visit""").fetchall()
    strata = {f"T{t}_V{v}": n for t, v, n in rows}
    assert strata == result["observed_strata"]
    assert sum(strata.values()) == registry["memberships"]["development"]["rows"]
    assert sum(strata.values()) != registry["rows"]  # Full source must never replace development.


def test_all_memberships_and_phase3_phase4_evidence_remain_identical(actual_ate):
    config, result, registry = actual_ate
    assert analysis_snapshot(config) == result["protected_artifacts"]
    assert result["protected_artifacts_unchanged"]
    assert len([p for p in result["protected_artifacts"] if p.endswith(".npy")]) == 12
    assert result["registry_sha256"] == file_sha256(config["experiment"]["split_registry"])
    assert result["phase4_audit_sha256"] == file_sha256("reports/data_audit.json")
    verify_registry(registry)
    assert not result["holdout_outcomes_analyzed"]
    assert not result["exposure_conditioned_on"]
    assert not result["treatment_on_treated_estimated"]
    assert not result["models_or_individual_uplift_computed"]
