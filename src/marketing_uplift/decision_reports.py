"""Aggregate-only hypothetical economics and development stability publication."""

from collections import Counter
from pathlib import Path

import numpy as np

from marketing_uplift.data_contract import atomic_json
from marketing_uplift.decision_engine import counts, ledger

CAVEATS = """All monetary inputs are hypothetical currency units, not observed Criteo costs,
revenue, ROI or savings. Values below are assumption-dependent released-development
benchmark estimates, not proven causal or financial improvements. Propensities are
assumptions; DR does not repair unknown experiment assignment, privacy selection or
unverified identification. Gaussian intervals are nominal IID working-model,
conditional on fitted models and fixed role-specific policies, excluding refitting,
unknown dependence and outcome-stratification uncertainty. Pointwise intervals differ
from the one-sided simultaneous 300-coordinate marginal decision bounds. Splits overlap;
mean/range and decision frequencies are descriptive, not independent replications.
Auxiliary assessment roles reduce direct selection reuse but are not fresh confirmatory
data: development outcomes informed prior phases. No deployment policy is selected or
locked, and the final holdout remains sealed.
"""


def valued(policy, financial, n):
    v = float(financial["value_per_incremental_visit"])
    spending = float(financial["spending"])
    return {
        "incremental_visits": policy["estimate"] * n,
        "incremental_visits_per_1000": policy["per_1000"],
        "pointwise_visits_interval": [x * n for x in policy["pointwise_interval"]],
        "hypothetical_net_value": v * policy["estimate"] * n - spending,
        "pointwise_net_interval": [v * x * n - spending for x in policy["pointwise_interval"]],
    }


def render(report, tracking_directory=None):
    aggregate = []
    lines = [
        "# Phase 8 — development-only budget and abstention simulation",
        "",
        CAVEATS,
        "## Frozen design",
        "",
        f"Protocol SHA-256: `{report['protocol_sha256']}`.",
        "Each outer validation has 1,188,265 selection and 1,188,266 assessment records.",
        "Recommendations and assessment assignment hashes persisted before "
        "assessment outcome queries.",
        "Eight predeclared economic configurations use exact budget density scaling B=b*N.",
        "The objective sums worst-scenario simultaneous lower marginal net "
        "values, and stops at the first failed tranche.",
        "Selection support requires both arms and 30 control visits per tranche; "
        "assessment support is diagnostic only.",
        "No model retraining, recalibration, split regeneration, holdout outcome "
        "analysis or lockfile change.",
        "",
        "## Hypothetical scenarios",
        "",
        "| Scenario | Assignment cost | Visit value | Budget/eligible record | Max reach |",
        "|---|---:|---:|---:|---:|",
    ]
    for s in report["settings"]["economics"]:
        lines.append(
            f"| {s['name']} | {s['cost']} | {s['value']} | {s['budget_per_record']} | "
            f"{s['maximum_reach']} |"
        )
    lines += [
        "",
        "## Provisional selection and assessment decisions",
        "",
        "| Split | Scenario | Model | Selection reach | Assessment reach | "
        "Assignments | Spending | Unspent | Reasons |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for split in report["splits"]:
        for economic in report["settings"]["economics"]:
            name = economic["name"]
            decision, app = split["decisions"][name], split["applications"][name]
            financial_ledger = app["ledger"]
            lines.append(
                f"| {split['seed']} | {name} | {app['model'] or 'none'} | "
                f"{decision['ledger']['actual_reach']:.6%} | "
                f"{financial_ledger['actual_reach']:.6%} | "
                f"{financial_ledger['selected']:,} | {financial_ledger['spending']} | "
                f"{financial_ledger['unspent_budget']} | "
                f"{', '.join(decision['reason_codes'])} |"
            )
            n = split["assessment"]["rows"]
            references = app["comparisons"]["equal_budget_cap_policy_keys"]
            all_policies = []
            for key in references:
                model, k = key.split(":")
                k = int(k)
                count = n if k == 6 else counts(n)[k]
                financial = ledger(economic, n, count)
                estimates = split["assessment"]["policies"][key]
                all_policies.append(
                    {
                        "policy": key,
                        "ledger": financial,
                        "scenarios": [
                            dict(method=m, propensity_assumption=e, **valued(row, financial, n))
                            for (m, e), row in zip(split["scenario_keys"], estimates, strict=True)
                        ],
                    }
                )
            chosenkey = f"{app['model']}:{app['reach_index']}" if app["model"] else "none:0"
            chosen = split["assessment"]["policies"][chosenkey]
            aggregate.append(
                {
                    "seed": split["seed"],
                    "economic_scenario": name,
                    "hypothetical": True,
                    "decision_reasons": decision["reason_codes"],
                    "application": {k: v for k, v in app.items() if k != "comparisons"},
                    "engine_estimates": [
                        dict(method=m, propensity_assumption=e, **valued(row, financial_ledger, n))
                        for (m, e), row in zip(split["scenario_keys"], chosen, strict=True)
                    ],
                    "equal_budget_cap": all_policies,
                    "equal_actual_spending": app["comparisons"]["equal_actual_spending"],
                }
            )
    lines += [
        "",
        "## Assessment at reference assumed e=.85",
        "",
        "Intervals below are paired-draw pointwise 95% working-model intervals, "
        "not the decision family bounds.",
        "",
        "| Split | Scenario | Evaluator | Incremental visits/1,000 | 95% "
        "interval/1,000 | Hypothetical net value |",
        "|---|---|---|---:|---|---:|",
    ]
    for row in aggregate:
        for estimate in row["engine_estimates"]:
            if estimate["propensity_assumption"] == 0.85:
                n = next(
                    s["assessment"]["rows"] for s in report["splits"] if s["seed"] == row["seed"]
                )
                ci = [x / n * 1000 for x in estimate["pointwise_visits_interval"]]
                lines.append(
                    f"| {row['seed']} | {row['economic_scenario']} | {estimate['method']} | "
                    f"{estimate['incremental_visits_per_1000']:.4f} | [{ci[0]:.4f}, "
                    f"{ci[1]:.4f}] | {estimate['hypothetical_net_value']:.4f} |"
                )
    lines += ["", "## Stability and comparisons", ""]
    for economic in report["settings"]["economics"]:
        name = economic["name"]
        apps = [s["applications"][name] for s in report["splits"]]
        reaches = [a["ledger"]["actual_reach"] for a in apps]
        abstentions = sum(a["model"] is None for a in apps)
        orders = dict(Counter(a["model"] or "none" for a in apps))
        lines.append(
            f"- {name}: abstention {abstentions}/{len(apps)}; assessment reach mean "
            f"{np.mean(reaches):.6%}, range [{min(reaches):.6%}, {max(reaches):.6%}]; "
            f"provisional model counts {orders}."
        )
    lines += [
        "",
        "Same-cap policies can spend different amounts. All-targeting appears "
        "only when feasible; it is not reach-matched.",
        "The JSON economics report contains all feasible fixed-reach gains, "
        "hypothetical net values and intervals for all 15 evaluator/propensity "
        "combinations.",
        "Matched-spending contrasts use exactly the engine's actual count; "
        "zero-spending recommendations make all matched comparators no "
        "targeting.",
        "No ranking AUUC/Qini definition changed; those historical areas are not "
        "a spending objective.",
        "",
        "## Resources and preservation",
        "",
        f"All {len(report['protected_before'])} protected file/tree entries match before/after.",
        f"Split evaluation elapsed seconds: "
        f"{[round(s['elapsed_seconds'], 2) for s in report['splits']]}; total "
        f"{sum(s['elapsed_seconds'] for s in report['splits']):.2f} (excludes "
        f"protection/gate/publication overhead).",
        f"Maximum process RSS: "
        f"{max(s['peak_rss_kib'] for s in report['splits']) / 1024**2:.3f} GiB.",
        "Memory cgroup snapshots, disk availability and individual numerical "
        "diagnostics are in phase_8_metrics.json.",
        "Cloud-local models/data/memberships/MLflow are not guaranteed to "
        "persist across new tasks. Preserve matching artifacts; deliberately "
        "restore and verify missing prerequisites.",
        "",
        "Existing calibration and exact-vector overlap diagnostics remain in "
        "phase_7_comparison.md; vector matches are not customer identities or "
        "validated clusters.",
    ]
    sensitivity = [
        "# Phase 8 — propensity, nuisance and marginal evidence",
        "",
        CAVEATS,
        "The next table reports selection first-tranche gain/1,000 ranges across "
        "all 15 assumptions, and the worst simultaneous lower bound.",
        "No probabilities are assigned to scenarios. IPW, primary DR and "
        "saved-S-nuisance DR remain separate.",
        "",
        "| Split | Ranking | First-tranche point range/1,000 | Worst lower/1,000 |",
        "|---|---|---|---:|",
    ]
    for split in report["splits"]:
        point = np.array(split["selection"]["marginal_point"])
        lower = np.array(split["selection"]["marginal_lower"])
        for mi, model in enumerate(("random", "response", "s_learner", "t_learner")):
            values = point[:, mi, 0] * 1000
            sensitivity.append(
                f"| {split['seed']} | {model} | [{values.min():.4f}, {values.max():.4f}] "
                f"| {lower[:, mi, 0].min() * 1000:.4f} |"
            )
    sensitivity += [
        "",
        "## Evaluator sensitivity at 10% reach",
        "",
        "Selection gain ranges across the five assumed propensities, per 1,000 "
        "eligible records. These are stress ranges, not confidence intervals.",
        "",
        "| Split | Ranking | Evaluator | Point range/1,000 |",
        "|---|---|---|---|",
    ]
    for split in report["splits"]:
        point = np.array(split["selection"]["marginal_point"])
        for mi, model in enumerate(("random", "response", "s_learner", "t_learner")):
            for j, method in enumerate(("ipw", "dr", "s_dr")):
                values = point[j * 5 : (j + 1) * 5, mi, 0] * 1000
                sensitivity.append(
                    f"| {split['seed']} | {model} | {method} | [{values.min():.4f}, "
                    f"{values.max():.4f}] |"
                )
    sensitivity += ["", "## Support and limitations", ""]
    for split in report["splits"]:
        for role in ("selection", "assessment"):
            rows = [r for model in split[role]["support"].values() for r in model[:5]]
            minimum = min(r["control_visits"] for r in rows)
            warnings = sum(
                r["control_visits"] < 30 or not r["control_n"] or not r["treatment_n"] for r in rows
            )
            sensitivity.append(
                f"- Split {split['seed']} {role}: minimum tranche control visits "
                f"{minimum}; inadequate-support tranches {warnings}/20. Assessment "
                f"warnings do not change decisions."
            )
    sensitivity += [
        "",
        "Worst-case aggregation can abstain because one assumed propensity makes "
        "even the first tranche negative; increasing hypothetical visit value "
        "cannot repair a negative visit-gain bound.",
        "Any zero recommendation concerns the declared grid and stress "
        "objective. It does not prove all smaller campaigns, all models or the "
        "real population have nonpositive effects.",
        "If identification or dependence assumptions cannot be justified, use "
        "these outputs as scenario analysis and withhold an operational spending "
        "recommendation.",
    ]
    atomic_json(
        Path("reports/phase_8_economics.json"),
        {
            "hypothetical": True,
            "protocol_sha256": report["protocol_sha256"],
            "limitations": CAVEATS,
            "comparisons": aggregate,
        },
    )
    Path("reports/phase_8_decisions.md").write_text("\n".join(lines) + "\n")
    Path("reports/phase_8_sensitivity.md").write_text("\n".join(sensitivity) + "\n")
    if tracking_directory:
        import mlflow

        mlflow.set_tracking_uri(Path(tracking_directory).resolve().as_uri())
        # Publish aggregate reports in a NEW run; completed per-split runs remain immutable.
        mlflow.set_experiment("marketing-uplift-phase8-publication")
        with mlflow.start_run(run_name=f"phase8-reports-{report['protocol_sha256'][:12]}"):
            mlflow.log_param("protocol_sha256", report["protocol_sha256"])
            for name in (
                "phase_8_economics.json",
                "phase_8_decisions.md",
                "phase_8_sensitivity.md",
            ):
                mlflow.log_artifact(str(Path("reports") / name))
