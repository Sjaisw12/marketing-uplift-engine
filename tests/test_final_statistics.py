"""Independent final policy-value and paired covariance/interval references."""

import numpy as np
import pytest

from marketing_uplift.data_contract import ContractError
from marketing_uplift.decision_metrics import scenario_keys
from marketing_uplift.final_metrics import contrast_family, evaluate_arrays, moments
from marketing_uplift.final_verification import check_numerics, row_reference
from marketing_uplift.robust_metrics import MODELS


def fixture(n=511):
    rng = np.random.default_rng(2029)
    t = (np.arange(n) % 4 >= 2).astype(int)
    y = (np.arange(n) % 2).astype(int)
    arrays = (t, y, *[rng.uniform(0.01, 0.8, n) for _ in range(4)])
    scores = {m: rng.random(n) for m in MODELS}
    settings = dict(
        scenarios=[0.8, 0.825, 0.85, 0.875, 0.9],
        replicates=2000,
        comparison_family_size=765,
        multiplier_seed=9000004,
        stratified_multiplier_seed=9000005,
        batch_rows=31,
    )
    return np.arange(n), scores, arrays, settings


@pytest.mark.parametrize("batch", [1, 31, 65536])
def test_final_streaming_and_stratified_covariance_against_rows(batch):
    ids, scores, arrays, settings = fixture()
    settings["batch_rows"] = batch
    result = evaluate_arrays(ids, scores, arrays, settings)
    evidence = check_numerics(result, arrays)
    assert evidence["family_size"] == 765 and evidence["coordinates"] == 375
    assert evidence["maximum_covariance_error"] < 2e-14
    assert evidence["maximum_stratified_covariance_error"] < 2e-14
    # All-target IPW conditional on T,Y composition is constant, not exact causal certainty.
    all_row = next(
        i for i, label in enumerate(result["family"]) if label["contrast"] == "all_minus_none"
    )
    assert result["stratified"]["standard_error"][all_row] == 0
    assert result["iid"]["standard_error"][all_row] > 0


def test_independent_family_contrasts_and_max_t_calculation():
    ids, scores, arrays, settings = fixture(103)
    result = evaluate_arrays(ids, scores, arrays, settings)
    labels, c = contrast_family(result["keys"])
    assert len({(r["evaluator"], r["propensity_assumption"], r["contrast"]) for r in labels}) == 765
    assert sum(r["contrast"].endswith("_minus_none") for r in labels) == 315
    h = row_reference(result["bins"], arrays, result["keys"])
    direct = h @ c.T
    np.testing.assert_allclose(result["iid"]["estimate"], direct.mean(axis=0), atol=1e-14)
    np.testing.assert_allclose(
        result["iid"]["standard_error"], direct.std(axis=0, ddof=1) / np.sqrt(len(h)), atol=1e-13
    )
    se = result["iid"]["standard_error"]
    draws = result["iid"]["draws"] @ c.T
    active = se > 0
    maximum = np.max(np.abs(draws[:, active] / se[active]), axis=1)
    critical = np.quantile(maximum, 0.95, method="linear")
    assert critical == result["iid"]["critical"]
    expected = np.c_[direct.mean(axis=0) - critical * se, direct.mean(axis=0) + critical * se]
    np.testing.assert_allclose(result["iid"]["simultaneous_interval"], expected, atol=1e-13)


def test_known_all_targeting_gain_ipw_and_dr():
    ids, scores, _, settings = fixture(100)
    t = np.r_[np.ones(80), np.zeros(20)]
    y = np.zeros(100)
    y[:16] = 1
    y[80:82] = 1
    arrays = (t, y, np.full(100, 0.1), np.full(100, 0.2), np.full(100, 0.1), np.full(100, 0.2))
    result = evaluate_arrays(ids, scores, arrays, settings)
    for method in ("ipw", "dr", "s_dr"):
        index = next(
            i
            for i, r in enumerate(result["family"])
            if r == dict(evaluator=method, propensity_assumption=0.8, contrast="all_minus_none")
        )
        assert result["iid"]["estimate"][index] == pytest.approx(0.1, abs=1e-14)


def test_zero_variance_and_one_record_stratum_is_not_substituted():
    ids, scores, arrays, settings = fixture(41)
    t = np.zeros(41)
    y = np.zeros(41)
    arrays = (t, y, *[np.zeros(41) for _ in range(4)])
    zero = evaluate_arrays(ids, scores, arrays, settings)
    assert zero["iid"]["critical"] == 0
    assert not zero["iid"]["simultaneous_interval"].any()
    y[0] = 1
    undefined = evaluate_arrays(ids, scores, arrays, settings)
    assert undefined["stratified"]["status"] == "undefined_nonempty_stratum_below_two"
    assert undefined["stratified_covariance"] is None


def test_invalid_probabilities_and_family_fail():
    ids, scores, arrays, settings = fixture(41)
    with pytest.raises(ContractError, match="Invalid final contribution layout"):
        # Invalid shape is an error, never a silently reduced sample.
        moments(np.zeros((4, 2)), arrays, scenario_keys(settings["scenarios"]))

    with pytest.raises(ContractError):
        evaluate_arrays(ids, scores, (*arrays[:2], np.full(41, np.nan), *arrays[3:]), settings)
    with pytest.raises(ContractError):
        evaluate_arrays(ids, scores, arrays, dict(settings, comparison_family_size=10))
