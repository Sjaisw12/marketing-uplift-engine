"""Independent tiny-fixture references for descriptive statistics and holdout exclusion."""

from collections import Counter
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import skew

from marketing_uplift import data_contract as dc
from marketing_uplift.data_audit import (
    AUDIT_JSON,
    AUDIT_MD,
    audit,
    balance_metrics,
    feature_summary,
    protected_snapshot,
)
from marketing_uplift.ingestion import ingest
from marketing_uplift.splits import get_member, initial_members, split


def prepare(source):
    config = source[0]
    dc.validate(config, full=True)
    ingest(config)
    return config, split(config)


def test_audit_matches_independent_numpy_and_counter_references(source):
    config, registry = prepare(source)
    original = protected_snapshot(config)
    result = audit(config)
    ids = get_member(registry["memberships"]["development"], registry["rows"])
    rows = np.array(source[1], dtype=float)[ids]
    assert result["development_rows"] == len(rows) == 68
    for i, column in enumerate(dc.FEATURES):
        values = rows[:, i]
        summary = result["features"][column]
        assert summary["mean"] == pytest.approx(values.mean())
        assert summary["stddev"] == pytest.approx(values.std(ddof=1))
        assert summary["skewness"] == pytest.approx(skew(values, bias=False))
        assert summary["quantiles"]["p25"] == pytest.approx(np.quantile(values, 0.25))
        assert summary["quantiles"]["p99"] == pytest.approx(np.quantile(values, 0.99))
        control = values[rows[:, 12] == 0]
        treated = values[rows[:, 12] == 1]
        reference = (treated.mean() - control.mean()) / np.sqrt(
            (treated.var(ddof=1) + control.var(ddof=1)) / 2
        )
        assert summary["balance"]["smd"] == pytest.approx(reference)
        cuts = summary["distribution_cutoffs"]
        gap = max(abs(np.mean(treated <= cut) - np.mean(control <= cut)) for cut in cuts)
        assert summary["balance"]["grid_ecdf_gap"] == pytest.approx(gap)
        assert sum(summary["histogram_counts_by_treatment"]["0"]) == len(control)
        assert sum(summary["histogram_counts_by_treatment"]["1"]) == len(treated)
        lower, upper = summary["tukey_lower"], summary["tukey_upper"]
        assert summary["tukey_outlier_rows"] == np.count_nonzero(
            (values < lower) | (values > upper)
        )
    vectors = Counter(tuple(row[:12]) for row in rows)
    repeated = result["repeated_vectors"]
    assert repeated["distinct_vectors"] == len(vectors)
    assert repeated["rows_in_repeated_vectors"] == sum(n for n in vectors.values() if n > 1)
    assert repeated["excess_rows_over_distinct_vectors"] == len(rows) - len(vectors)
    assert repeated["max_multiplicity"] == max(vectors.values())
    assert sum(result["arm_rows"].values()) == len(rows)
    for entry in result["strata"]["splits"]:
        for role in ("train", "validation"):
            frozen = next(s for s in registry["development_splits"] if s["seed"] == entry["seed"])
            indices = get_member(frozen[role], registry["rows"])
            data = np.array(source[1], dtype=float)[indices]
            expected = {
                f"T{t}_V{v}": int(np.sum((data[:, 12] == t) & (data[:, 13] == v)))
                for t in (0, 1)
                for v in (0, 1)
            }
            assert entry[role] == expected
    assert original == protected_snapshot(config)
    assert result["protected_artifacts_unchanged"]
    assert AUDIT_JSON.exists() and AUDIT_MD.exists()
    assert "KS distance" in AUDIT_MD.read_text()


def test_holdout_feature_sentinel_never_enters_audit(source):
    config, rows, write = source
    labels = np.array([2 * int(row[12]) + int(row[13]) for row in rows], dtype=np.uint8)
    _, held = initial_members(labels, config)
    for index in held:
        rows[index][0] = "999999999"
    write(rows)
    config, _ = prepare(source)
    result = audit(config)
    assert result["features"]["f0"]["max"] == 2
    assert result["features"]["f0"]["mean"] < 3
    assert "999999999" not in AUDIT_MD.read_text()


@pytest.mark.parametrize(
    "control,treated,expected",
    [
        ({"mean": 1.0, "variance": 4.0}, {"mean": 3.0, "variance": 4.0}, 1.0),
        ({"mean": 1.0, "variance": 0.0}, {"mean": 1.0, "variance": 0.0}, 0.0),
        ({"mean": 1.0, "variance": 0.0}, {"mean": 2.0, "variance": 0.0}, None),
        ({"mean": 1.0, "variance": None}, {"mean": 2.0, "variance": 4.0}, None),
    ],
)
def test_smd_denominator_and_constant_cases(control, treated, expected):
    assert balance_metrics(control, treated)["smd"] == expected


def test_constant_discrete_feature_is_reported_without_deletion(source):
    config, rows, write = source
    for row in rows:
        row[0] = "7"
    write(rows)
    config, _ = prepare(source)
    result = audit(config)
    constant = result["features"]["f0"]
    assert constant["constant"] and constant["zero_iqr"] and constant["low_variance_relative"]
    assert constant["dominant_value_share"] == 1
    assert constant["tukey_outlier_rows"] == 0
    assert constant["balance"]["smd"] == 0
    assert constant["balance"]["variance_ratio"] is None
    assert result["development_rows"] == 68


def test_missing_membership_is_not_recreated(source):
    config, registry = prepare(source)
    path = Path(registry["memberships"]["holdout"]["path"])
    path.unlink()  # Isolated synthetic fixture only.
    with pytest.raises((dc.ContractError, FileNotFoundError)):
        audit(config)
    assert not path.exists()
    assert not AUDIT_JSON.exists()


def test_protected_change_aborts_publication(source, monkeypatch):
    config, _ = prepare(source)
    from marketing_uplift import data_audit

    original = data_audit.protected_snapshot
    calls = 0

    def changed(cfg):
        nonlocal calls
        result = original(cfg)
        calls += 1
        if calls == 2:
            result["simulated_change"] = {}
        return result

    monkeypatch.setattr(data_audit, "protected_snapshot", changed)
    with pytest.raises(dc.ContractError, match="Protected artifacts changed"):
        audit(config)
    assert not AUDIT_JSON.exists()


def test_outcome_cannot_be_sent_to_feature_analysis():
    with pytest.raises(dc.ContractError, match="pre-treatment"):
        feature_summary(None, "visit")


def test_numeric_patterns_and_heavy_tails_match_reference(source):
    config, rows, write = source
    for i, row in enumerate(rows):
        row[0] = str(1e9 if i % 11 == 0 else [-0.25, 0, 0, 0, 0.25][i % 5])
    write(rows)
    config, registry = prepare(source)
    report = audit(config)
    ids = get_member(registry["memberships"]["development"], registry["rows"])
    values = np.array([float(row[0]) for row in rows])[ids]
    summary = report["features"]["f0"]
    assert summary["zero_rows"] == np.count_nonzero(values == 0)
    assert summary["negative_rows"] == np.count_nonzero(values < 0)
    assert summary["integer_like_rows"] == np.count_nonzero(abs(values - np.round(values)) <= 1e-9)
    assert summary["skewness"] == pytest.approx(skew(values, bias=False))
    assert summary["skewness"] > 1
    assert summary["tukey_outlier_rows"] > 0
    assert report["development_rows"] == 68  # No outlier deletion.


def test_changed_raw_archive_stops_before_analysis(source):
    config, _ = prepare(source)
    dc.source_path(config).write_bytes(b"invalid synthetic archive")
    with pytest.raises(dc.ContractError, match="Raw archive identity changed"):
        audit(config)
    assert not AUDIT_JSON.exists()


def test_incomplete_frozen_protocol_cannot_start_eda(source):
    config = source[0]
    dc.validate(config, full=True)
    ingest(config)
    split(config, holdout_only=True)
    with pytest.raises(dc.ContractError, match="Freeze all development"):
        audit(config)
    assert not AUDIT_JSON.exists()
