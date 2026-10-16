"""Offline external references and synthetic pipeline checks; no holdout analysis."""

import json
from pathlib import Path

import numpy as np
import pytest

from marketing_uplift import data_contract as dc
from marketing_uplift.data_audit import audit
from marketing_uplift.development_ate import (
    ATE_JSON,
    ATE_MD,
    REFERENCE_FILE,
    Z,
    analysis_snapshot,
    analyze_development,
    assignment_contrast,
    wilson,
)
from marketing_uplift.ingestion import ingest
from marketing_uplift.splits import get_member, split

REFERENCE = json.loads(REFERENCE_FILE.read_text())


@pytest.mark.parametrize("case", REFERENCE["cases"], ids=lambda case: case["name"])
def test_newcombe_agrees_with_external_and_high_precision_references(case):
    result = assignment_contrast(
        case["treatment_visits"], case["treatment_n"], case["control_visits"], case["control_n"]
    )
    assert result["difference_probability"] == pytest.approx(case["expected_difference"], abs=1e-15)
    for name in ("statsmodels_interval", "decimal_interval"):
        assert result["interval_probability"] == pytest.approx(
            [float(v) for v in case[name]], rel=0, abs=REFERENCE["absolute_tolerance"]
        )
    low, high = result["interval_probability"]
    assert -1 <= low <= result["difference_probability"] <= high <= 1


def test_zero_and_all_event_wilson_limits_have_known_closed_form():
    upper = Z**2 / (10 + Z**2)
    assert wilson(0, 10) == pytest.approx([0, upper], abs=1e-15)
    assert wilson(10, 10) == pytest.approx([1 - upper, 1], abs=1e-15)
    assert assignment_contrast(0, 10, 0, 10)["interval_probability"] == pytest.approx(
        [-upper, upper]
    )


@pytest.mark.parametrize(
    "bad",
    [
        (-1, 10, 1, 10),
        (11, 10, 1, 10),
        (1, 0, 1, 10),
        (1, 10, -1, 10),
        (1, 10, 11, 10),
        (1, 10, 1, 0),
        (1.0, 10, 1, 10),
        (1, 10.0, 1, 10),
        (True, 10, 1, 10),
        (1, 10, False, 10),
        (1, 10, 1, float("inf")),
    ],
)
def test_invalid_counts_fail_explicitly(bad):
    with pytest.raises(dc.ContractError, match="Counts require"):
        assignment_contrast(*bad)


@pytest.mark.parametrize("case", REFERENCE["cases"][:6], ids=lambda case: case["name"])
def test_arm_swap_changes_sign_and_reverses_interval(case):
    args = [case[k] for k in ["treatment_visits", "treatment_n", "control_visits", "control_n"]]
    result = assignment_contrast(*args)
    swapped = assignment_contrast(args[2], args[3], args[0], args[1])
    low, high = result["interval_probability"]
    assert swapped["difference_probability"] == pytest.approx(-result["difference_probability"])
    assert swapped["interval_probability"] == pytest.approx([-high, -low], abs=1e-15)


def test_absolute_units_are_not_relative_percentage_changes():
    result = assignment_contrast(12, 100, 5, 100)
    assert result["difference_probability"] == pytest.approx(0.07)
    assert result["difference_percentage_points"] == pytest.approx(7)
    assert result["difference_per_1000_assignments"] == pytest.approx(70)
    assert result["difference_percentage_points"] != pytest.approx(100 * (0.12 / 0.05 - 1))
    for scale, key in [
        (100, "interval_percentage_points"),
        (1000, "interval_per_1000_assignments"),
    ]:
        assert result[key] == pytest.approx([scale * v for v in result["interval_probability"]])


def prepare(source):
    config = source[0]
    dc.validate(config, full=True)
    ingest(config)
    registry = split(config)
    audit(config)
    return config, registry


def test_pipeline_matches_development_counts_and_preserves_all_inputs(source):
    config, registry = prepare(source)
    before = analysis_snapshot(config)
    result = analyze_development(config)
    ids = get_member(registry["memberships"]["development"], registry["rows"])
    rows = np.array(source[1], dtype=float)[ids]
    for name, t in [("treatment", 1), ("control", 0)]:
        selected = rows[rows[:, 12] == t]
        actual = result["statistics"][name]
        assert actual["records"] == len(selected)
        assert actual["visits"] == int(selected[:, 13].sum())
        assert actual["visit_probability"] == pytest.approx(selected[:, 13].mean())
    assert result["development_rows"] == 68  # All 12 held-out synthetic rows excluded.
    assert result["interval_method"]["confidence_level"] == 0.95
    assert "nominal working-model" in result["interval_method"]["interpretation"]
    assert analysis_snapshot(config) == before
    assert result["protected_artifacts"] == before
    assert ATE_JSON.exists() and ATE_MD.exists()
    text = ATE_MD.read_text()
    assert "not an exact randomization-based" in text
    assert "percentage-point" in text.lower()
    assert not result["holdout_outcomes_analyzed"]
    assert not result["exposure_conditioned_on"]
    assert analyze_development(config)["statistics"] == result["statistics"]
    assert analysis_snapshot(config) == before


def test_exposure_and_conversion_do_not_change_the_contrast(source, monkeypatch, tmp_path):
    config, _ = prepare(source)
    first = analyze_development(config)["statistics"]
    variant = tmp_path / "variant"
    variant.mkdir()
    monkeypatch.chdir(variant)
    rows = source[1]
    for row in rows:
        row[14] = "1"
        row[15] = "1"
    source[2](rows)
    config, _ = prepare(source)
    assert analyze_development(config)["statistics"] == first


def test_counts_must_reconcile_with_completed_audit(source):
    config, _ = prepare(source)
    path = Path("reports/data_audit.json")
    report = json.loads(path.read_text())
    report["strata"]["development"]["T1_V1"] += 1
    path.write_text(json.dumps(report))
    with pytest.raises(dc.ContractError, match="disagree"):
        analyze_development(config)
    assert not ATE_JSON.exists()


def test_missing_membership_is_not_reconstructed(source):
    config, registry = prepare(source)
    missing = Path(registry["memberships"]["holdout"]["path"])
    missing.unlink()  # Isolated synthetic fixture only.
    with pytest.raises((OSError, dc.ContractError)):
        analyze_development(config)
    assert not missing.exists()
    assert not ATE_JSON.exists()


def test_provenance_change_stops_publication(source, monkeypatch):
    from marketing_uplift import development_ate

    config, _ = prepare(source)
    original = development_ate.analysis_snapshot
    calls = 0

    def changed(cfg):
        nonlocal calls
        result = original(cfg)
        calls += 1
        if calls == 2:
            result["simulated_change"] = {}
        return result

    monkeypatch.setattr(development_ate, "analysis_snapshot", changed)
    with pytest.raises(dc.ContractError, match="Protected inputs changed"):
        analyze_development(config)
    assert not ATE_JSON.exists()
