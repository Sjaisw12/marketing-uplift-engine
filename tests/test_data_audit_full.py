"""Read-only full-data audit integration checks; never reconstruct or analyze holdout."""

import json
import tomllib
from pathlib import Path

import pytest

from marketing_uplift import data_contract as dc
from marketing_uplift.data_audit import protected_snapshot, stratum_counts
from marketing_uplift.features import development_relation
from marketing_uplift.ingestion import file_sha256

pytestmark = pytest.mark.full_data
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def actual_audit(monkeypatch):
    monkeypatch.chdir(ROOT)
    config = tomllib.loads(Path("configs/project.toml").read_text())
    report = json.loads(Path("reports/data_audit.json").read_text())
    registry = json.loads(Path("artifacts/splits.json").read_text())
    return config, report, registry


def test_actual_audit_preserved_all_phase3_assets(actual_audit):
    config, report, registry = actual_audit
    assert report["protected_artifacts_unchanged"]
    assert protected_snapshot(config) == report["protected_artifacts"]
    assert report["registry_sha256"] == file_sha256("artifacts/splits.json")
    assert (
        report["development_membership_sha256"] == registry["memberships"]["development"]["sha256"]
    )
    assert not report["holdout_outcome_analysis"]
    assert not report["treatment_effects_or_models_computed"]


def test_actual_development_counts_independently_rechecked(actual_audit):
    config, report, registry = actual_audit
    assert report["development_rows"] == registry["memberships"]["development"]["rows"] == 11882653
    with dc.connection(config) as con:
        development_relation(con, config).create_view("audit_development")
        assert stratum_counts(con) == report["strata"]["development"]
    for entry in report["strata"]["splits"]:
        frozen = next(s for s in registry["development_splits"] if s["seed"] == entry["seed"])
        for role in ("train", "validation"):
            assert sum(entry[role].values()) == frozen[role]["rows"]
        for key, n in report["strata"]["development"].items():
            assert entry["train"][key] + entry["validation"][key] == n


def test_actual_feature_and_duplicate_aggregates_cover_all_development(actual_audit):
    _, report, _ = actual_audit
    n = report["development_rows"]
    assert list(report["features"]) == dc.FEATURES
    for summary in report["features"].values():
        assert summary["rows"] == n
        for t in ("0", "1"):
            assert sum(summary["histogram_counts_by_treatment"][t]) == report["arm_rows"][t]
        assert 0 <= summary["tukey_outlier_rows"] <= n
        assert 0 <= summary["balance"]["grid_ecdf_gap"] <= 1
    vectors = report["repeated_vectors"]
    assert vectors["rows"] == n
    assert vectors["distinct_vectors"] + vectors["excess_rows_over_distinct_vectors"] == n
    assert sum(vectors["group_multiplicity_buckets"].values()) == vectors["distinct_vectors"]
