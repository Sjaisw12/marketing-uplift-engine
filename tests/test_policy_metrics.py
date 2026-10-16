"""Independent small-data checks of the declared statistical functionals."""

import itertools

import numpy as np
import pytest

from marketing_uplift.data_contract import ContractError
from marketing_uplift.policy_metrics import (
    MODELS,
    areas,
    bootstrap_counts,
    compressed_cells,
    evaluate,
    ranking,
    reach_bins,
    simultaneous,
    weights,
)


def test_ht_expectation_by_enumerating_all_assignments():
    y0, y1, policy, e = np.array([0, 1, 0]), np.array([1, 1, 0]), np.array([1, 0, 1]), 0.7
    expectation = 0
    for bits in itertools.product([0, 1], repeat=3):
        t = np.array(bits)
        y = np.where(t, y1, y0)
        probability = np.prod(np.where(t, e, 1 - e))
        estimate = np.mean(policy * t * y / e + (1 - policy) * (1 - t) * y / (1 - e))
        expectation += probability * estimate
    assert expectation == pytest.approx(np.mean(policy * y1 + (1 - policy) * y0))


def test_full_prefix_area_matches_independent_trapezoids():
    w = np.array([2.0, -4.0, 0.0, 3.0])
    order = np.array([3, 0, 2, 1])
    curve = np.r_[0, np.cumsum(w[order]) / 4]
    expected = np.trapezoid(curve, np.arange(5) / 4)
    assert areas(w, order)["ipw_auuc"] == pytest.approx(expected)
    assert areas(w, order)["ipw_qini_area"] == pytest.approx(expected - w.mean() / 2)
    assert areas(-np.ones(4), order)["ipw_auuc"] == -0.5


def test_constant_model_ties_equal_random_and_nested_exact_ceiling():
    ids = np.arange(37)
    priorities = np.random.default_rng(4).random(37)
    order = ranking(np.zeros(37), priorities, ids)
    np.testing.assert_array_equal(order, ranking(priorities, priorities, ids))
    bins = reach_bins(order)
    for k, q in enumerate([0.1, 0.2, 0.3, 0.4, 0.5]):
        assert (bins <= k).sum() == int(np.ceil(q * 37))


def test_compression_matches_row_bootstrap_for_every_given_multiplicity():
    rng = np.random.default_rng(37)
    n = 97
    bins = rng.integers(0, 6, (3, n), dtype=np.uint8)
    t, y = rng.integers(0, 2, (2, n))
    counts, cb, ct, cy = compressed_cells(bins, t, y)
    codes = ((bins[0].astype(int) * 6 + bins[1]) * 6 + bins[2]) * 4 + t * 2 + y
    occupied = np.unique(codes)
    for _ in range(50):
        rows = rng.integers(0, n, n)
        multiplicities = np.array([(codes[rows] == code).sum() for code in occupied])
        for e in [0.8, 0.85, 0.9]:
            for model in range(3):
                for k in range(1, 6):
                    ordinary = np.mean((bins[model, rows] < k) * weights(t[rows], y[rows], e))
                    compressed = multiplicities @ ((cb[model] < k) * weights(ct, cy, e)) / n
                    assert compressed == pytest.approx(ordinary)
    # Both algorithms have the same multinomial cell law; verify moments empirically.
    draws = bootstrap_counts(counts, 2000, 55)
    assert np.all(draws.sum(axis=1) == n)
    np.testing.assert_allclose(draws.mean(axis=0), counts, atol=0.15)


def test_paired_identical_policies_zero_bands_and_anchors():
    t = np.tile([0, 1, 1, 1], 50)
    y = np.tile([1, 1, 0, 1], 50)
    orders = {name: np.arange(200) for name in MODELS}
    result = evaluate(t, y, orders, [0.85, 0.8], seed=72)
    assert result == evaluate(t, y, orders, [0.85, 0.8], seed=72)
    scenario = result["scenarios"]["0.85"]
    assert scenario["anchors"]["none"] == pytest.approx(np.mean((1 - t) * y / 0.15))
    assert scenario["anchors"]["all"] == pytest.approx(np.mean(t * y / 0.85))
    assert scenario["s_minus_response_simultaneous_bands"] == [[0.0, 0.0]] * 5
    assert scenario["models"]["random"]["policies"][0]["value"] > 1  # never clip HT


def test_max_t_bands_cover_larger_family_than_marginal_normal_width():
    rng = np.random.default_rng(9)
    samples = rng.normal(size=(2000, 5))
    bands, critical = simultaneous(np.zeros(5), samples)
    assert critical > 1.96
    assert all(a < 0 < b for a, b in bands)


@pytest.mark.parametrize("e", [0, 1, -1, float("nan")])
def test_invalid_propensities(e):
    with pytest.raises(ContractError):
        weights(np.array([1]), np.array([1]), e)


def test_zero_events_and_absent_selected_arm_are_explicit():
    t = np.ones(20, dtype=int)
    y = np.zeros(20, dtype=int)
    result = evaluate(t, y, {name: np.arange(20) for name in MODELS}, [0.85], seed=9)
    scenario = result["scenarios"]["0.85"]
    assert scenario["anchors"]["none"] == scenario["anchors"]["all"] == 0
    assert scenario["s_minus_response_simultaneous_bands"] == [[0.0, 0.0]] * 5
    for model in scenario["models"].values():
        assert model["ipw_auuc"] == model["ipw_qini_area"] == 0
        for policy in model["policies"]:
            assert policy["selected_arm_rate_difference"] is None
            assert policy["low_control_visit_support"]
            assert policy["pointwise_value_interval"] == [0, 0]


def test_ranking_rejects_nonfinite_and_misaligned_scores():
    with pytest.raises(ContractError):
        ranking(np.array([0.0, float("nan")]), np.ones(2), np.arange(2))
    with pytest.raises(ContractError):
        ranking(np.zeros(2), np.ones(3), np.arange(2))
