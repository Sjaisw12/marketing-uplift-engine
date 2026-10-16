"""Budget, abstention, ties and outcome-blind application invariants."""

from decimal import Decimal

import numpy as np
import pytest

from marketing_uplift.data_contract import ContractError
from marketing_uplift.decision_engine import apply, choose, counts, feasible, ledger
from marketing_uplift.robust_metrics import MODELS


def spec(**kw):
    return dict(cost="0.01", value="1", budget_per_record="0.005", maximum_reach="0.5", **kw)


def evidence():
    point = np.full((15, 4, 6), 0.01)
    lower = point - 0.001
    support = {m: [dict(treatment_n=85, control_n=15, control_visits=30)] * 6 for m in MODELS}
    return point, lower, support


def test_positive_zero_and_negative_value_and_exact_ties():
    p, low, s = evidence()
    d = choose(p, low, s, spec(), 1000)
    assert d["model"] == "random"  # Frozen model order resolves exact ties.
    assert d["reach_index"] == 5
    assert Decimal(d["ledger"]["spending"]) == Decimal("5")
    zero = dict(spec(), value="0")
    assert choose(p, low, s, zero, 1000)["reason_codes"] == ["zero_value"]
    assert choose(-p, -p, s, spec(), 1000)["model"] is None
    assert choose(-p, -p, s, spec(), 1000)["reason_codes"] == ["negative_estimated_net_benefit"]


def test_stops_first_failed_tranche_and_underspends():
    p, low, s = evidence()
    low[:, :, 1] = 0
    d = choose(p, low, s, spec(), 1000)
    assert d["reach_index"] == 1  # Never skip bad20% tranche to good30% tranche.
    assert Decimal(d["ledger"]["unspent_budget"]) == Decimal("4")
    low[:, :, 0] = 0.001  # Exactly zero net lower value must fail.
    assert choose(p, low, s, spec(), 1000)["model"] is None


def test_assumption_disagreement_inconclusive_and_support_reasons():
    p, low, s = evidence()
    low[:, :, 0] = -1
    assert choose(p, low, s, spec(), 1000)["reason_codes"] == ["inconclusive_lower_bound"]
    p[0, :, 0] = -1
    assert choose(p, low, s, spec(), 1000)["reason_codes"] == ["assumption_sensitive"]
    s = {m: [dict(treatment_n=85, control_n=15, control_visits=29)] * 6 for m in MODELS}
    assert choose(p, low, s, spec(), 1000)["reason_codes"] == ["insufficient_selection_support"]


def test_exact_budget_rounding_no_interpolation_and_zero_cost():
    p, low, s = evidence()
    tight = dict(spec(), budget_per_record="0.0005")
    assert choose(p, low, s, tight, 1000)["reason_codes"] == ["no_feasible_positive_reach"]
    assert not feasible(spec(), 1001, counts(1001)[5])  # ceil50% exceeds strict floor cap.
    with pytest.raises(ContractError, match="exceeds"):
        ledger(spec(), 1001, 501)
    free = dict(spec(), cost="0", budget_per_record="0")
    assert choose(p, low, s, free, 1000)["reach_index"] == 5
    assert choose(p, low, s, dict(spec(), budget_per_record="0"), 1000)["model"] is None


def test_assessment_application_never_uses_outcomes_or_reselects_model():
    p, low, s = evidence()
    d = choose(p, low, s, spec(), 1000)
    result = apply(d, spec(), 1001)
    assert result["model"] == d["model"]
    assert result["reach_index"] == 4 and result["rounding_adjustment"]
    assert result == apply(d, spec(), 1001)
    assert apply(dict(d, reach_index=0, model=None), spec(), 1001)["ledger"]["selected"] == 0


@pytest.mark.parametrize("key,value", [("cost", "NaN"), ("value", "-1"), ("maximum_reach", "1.1")])
def test_invalid_economics_stop(key, value):
    with pytest.raises(ContractError):
        feasible(dict(spec(), **{key: value}), 1000, 0)


def test_money_is_exact_beyond_default_decimal_precision():
    config = dict(
        spec(),
        cost="0.00000000000000000000000000001",
        budget_per_record="12345678901234567890123456789.123456789",
    )
    value = ledger(config, 1, 0)
    assert value["budget"] == "12345678901234567890123456789.123456789"
    assert Decimal(value["unspent_budget"]) == Decimal(value["budget"])
