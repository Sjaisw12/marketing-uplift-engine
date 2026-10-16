"""Pure hypothetical budget constraints and frozen successive-tranche decisions."""

import hashlib
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal, InvalidOperation, localcontext

import numpy as np

from marketing_uplift.data_contract import ContractError
from marketing_uplift.robust_metrics import MODELS

REACH = ("0.1", "0.2", "0.3", "0.4", "0.5")


def decimal(value):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ContractError("Invalid hypothetical monetary input") from exc
    if not number.is_finite() or number < 0:
        raise ContractError("Hypothetical inputs must be finite and nonnegative")
    return number


def product(amount, count):
    with localcontext() as ctx:
        ctx.prec = max(28, len(amount.as_tuple().digits) + len(str(count)) + 3)
        return amount * count


def difference(a, b):
    with localcontext() as ctx:
        ctx.prec = max(
            28,
            max(a.adjusted(), b.adjusted()) - min(a.as_tuple().exponent, b.as_tuple().exponent) + 3,
        )
        return a - b


def economics(spec, n):
    c, v, b, reach = [
        decimal(spec[k]) for k in ("cost", "value", "budget_per_record", "maximum_reach")
    ]
    if reach > 1 or not isinstance(n, int) or n < 1:
        raise ContractError("Invalid cohort size or maximum reach")
    return c, v, product(b, n), int(product(reach, n).to_integral_value(rounding=ROUND_FLOOR))


def counts(n):
    return [0, *[int((Decimal(q) * n).to_integral_value(rounding=ROUND_CEILING)) for q in REACH]]


def feasible(spec, n, count):
    cost, _, budget, cap = economics(spec, n)
    return 0 <= count <= cap and product(cost, count) <= budget


def ledger(spec, n, count):
    c, v, budget, cap = economics(spec, n)
    if not feasible(spec, n, count):
        raise ContractError("Policy exceeds exact budget or actual reach cap")
    return {
        "hypothetical": True,
        "cost_per_assignment": str(c),
        "value_per_incremental_visit": str(v),
        "budget": str(budget),
        "spending": str(product(c, count)),
        "unspent_budget": str(difference(budget, product(c, count))),
        "maximum_assignments_by_reach": cap,
        "selected": count,
        "actual_reach": count / n,
    }


def choose(point, lower, support, spec, n, minimum_control_visits=30):
    """Only selection evidence enters here: (scenario,model,6-bin) arrays."""
    point, lower = np.asarray(point), np.asarray(lower)
    if point.shape != lower.shape or point.shape[1:] != (4, 6):
        raise ContractError("Invalid decision evidence layout")
    if not np.isfinite(point).all() or not np.isfinite(lower).all():
        raise ContractError("Nonfinite decision evidence")
    c, v, _, _ = economics(spec, n)
    ends = counts(n)
    result = {
        "model": None,
        "reach_index": 0,
        "objective": 0.0,
        "reason_codes": [],
        "candidates": {},
    }
    feasible_k = [k for k in range(1, 6) if feasible(spec, n, ends[k])]
    if not feasible_k:
        result["reason_codes"] = ["no_feasible_positive_reach"]
    elif v == 0:
        result["reason_codes"] = ["zero_value"]
    else:
        best_key = (0.0, Decimal(0), 0, 0)
        for mi, model in enumerate(MODELS):
            objective = 0.0
            passed = 0
            details = []
            reason = "selected"
            for k in range(1, 6):
                if k not in feasible_k:
                    break
                s = support[model][k - 1]
                dn = ends[k] - ends[k - 1]
                nets = float(v) * n * point[:, mi, k - 1] - float(product(c, dn))
                bounds = float(v) * n * lower[:, mi, k - 1] - float(product(c, dn))
                worst = float(bounds.min())
                if (
                    s["control_n"] == 0
                    or s["treatment_n"] == 0
                    or (s["control_visits"] < minimum_control_visits)
                ):
                    reason = "insufficient_selection_support"
                elif worst <= 0:
                    reason = (
                        "negative_estimated_net_benefit"
                        if nets.max() <= 0
                        else "assumption_sensitive"
                        if nets.min() <= 0
                        else "inconclusive_lower_bound"
                    )
                details.append(
                    {
                        "reach_index": k,
                        "marginal_assignments": dn,
                        "worst_lower_net_value": worst,
                        "worst_point_net_value": float(nets.min()),
                        "best_point_net_value": float(nets.max()),
                        "binding_scenario_index": int(np.argmin(bounds)),
                        "reason": reason,
                    }
                )
                if reason != "selected":
                    break
                objective += worst
                passed = k
            result["candidates"][model] = {
                "accepted_prefix": passed,
                "objective": objective,
                "stop_reason": reason,
                "tranches": details,
            }
            key = (objective, -product(c, ends[passed]), -ends[passed], -mi)
            if passed and key > best_key:
                best_key = key
                result.update(model=model, reach_index=passed, objective=objective)
        result["reason_codes"] = (
            ["selected"]
            if result["model"] is not None
            else sorted({row["stop_reason"] for row in result["candidates"].values()})
        )
    result["ledger"] = ledger(spec, n, ends[result["reach_index"]])
    return result


def apply(decision, spec, n):
    """Outcome-blind assessment application; only lower approved grid prefixes."""
    k = decision["reach_index"]
    ends = counts(n)
    while k and not feasible(spec, n, ends[k]):
        k -= 1
    return {
        "model": decision["model"] if k else None,
        "reach_index": k,
        "rounding_adjustment": k != decision["reach_index"],
        "ledger": ledger(spec, n, ends[k]),
    }


def id_hash(ids):
    return hashlib.sha256(np.asarray(ids, dtype="<i8").tobytes()).hexdigest()
