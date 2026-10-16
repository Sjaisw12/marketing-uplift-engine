"""Financial transforms retain negative evidence and correct units."""

import pytest

from marketing_uplift.decision_reports import valued


def test_hypothetical_currency_and_per1000_are_distinct():
    row = valued(
        {"estimate": 0.002, "per_1000": 2, "pointwise_interval": [-0.001, 0.005]},
        {"value_per_incremental_visit": "3", "spending": "10"},
        1000,
    )
    assert row["incremental_visits"] == 2
    assert row["hypothetical_net_value"] == -4
    assert row["pointwise_net_interval"] == pytest.approx([-13, 5])
    assert row["pointwise_visits_interval"] == pytest.approx([-1, 5])
