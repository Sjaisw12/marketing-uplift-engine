"""Independent synthetic references for DR, continuous moments and multiplier laws."""

import itertools

import numpy as np
import pytest

from marketing_uplift.data_contract import ContractError
from marketing_uplift.robust_metrics import (
    basis,
    cell_moments,
    coefficients,
    evaluate,
    gaussian_draws,
    layout,
    moments,
    summarize,
)


def test_dr_expectation_either_nuisance_correct_and_both_wrong_bias():
    p = 0.7
    y0, y1, policy = np.array([0.0, 1.0, 0.0]), np.array([1.0, 1.0, 0.0]), np.array([1, 0, 1])
    truth = np.mean(policy * y1 + (1 - policy) * y0)
    for e, m0, m1, correct in [
        (p, np.full(3, 0.2), np.full(3, 0.4), True),
        (0.4, y0, y1, True),
        (0.4, np.full(3, 0.2), np.full(3, 0.4), False),
    ]:
        mean = 0
        for bits in itertools.product([0, 1], repeat=3):
            t = np.array(bits)
            y = np.where(t, y1, y0)
            h0 = m0 + (1 - t) * (y - m0) / (1 - e)
            z = m1 - m0 + t * (y - m1) / e - (1 - t) * (y - m0) / (1 - e)
            mean += np.prod(np.where(t, p, 1 - p)) * np.mean(h0 + policy * z)
        if correct:
            assert mean == pytest.approx(truth)
        else:
            assert abs(mean - truth) > 0.05


def test_streaming_moments_equal_independent_direct_row_contributions():
    rng = np.random.default_rng(84)
    n = 257
    bins = rng.integers(0, 6, (4, n))
    t, y = rng.integers(0, 2, (2, n))
    m0, m1 = rng.random((2, n))
    keys = layout([0.8, 0.85, 0.9])
    v = basis(t, y, m0, m1)
    direct = np.array([coefficients(bins[:, i], keys) @ v[i] for i in range(n)])
    for batch in (1, 17, 65536):
        mean, cov = moments(*cell_moments(bins, t, y, m0, m1, batch), keys)
        np.testing.assert_allclose(mean, direct.mean(axis=0), atol=2e-14)
        np.testing.assert_allclose(cov, np.cov(direct, rowvar=False, ddof=1) / n, atol=2e-14)
    draws, meta = gaussian_draws(cov, 2000, 901)
    assert meta["minimum_eigenvalue"] > -1e-10
    # Direct row multipliers have the same Gaussian law; covariance is the exact target.
    ordinary = rng.normal(size=(2000, n)) @ (direct - direct.mean(axis=0)) / np.sqrt(n * (n - 1))
    np.testing.assert_allclose(
        np.std(draws, axis=0), np.std(ordinary, axis=0), rtol=0.1, atol=1e-10
    )
    assert (
        np.max(np.abs(draws[:, 0] - draws[:, 2])) > 0
    )  # scenarios share draws, not identical values


def test_singular_zero_variance_and_invalid_covariance():
    cov = np.array([[1.0, 1.0, 0], [1.0, 1.0, 0], [0, 0, 0]])
    delta, _ = gaussian_draws(cov, 2000, 4)
    np.testing.assert_allclose(delta[:, 0], delta[:, 1], atol=1e-14)
    row = summarize(np.ones(3), delta, cov, [1, -1, 0], 1e-12)
    assert row["estimate"] == 0 and row["pointwise_interval"] == [0, 0]
    assert row["standard_error"] == 0
    with pytest.raises(ContractError):
        gaussian_draws(np.diag([1.0, -0.1]), 2000, 4)


def test_paired_policies_zero_contrasts_ten_bands_and_reproducibility():
    rng = np.random.default_rng(17)
    n = 100
    t, y = rng.integers(0, 2, (2, n))
    ids = np.arange(n)
    scores = {
        m: np.arange(n, dtype=float) for m in ("random", "response", "s_learner", "t_learner")
    }
    m0, m1 = rng.random((2, n))
    a = evaluate(t, y, ids, scores, m0, m1, m0, m1, [0.8, 0.85, 0.9], 2000, 10)
    assert a == evaluate(t, y, ids, scores, m0, m1, m0, m1, [0.8, 0.85, 0.9], 2000, 10)
    assert a["simultaneous_family_size"] == 10
    for method in ("ipw", "dr"):
        scenario = a["estimates"][method]["0.85"]
        for row in scenario["models"]["t_learner"]["policies"]:
            contrast = row["paired"]["s_learner"]
            assert contrast["estimate"] == 0
            assert contrast["simultaneous_interval"] == [0, 0]
        if method == "ipw":
            assert scenario["anchors"]["all"]["estimate"] == pytest.approx(np.mean(t * y / 0.85))
        else:
            assert scenario["anchors"]["all"]["estimate"] == pytest.approx(
                np.mean(m1 + t * (y - m1) / 0.85)
            )


def test_selected_policy_formula_independent_of_coefficient_builder():
    rng = np.random.default_rng(541)
    n = 81
    t, y = rng.integers(0, 2, (2, n))
    m0, m1 = rng.random((2, n))
    bins = rng.integers(0, 6, (4, n))
    keys = layout([0.85])
    mean, _ = moments(*cell_moments(bins, t, y, m0, m1), keys)
    for j, (method, e, name, k) in enumerate(keys):
        if name == "none":
            selected = np.zeros(n)
        elif name == "all":
            selected = np.ones(n)
        else:
            selected = bins[["random", "response", "s_learner", "t_learner"].index(name)] < k
        if method == "ipw":
            expected = np.mean(selected * t * y / e + (1 - selected) * (1 - t) * y / (1 - e))
        else:
            expected = np.mean(
                selected * (m1 + t * (y - m1) / e)
                + (1 - selected) * (m0 + (1 - t) * (y - m0) / (1 - e))
            )
        assert mean[j] == pytest.approx(expected, abs=1e-13)


def test_zero_outcome_zero_nuisance_and_absent_control_support():
    n = 20
    t = np.ones(n, dtype=int)
    y = np.zeros(n, dtype=int)
    scores = {
        name: np.arange(n, dtype=float) for name in ("random", "response", "s_learner", "t_learner")
    }
    result = evaluate(
        t,
        y,
        np.arange(n),
        scores,
        y.astype(float),
        y.astype(float),
        y.astype(float),
        y.astype(float),
        [0.85],
        2000,
        81,
    )
    for method in ("ipw", "dr"):
        for model in result["estimates"][method]["0.85"]["models"].values():
            for p in model["policies"]:
                assert p["value"]["estimate"] == 0
                assert p["value"]["pointwise_interval"] == [0, 0]
    assert result["simultaneous_critical"] == 0
    assert result["support"]["t_learner"]["cumulative"][0]["selected_arm_rate_difference"] is None
