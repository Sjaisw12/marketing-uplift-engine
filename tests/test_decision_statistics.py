"""Independent row formulas, covariance and simultaneous lower-band references."""

import numpy as np
import pytest

from marketing_uplift.data_contract import ContractError
from marketing_uplift.decision_metrics import (
    evaluate,
    lower_bands,
    scenario_keys,
    stream_moments,
)
from marketing_uplift.policy_metrics import reach_bins
from marketing_uplift.robust_metrics import gaussian_draws


def fixture(n=511):
    rng = np.random.default_rng(919)
    t = rng.binomial(1, 0.85, n)
    y = rng.binomial(1, 0.15, n)
    arrays = (t, y, *[rng.uniform(0.01, 0.8, n) for _ in range(4)])
    bins = np.array([reach_bins(rng.permutation(n)) for _ in range(4)])
    keys = scenario_keys([0.8, 0.825, 0.85, 0.875, 0.9])
    t, y, m0, m1, s0, s1 = arrays
    columns = []
    for method, e in keys:
        z = (
            t * y / e - (1 - t) * y / (1 - e)
            if method == "ipw"
            else (m1 - m0 + t * (y - m1) / e - (1 - t) * (y - m0) / (1 - e))
            if method == "dr"
            else (s1 - s0 + t * (y - s1) / e - (1 - t) * (y - s0) / (1 - e))
        )
        columns.extend([(bins[m] == k) * z for m in range(4) for k in range(6)])
    return bins, arrays, keys, np.column_stack(columns)


@pytest.mark.parametrize("batch", [1, 31, 65536])
def test_streaming_covariance_against_independent_row_matrix(batch):
    bins, arrays, keys, h = fixture()
    point, covariance, _ = stream_moments(bins, arrays, keys, batch)
    np.testing.assert_allclose(point, h.mean(axis=0), atol=2e-14, rtol=0)
    np.testing.assert_allclose(covariance, np.cov(h, rowvar=False, ddof=1) / len(h), atol=2e-14)
    # Covariance of direct row Gaussian multipliers, without calling production moments.
    row_factor = (h - h.mean(axis=0)).T / np.sqrt(len(h) * (len(h) - 1))
    np.testing.assert_allclose(covariance, row_factor @ row_factor.T, atol=2e-14)
    # Paired tranches share covariance; treating them as independent changes this quantity.
    c = np.zeros(h.shape[1])
    c[[0, 6]] = [1, -1]
    assert c @ covariance @ c == pytest.approx((h @ c).var(ddof=1) / len(h), abs=2e-14)


def test_lower_bound_independent_maximum_reference():
    point = np.arange(24, dtype=float) / 100
    variances = np.arange(1, 25, dtype=float) / 1000
    draws = np.random.default_rng(3).normal(size=(2000, 24)) * np.sqrt(variances)
    lower, critical, family = lower_bands(point, np.diag(variances), draws, 0)
    indices = [j for j in range(24) if j % 6 != 5]
    expected = sorted(max(row[j] / np.sqrt(variances[j]) for j in indices) for row in draws)
    # Linear 95th quantile between positions 1899 and1900, independently interpolated.
    q = expected[1899] * 0.95 + expected[1900] * 0.05
    assert family == 20
    assert critical == pytest.approx(q)
    np.testing.assert_allclose(lower, point - q * np.sqrt(variances))


def test_singular_zero_and_invalid_covariance():
    covariance = np.array([[1.0, 1.0], [1.0, 1.0]])
    draws, _ = gaussian_draws(covariance, 2000, 10)
    np.testing.assert_allclose(draws[:, 0], draws[:, 1], atol=1e-14)
    lower, critical, _ = lower_bands(np.zeros(24), np.zeros((24, 24)), np.zeros((2000, 24)), 0)
    assert critical == 0 and not lower.any()
    with pytest.raises(ContractError, match="positive semidefinite"):
        gaussian_draws(np.array([[1.0, 2.0], [2.0, 1.0]]), 2000, 0)


def test_complete_layout_and_deterministic_correlated_draws():
    _, arrays, _, _ = fixture(101)
    rng = np.random.default_rng(12)
    scores = {m: rng.random(101) for m in ("random", "response", "s_learner", "t_learner")}
    args = (np.arange(101), scores, arrays, [0.8, 0.825, 0.85, 0.875, 0.9], 2000, 18)
    a, b = evaluate(*args), evaluate(*args)
    assert a["uncertainty"]["family_size"] == 300
    assert a["uncertainty"]["replicates"] == 2000
    np.testing.assert_array_equal(a["draws"], b["draws"])
    np.testing.assert_array_equal(a["lower"], b["lower"])
