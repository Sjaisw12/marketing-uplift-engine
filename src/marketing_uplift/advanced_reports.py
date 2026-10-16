# ruff: noqa: E501
# Report prose and generated Markdown tables retain natural width.
"""Aggregate-only Phase 7 reports; no model fitting or record access."""

import platform
from pathlib import Path

import duckdb
import lightgbm
import mlflow
import numpy as np
import sklearn

from marketing_uplift.robust_metrics import MODELS


def render(report, tracking_directory="mlruns"):
    splits = report["splits"]
    lines = [
        "# Phase 7 — advanced uplift and robust evaluation",
        "",
        "Measured on five frozen development validation partitions. The final holdout remains sealed.",
        "All propensity values are assumptions; neither IPW nor DR establishes causal superiority.",
        "DR requires causal identification plus either correct assignment propensity or both outcome regressions. It does not remove selection bias, hidden experiments, dependence or development-stratification limitations.",
        "",
        "## Methods and interpretation",
        "",
        "The T-learner reuses each Phase 6 treated-response model and trains one control-arm LightGBM with the same frozen recipe. Both arms receive exactly f0–f11. Scores are m1−m0. Existing response/S/random predictions and all historical results are preserved.",
        "The common DR evaluator averages three training-only fold models per arm. Inner held-fold factual predictions support OOF diagnostics; outer-validation outcomes never enter fitting. All policies share the same evaluator. Saved S-learner m0/m1 supply a separately labeled nuisance sensitivity, not a selected evaluator.",
        "See [the frozen protocol](../docs/PHASE7_PROTOCOL.md) for formulas, seeds, fold definitions, source alignment, full-prefix IPW AUUC/Qini and uncertainty conventions.",
        "All value/gain/contrast numbers below are per 1,000 eligible validation records. Means and ranges across overlapping splits describe stability; they are not independent-replication estimates.",
        "",
        "## Reference e=.85: descriptive mean gain over no targeting",
        "",
        "| Reach | Evaluator | Random | Response | S | T |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for k, q in enumerate((0.1, 0.2, 0.3, 0.4, 0.5)):
        for method in ("ipw", "dr"):
            vals = [
                np.mean(
                    [
                        1000
                        * s["evaluation"]["estimates"][method]["0.85"]["models"][name]["policies"][
                            k
                        ]["gain_over_none"]["estimate"]
                        for s in splits
                    ]
                )
                for name in MODELS
            ]
            lines.append(
                f"| {q:.0%} | {method.upper()} | " + " | ".join(f"{v:.4f}" for v in vals) + " |"
            )

    lines += [
        "",
        "## Per-split reference gains and anchors",
        "",
        "| Seed | Method | Reach | Random | Response | S | T | None/all values |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for result in splits:
        for method in ("ipw", "dr"):
            entry = result["evaluation"]["estimates"][method]["0.85"]
            anchors = "/".join(
                f"{entry['anchors'][a]['estimate'] * 1000:.4f}" for a in ("none", "all")
            )
            for k, q in enumerate((0.1, 0.2, 0.3, 0.4, 0.5)):
                vals = [
                    entry["models"][name]["policies"][k]["gain_over_none"]["estimate"] * 1000
                    for name in MODELS
                ]
                lines.append(
                    f"| {result['seed']} | {method} | {q:.0%} | "
                    + " | ".join(f"{v:.4f}" for v in vals)
                    + f" | {anchors} |"
                )
    lines += [
        "",
        "## Paired T-minus-S reference contrasts",
        "",
        "2,000 correlated Gaussian-multiplier replicates use the full joint covariance recovered from continuous within-cell moments. This is not an exact ordinary row bootstrap. Intervals are nominal IID working-model intervals, conditional on fitted models, nuisance predictions, fixed rankings and targeting memberships. No refitting, reranking, cluster correction or stratification correction is included.",
        "Pointwise intervals use multiplier quantiles. Simultaneous bands cover the predeclared ten comparisons (five reaches × IPW/DR) within each split at e=.85. They do not adjust across splits, other policy contrasts, propensity scenarios or nuisance alternatives.",
        "",
        "| Seed | Method | Reach | Difference | Pointwise 95% | Simultaneous 95% |",
        "|---|---|---|---:|---:|---:|",
    ]
    for s in splits:
        for method in ("ipw", "dr"):
            for p in s["evaluation"]["estimates"][method]["0.85"]["models"]["t_learner"][
                "policies"
            ]:
                c = p["paired"]["s_learner"]
                a, b = np.array(c["pointwise_interval"]) * 1000
                lo, hi = np.array(c["simultaneous_interval"]) * 1000
                lines.append(
                    f"| {s['seed']} | {method} | {p['reach']:.0%} | {c['estimate'] * 1000:.4f} | [{a:.4f}, {b:.4f}] | [{lo:.4f}, {hi:.4f}] |"
                )
    lines += [
        "",
        "## Propensity and nuisance sensitivity: mean T-minus-S",
        "",
        "Each scenario is separate. The range is illustrative, not a validated bound on propensity or bias. S-nuisance DR has point estimates only and is not selected based on favorable performance.",
        "",
        "| e | Reach | IPW | Shared cross-fit DR | S-nuisance DR |",
        "|---|---|---:|---:|---:|",
    ]
    for e in (0.8, 0.825, 0.85, 0.875, 0.9):
        for k, q in enumerate((0.1, 0.2, 0.3, 0.4, 0.5)):
            vals = [
                np.mean(
                    [
                        1000
                        * s["evaluation"]["estimates"][m][str(e)]["models"]["t_learner"][
                            "policies"
                        ][k]["paired"]["s_learner"]["estimate"]
                        for s in splits
                    ]
                )
                for m in ("ipw", "dr")
            ]
            vals.append(
                np.mean(
                    [
                        1000
                        * (
                            s["evaluation"]["s_nuisance_sensitivity"][str(e)]["models"][
                                "t_learner"
                            ][k]
                            - s["evaluation"]["s_nuisance_sensitivity"][str(e)]["models"][
                                "s_learner"
                            ][k]
                        )
                        for s in splits
                    ]
                )
            )
            lines.append(f"| {e} | {q:.0%} | " + " | ".join(f"{v:.4f}" for v in vals) + " |")
    lines += [
        "",
        "## Support and calibration",
        "",
        "Each validation partition contains 2,020,052 treated records/98,060 visits and 356,479 controls/13,618 visits. JSON contains arm/event counts for every policy at cumulative and disjoint reaches, absent-arm handling and control-visits<30 warnings.",
        "Calibration bins are fixed before performance examination. Diagnostics below concern factual outcome probabilities, not individual-effect accuracy. Full fixed-bin reliability counts, log loss, Brier, AUC and AP are in JSON. No calibration transformation was fitted.",
        "",
        "| Seed | Predictor/population | Log loss | Brier | AUC | AP |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for s in splits:
        for name, cal in s["diagnostics"].items():
            m = cal["metrics"]
            lines.append(
                f"| {s['seed']} | {name} | {m['log_loss']:.6f} | {m['brier']:.6f} | {m['roc_auc']:.6f} | {m['average_precision']:.6f} |"
            )

    lines += [
        "",
        "### Control event support across splits",
        "",
        "Minima are descriptive across the five overlapping splits. Flags use the predeclared <30 control-visits threshold in disjoint bands.",
        "",
        "| Reach | Ranking | Minimum cumulative control n | Minimum cumulative control visits | Minimum band control visits | Flagged bands /5 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for k, q in enumerate((0.1, 0.2, 0.3, 0.4, 0.5)):
        for name in MODELS:
            cumulative = [s["evaluation"]["support"][name]["cumulative"][k] for s in splits]
            bands = [s["evaluation"]["support"][name]["band"][k] for s in splits]
            lines.append(
                f"| {q:.0%} | {name} | {min(x['control_n'] for x in cumulative)} | {min(x['control_visits'] for x in cumulative)} | {min(x['control_visits'] for x in bands)} | {sum(x['low_control_visits'] for x in bands)} |"
            )
    lines += [
        "",
        "### First-split control calibration illustration",
        "",
        "The full bin tables for every split and arm are retained in JSON; bin boundaries were frozen before evaluation.",
        "",
        "| Predictor | Probability bin | Records | Observed visit rate | Mean prediction |",
        "|---|---|---:|---:|---:|",
    ]
    for name in ("t_arm_0", "dr_arm_0", "s_arm_0"):
        for row in splits[0]["diagnostics"][name]["bins"]:
            if row["records"]:
                lines.append(
                    f"| {name} | {row['lower']}–{row['upper']} | {row['records']} | {row['visits'] / row['records']:.5f} | {row['mean_prediction']:.5f} |"
                )
    lines += [
        "",
        "## Repeated vectors and dependence",
        "",
        "Exact equality of all twelve features defines a vector, not a customer. No deduplication or membership changes were made. Overlap may reflect distinct anonymous records and cannot justify an entity-cluster correction.",
        "",
        "| Seed | Shared distinct vectors | Validation rows matching training | Share |",
        "|---|---:|---:|---:|",
    ]
    for s in splits:
        v = s["vector_overlap"]
        n = v["validation_rows_matching_training"]
        lines.append(
            f"| {s['seed']} | {v['shared_vectors']} | {n} | {n / s['validation_rows']:.4%} |"
        )
    lines += [
        "",
        "## Resources and reproducibility",
        "",
        f"Protocol SHA-256: `{report['protocol_sha256']}`.",
        "All five auxiliary fold files were hashed before first execution; fit manifests hash models/predictions before evaluation. Phase 6 models, predictions, MLflow runs, frozen protocol, reports, lockfile and memberships remain unchanged.",
        "Sequential two-thread fits, one-thread bounded DuckDB, batched predictions and streaming moments avoid a rows × 2,000 replicate matrix. Peak RSS is a process high-water mark, potentially including earlier splits.",
        "",
        "| Seed | New fitted models | Elapsed seconds | Peak process RSS GiB | Joint cells | MLflow run |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for s in splits:
        lines.append(
            f"| {s['seed']} | {len(s['models'])} | {s['elapsed_seconds']:.2f} | {s['peak_rss_kib'] / 1024**2:.3f} | {s['evaluation']['joint_cells']} | `{s['mlflow_run_id']}` |"
        )
    lines += [
        "",
        "Models, predictions, OOF records, nuisance folds and MLflow remain ignored by Git. Cloud local artifacts are not guaranteed to persist into another task; preserve private artifacts separately if needed. Reuse matching existing inputs rather than recreating them.",
        "The five development splits overlap and already informed earlier development; these are further development comparisons, not a fresh confirmatory test. Calibration cannot validate exchangeability or selection assumptions. Unknown individual/experiment dependence remains unresolved.",
        "No final model/reach, causal superiority, advertiser-wide effect, ROI, abstention decision or holdout result is claimed.",
        "",
    ]
    contrast_means = {
        method: [
            float(
                np.mean(
                    [
                        s["evaluation"]["estimates"][method]["0.85"]["models"]["t_learner"][
                            "policies"
                        ][k]["paired"]["s_learner"]["estimate"]
                        * 1000
                        for s in splits
                    ]
                )
            )
            for k in range(5)
        ]
        for method in ("ipw", "dr")
    }
    all_bands = [
        p["paired"]["s_learner"]["simultaneous_interval"]
        for s in splits
        for method in ("ipw", "dr")
        for p in s["evaluation"]["estimates"][method]["0.85"]["models"]["t_learner"]["policies"]
    ]
    lines += [
        "",
        "## Measured interpretation",
        "",
        f"At reference e=.85 and 10% reach, mean T-minus-S is {contrast_means['ipw'][0]:.4f} per1,000 with IPW and {contrast_means['dr'][0]:.4f} with the common DR evaluator.",
        "The T-learner's mean contrast is negative at every reference reach under both evaluators. Separate arm models do not guarantee better uplift ranking; the control arm is smaller and subtracting two response predictions can amplify estimation error.",
        f"Across the {len(all_bands)} within-split simultaneous bands, {sum(b[0] > 0 for b in all_bands)} lie wholly above zero and {sum(b[1] < 0 for b in all_bands)} wholly below zero; the others contain zero. These are descriptive counts over overlapping splits, not independent confirmations or a pooled test.",
        "At 40% and 50% reference reach, the mean response-versus-S order differs between IPW and DR. Evaluator agreement cannot be presumed, and no favorable metric is selected.",
        "All disjoint reach bands have more than 30 control visits (minimum123 in the measured runs); no low-control-event warning is triggered. These counts do not remove unknown dependence or privacy-selection limitations.",
        "Control factual discrimination is strong (mean T-arm ROC AUC about .9475), but outcome discrimination and calibration do not validate individual treatment effects or causal identification.",
        "All reference T-versus-S means remain negative with the alternative S nuisance. This limited nuisance agreement does not establish correctness of either evaluator. The full propensity/nuisance grid remains assumption-dependent.",
        "",
    ]
    Path("reports/phase_7_comparison.md").write_text("\n".join(lines))
    stability = [
        "# Phase 7 — descriptive stability",
        "",
        "Five splits overlap. No pooled independent-replication confidence interval or final winner is computed.",
        "",
        "| Reach | Method | Point-estimate order by split | Mean T−S [min,max] /1,000 | Positive simultaneous bands |",
        "|---|---|---|---:|---:|",
    ]
    for k, q in enumerate((0.1, 0.2, 0.3, 0.4, 0.5)):
        for method in ("ipw", "dr"):
            orders = []
            vals = []
            positive = 0
            for s in splits:
                models = s["evaluation"]["estimates"][method]["0.85"]["models"]
                order = sorted(
                    MODELS,
                    key=lambda m: models[m]["policies"][k]["value"]["estimate"],
                    reverse=True,
                )
                orders.append(">".join(order))
                c = models["t_learner"]["policies"][k]["paired"]["s_learner"]
                vals.append(c["estimate"] * 1000)
                positive += c["simultaneous_interval"][0] > 0
            stability.append(
                f"| {q:.0%} | {method} | "
                + "; ".join(orders)
                + f" | {np.mean(vals):.4f} [{min(vals):.4f}, {max(vals):.4f}] | {positive}/5 |"
            )
    stability += [
        "",
        "A band containing zero supports no reliable difference detected under that working model. A positive band does not establish causal superiority. Propensity/nuisance sensitivity and unknown dependence can matter more than conditional sampling precision.",
        "",
    ]
    Path("reports/phase_7_stability.md").write_text("\n".join(stability))

    mlflow.set_tracking_uri(Path(tracking_directory).resolve().as_uri())
    for result in splits:
        with mlflow.start_run(run_id=result["mlflow_run_id"]):
            mlflow.log_dict(
                {
                    "python": platform.python_version(),
                    "numpy": np.__version__,
                    "lightgbm": lightgbm.__version__,
                    "sklearn": sklearn.__version__,
                    "duckdb": duckdb.__version__,
                    "mlflow": mlflow.__version__,
                    "platform": platform.platform(),
                },
                "runtime.json",
            )
            for method, scenarios in result["evaluation"]["estimates"].items():
                for e, scenario in scenarios.items():
                    for name, entry in scenario["models"].items():
                        mlflow.log_metrics(
                            {
                                f"{method}_e{e}_{name}_gain{int(row['reach'] * 100)}": row[
                                    "gain_over_none"
                                ]["estimate"]
                                for row in entry["policies"]
                            }
                        )
            mlflow.log_artifact("reports/phase_7_comparison.md", "aggregate_reports")
            mlflow.log_artifact("reports/phase_7_stability.md", "aggregate_reports")
            mlflow.log_artifact("reports/phase_7_numerical_reference.json", "aggregate_reports")
