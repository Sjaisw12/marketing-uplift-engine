"""Pure presentation and hypothetical arithmetic over approved public aggregates.

No model, data-record, outcome, checkpoint, credential or execution imports.
The only runtime file read is the fixed checksum-pinned public JSON snapshot.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from portfolio.presentation import MODELS, SCENARIOS, load_snapshot

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "reports/portfolio/aggregate_results.json"
REACHES = (10, 20, 30, 40, 50)
EVALUATORS = ("dr", "ipw")
LABELS = {
    "random": "Random",
    "response": "Treated response",
    "s_learner": "S-learner",
    "t_learner": "T-learner",
    "all": "All-targeting anchor",
    "none": "No targeting (primary)",
}


@dataclass(frozen=True)
class Estimate:
    value: float
    low: float
    high: float


@dataclass(frozen=True)
class Illustration:
    assignments: int
    actual_reach: Decimal
    incremental_visits: Decimal
    scaled_benchmark_bounds: tuple[Decimal, Decimal] | None
    spend: Decimal
    net_value: Decimal
    unspent_budget: Decimal


def load_data():
    """Fixed asset only: no UI file paths, file uploads, remote fetch or fallback."""
    return load_snapshot(SNAPSHOT)


def _options(method, propensity, uncertainty, interval):
    if method not in EVALUATORS or type(propensity) not in (int, float):
        raise ValueError("Choose saved IPW/shared DR and an exact saved propensity")
    if propensity not in SCENARIOS:
        raise ValueError("Unsupported propensity; interpolation is not available")
    if uncertainty not in ("iid", "stratified") or interval not in ("pointwise", "simultaneous"):
        raise ValueError("Choose a saved uncertainty method and interval convention")


def _lookup(data, contrast, method, propensity, uncertainty, interval):
    _options(method, propensity, uncertainty, interval)
    row = next(
        (
            r
            for r in data["comparisons"]
            if (r["contrast"], r["evaluator"], r["propensity_assumption"], r["uncertainty"])
            == (contrast, method, propensity, uncertainty)
        ),
        None,
    )
    if row is None:
        raise ValueError("Saved comparison is missing; no substitute estimate is allowed")
    return Estimate(
        row["estimate_per_1000"], row[f"{interval}_low_per_1000"], row[f"{interval}_high_per_1000"]
    )


def estimate(
    data, model, reach, method="dr", propensity=0.85, uncertainty="iid", interval="simultaneous"
):
    if model == "all":
        if reach != 100:
            raise ValueError("All-targeting is a separate 100% reference anchor")
        name = "all_minus_none"
    else:
        if model not in MODELS or type(reach) is not int or reach not in REACHES:
            raise ValueError("Choose one frozen ranking and a saved 10–50% reach")
        name = f"{model}:{reach // 10}_minus_none"
    return _lookup(data, name, method, propensity, uncertainty, interval)


def paired(
    data,
    first,
    second,
    reach,
    method="dr",
    propensity=0.85,
    uncertainty="iid",
    interval="simultaneous",
):
    if first not in MODELS or second not in MODELS or first == second:
        raise ValueError("Choose two different frozen rankings")
    if type(reach) is not int or reach not in REACHES:
        raise ValueError("Choose a saved reach")
    a, b = sorted((first, second), key=MODELS.index)
    row = _lookup(data, f"{a}_minus_{b}:{reach // 10}", method, propensity, uncertainty, interval)
    return row if first == a else Estimate(-row.value, -row.high, -row.low)


def policy_rows(data, **options):
    return [
        {
            "Policy": LABELS[model],
            "Reach (%)": reach,
            "Gain / 1,000": e.value,
            "Lower": e.low,
            "Upper": e.high,
        }
        for model in MODELS
        for reach in REACHES
        for e in [estimate(data, model, reach, **options)]
    ]


def sensitivity_rows(data, model, reach, **options):
    return [
        {
            "Evaluator": "Shared DR" if method == "dr" else "IPW",
            "Assumed propensity": f"{e:.3f}",
            "Gain / 1,000": value.value,
            "Lower": value.low,
            "Upper": value.high,
        }
        for method in EVALUATORS
        for e in SCENARIOS
        for value in [estimate(data, model, reach, method, e, **options)]
    ]


def observed_rates(data):
    s = data["support"]
    control = s["control_visits"] / (s["control_nonvisits"] + s["control_visits"])
    treated = s["treatment_visits"] / (s["treatment_nonvisits"] + s["treatment_visits"])
    return control, treated, 100 * (treated - control)


def _money(value):
    try:
        if isinstance(value, bool):
            raise ValueError("Money inputs must be finite and nonnegative")
        result = Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError("Money inputs must be finite and nonnegative") from exc
    if not result.is_finite() or result < 0 or result > Decimal("1000000000000"):
        raise ValueError("Money inputs must be finite, nonnegative and at most 1 trillion")
    return result


def illustrate(data, model, reach, population, cost, visit_value, budget, **options):
    """Scale a saved benchmark gain; never selects a policy or constructs a new CI.

    Exact ceil(qN) count and Decimal budget checks. Unsupported reaches and
    unaffordable candidates fail; no trimming or interpolation. Scaled bounds
    are the original benchmark interval multiplied by N/1000, not transport CIs.
    """
    if type(population) is not int or not 1 <= population <= 1_000_000_000:
        raise ValueError("Eligible population must be an integer from 1 to 1 billion")
    _options(
        options.get("method", "dr"),
        options.get("propensity", 0.85),
        options.get("uncertainty", "iid"),
        options.get("interval", "simultaneous"),
    )
    c, v, cap = map(_money, (cost, visit_value, budget))
    if model == "none":
        if reach != 0:
            raise ValueError("The frozen primary policy always has zero reach")
        return Illustration(0, Decimal(0), Decimal(0), None, Decimal(0), Decimal(0), cap)
    e = estimate(data, model, reach, **options)
    if model == "all":
        raise ValueError("Simulator uses the fixed 10–50% diagnostic reaches or no targeting")
    count = (population * reach + 99) // 100
    spend = c * count
    if spend > cap:
        raise ValueError(
            f"Candidate needs {spend:,.2f} currency units, above the {cap:,.2f} budget. "
            "No automatic trimming: choose a saved lower reach or no targeting."
        )
    scale = Decimal(population) / 1000
    gain = Decimal(str(e.value)) * scale
    bounds = (Decimal(str(e.low)) * scale, Decimal(str(e.high)) * scale)
    return Illustration(
        count, Decimal(count) / population, gain, bounds, spend, v * gain - spend, cap - spend
    )
