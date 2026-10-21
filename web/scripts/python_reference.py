"""Audit fixtures from approved public aggregates only; never an experiment.

Run from the repository's existing Python environment. All inputs are fixed
public snapshot fields and invented financial assumptions. Historical files are
read only; the sole output is an additive frontend test fixture.
"""

import json
import sys
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from app.dashboard_data import estimate, illustrate, load_data, paired  # noqa: E402


def main():
    data = load_data()
    values, pairs, budgets = [], [], []
    for method, e, uncertainty, interval in product(
        ("dr", "ipw"),
        (0.8, 0.825, 0.85, 0.875, 0.9),
        ("iid", "stratified"),
        ("simultaneous", "pointwise"),
    ):
        options = dict(method=method, propensity=e, uncertainty=uncertainty, interval=interval)
        scenario = [method, e, uncertainty, interval]
        for model, reach in [
            *product(("random", "response", "s_learner", "t_learner"), (10, 20, 30, 40, 50)),
            ("all", 100),
        ]:
            result = estimate(data, model, reach, **options)
            values.append([model, reach, *scenario, result.value, result.low, result.high])
            if model != "all":
                r = illustrate(data, model, reach, 100000, ".01", "1", "500", **options)
                budgets.append(
                    [
                        model,
                        reach,
                        100000,
                        ".01",
                        "1",
                        "500",
                        *scenario,
                        r.assignments,
                        str(r.incremental_visits),
                        str(r.spend),
                        str(r.net_value),
                        str(r.unspent_budget),
                        *map(str, r.scaled_benchmark_bounds),
                    ]
                )
        for reach in (10, 20, 30, 40, 50):
            result = paired(data, "t_learner", "s_learner", reach, **options)
            pairs.append([reach, *scenario, result.value, result.low, result.high])
    for model, reach, n, cost, value, cap in [
        ("none", 0, 11, "0", "0", "500"),
        ("random", 10, 11, ".01", "1", ".02"),
        ("s_learner", 20, 1000000000, "0", "1000000000000", "0"),
        ("t_learner", 50, 1000000000, ".01", "1000000000000", "10000000"),
    ]:
        r = illustrate(data, model, reach, n, cost, value, cap)
        budgets.append(
            [
                model,
                reach,
                n,
                cost,
                value,
                cap,
                "dr",
                0.85,
                "iid",
                "simultaneous",
                r.assignments,
                str(r.incremental_visits),
                str(r.spend),
                str(r.net_value),
                str(r.unspent_budget),
                *(
                    [str(v) for v in r.scaled_benchmark_bounds]
                    if r.scaled_benchmark_bounds
                    else [None, None]
                ),
            ]
        )
    output = {
        "snapshot_sha256": "358c331d72df76d0ca1e4fddd36c7c35be32b1a0b2dd0ae12949c5967ac46169",
        "estimates": values,
        "pairs": pairs,
        "budgets": budgets,
    }
    target = ROOT / "web/tests/python-scientific-reference.json"
    target.write_text(json.dumps(output, indent=2) + "\n")
    print(
        f"Public-only audit: {len(values)} estimates, {len(pairs)} paired intervals, "
        f"{len(budgets)} budget references. No experiments or private data."
    )


if __name__ == "__main__":
    main()
