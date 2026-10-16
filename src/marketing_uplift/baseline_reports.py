# ruff: noqa: E501
# Markdown prose and generated table rows retain their natural width.
"""Aggregate reporting; never opens row-level inputs or the sealed holdout."""

import platform
from pathlib import Path

import duckdb
import lightgbm
import mlflow
import numpy as np
import sklearn

from marketing_uplift.policy_metrics import MODELS, REACH


def render(report, tracking_directory="mlruns"):
    splits = report["splits"]
    lines = [
        "# Phase 6 — development machine-learning baselines",
        "",
        "All results below are measured on the five frozen development validation sets.",
        "Each contains 2,376,531 rows; overlapping splits are stability checks, not independent experiments.",
        "The sealed 2,096,939-row final holdout was excluded. All 25 protected input files remained identical.",
        "",
        "## Interpretation and frozen methods",
        "",
        "These are assumption-dependent IPW scenario functionals, not proven causal improvements.",
        "The causal target would be V_causal(pi)=E[Y(pi(X))] in the released population, with gain",
        "E[pi(X)*(Y(1)-Y(0))] over assigning nobody. The observable scenario functional is",
        "Phi_e(pi)=E[pi*T*Y/e+(1-pi)*(1-T)*Y/(1-e)]; tables estimate this by sample means.",
        "Differences of Phi_e are identifiable released-sample functionals for each fixed e; their",
        "interpretation as differences of causal policy values requires the assumptions below.",
        "The reference constant e=0.85 is not a verified individual assignment probability.",
        "Non-uniform privacy subsampling, pooled experiments and unknown assignment probabilities can bias",
        "all constant-propensity scenarios. Sensitivity does not establish identification.",
        "Causal policy values require consistency, no interference, positivity, exchangeability and correct",
        "assignment probabilities in the released population. No exposure conditioning or ROI inference is used.",
        "",
        "Treated-response LightGBM predicts who visits under assignment; it can prioritize people who would",
        "visit anyway. The S-learner ranks m(X,1)-m(X,0), a model contrast rather than an observed individual effect.",
        "Both use f0–f11 only as user predictors. The S-learner intervention is supplied separately.",
        "Histogram boosting handles nonlinear patterns in the anonymized numeric features without scaling.",
        "The fixed 63-bin, 31-leaf, minimum-1,000-record recipe limits memory and leaf complexity; 200 rounds",
        "avoid validation-driven early stopping. Unweighted binary loss preserves probability-scale targets.",
        "A linear probability/logistic baseline would be cheaper but less flexible; additional estimators",
        "and tuning require later approval. Calibration and individual-effect accuracy are not established",
        "by high visit-prediction AUC. S-learner regularization can suppress treatment interactions.",
        "The complete pre-performance recipes, ranking rules, formulas and integration convention are in",
        "[PHASE6_PROTOCOL.md](../docs/PHASE6_PROTOCOL.md). No hyperparameter or reach selection occurred.",
        "",
        "Areas use all n+1 prefixes and trapezoidal integration, not the five reporting reaches.",
        "IPW Qini is unnormalized area above the random diagonal. Negative estimates remain negative.",
        "Values and gains below are per 1,000 eligible validation rows, not per selected user.",
        "",
        "## Reference scenario: five-split descriptive means and ranges",
        "",
        "| Reach | Ranking | Value mean [min, max] /1,000 | Gain over none mean /1,000 |",
        "|---|---|---:|---:|",
    ]
    for k, q in enumerate(REACH):
        for name in MODELS:
            rows = [
                s["evaluation"]["scenarios"]["0.85"]["models"][name]["policies"][k] for s in splits
            ]
            vals = [r["value_per_1000"] for r in rows]
            gains = [1000 * r["gain_over_none"] for r in rows]
            lines.append(
                f"| {q:.0%} | {name} | {np.mean(vals):.4f} [{min(vals):.4f}, {max(vals):.4f}] | {np.mean(gains):.4f} |"
            )
    lines += [
        "",
        "## Per-split support, anchors and diagnostics",
        "",
        "| Seed | Treated / control validation | None / all value per 1,000 | Response AUC / AP | S factual AUC / AP |",
        "|---|---:|---:|---:|---:|",
    ]
    for s in splits:
        a = s["evaluation"]["scenarios"]["0.85"]["anchors"]
        r, u = s["predictive"]["response"], s["predictive"]["s_learner"]
        lines.append(
            f"| {s['seed']} | {s['validation_treatment_n']} / {s['validation_control_n']} | {1000 * a['none']:.4f} / {1000 * a['all']:.4f} | {r['roc_auc']:.4f} / {r['average_precision']:.4f} | {u['roc_auc']:.4f} / {u['average_precision']:.4f} |"
        )
    lines += [
        "",
        "The validation sets each contain 98,060 treated visits and 13,618 control visits,",
        "with 1,921,992 treated non-visits and 342,861 control non-visits.",
        "Predictive diagnostics use different populations: response on treated validation; S factual on all.",
        "AUC/AP do not validate causal uplift ranking. JSON also includes log loss and Brier score.",
        "",
        "## Paired uncertainty: S minus response, reference scenario",
        "",
        "2,000 paired IID bootstrap replicates per split, compressed into joint ranking-bin × T × Y cells.",
        "Pointwise percentile intervals and simultaneous max-t bands are conditional on fitted models and",
        "fixed original policy memberships. Simultaneous coverage applies only to five reaches within one split",
        "at the reference propensity, not across splits/scenarios. This does not capture refitting, cutoff estimation,",
        "unknown clustering or outcome-stratified sampling uncertainty. Nominal working-model coverage only.",
        "",
        "| Seed | Reach | Difference /1,000 | Pointwise 95% | Simultaneous 95% |",
        "|---|---|---:|---:|---:|",
    ]
    for s in splits:
        a = s["evaluation"]["scenarios"]["0.85"]
        c = a["paired_contrasts"]["s_learner_minus_response"]
        for k, q in enumerate(REACH):
            p, b = (
                np.array(c["pointwise_interval"][k]) * 1000,
                np.array(a["s_minus_response_simultaneous_bands"][k]) * 1000,
            )
            lines.append(
                f"| {s['seed']} | {q:.0%} | {c['difference'][k] * 1000:.4f} | [{p[0]:.4f}, {p[1]:.4f}] | [{b[0]:.4f}, {b[1]:.4f}] |"
            )
    lines += [
        "",
        "All model-versus-random and S-versus-response pointwise paired contrasts, value/gain intervals,",
        "selected-arm event counts, descriptive selected-arm rate differences and low-support flags are in JSON.",
        "",
        "## Propensity sensitivity: mean gain over none /1,000",
        "",
        "Scenarios remain separate; changing e can change policy order and does not correct unknown heterogeneity.",
        "This illustrative scenario range is not a validated bound on assignment probabilities or selection bias.",
        "",
        "| e assumption | Reach | Random | Response | S-learner |",
        "|---|---|---:|---:|---:|",
    ]
    for e in [0.8, 0.825, 0.85, 0.875, 0.9]:
        for k, q in enumerate(REACH):
            means = [
                np.mean(
                    [
                        1000
                        * s["evaluation"]["scenarios"][str(e)]["models"][name]["policies"][k][
                            "gain_over_none"
                        ]
                        for s in splits
                    ]
                )
                for name in MODELS
            ]
            lines.append(f"| {e} | {q:.0%} | " + " | ".join(f"{v:.4f}" for v in means) + " |")
    lines += [
        "",
        "## Reproducibility and resources",
        "",
        f"Protocol SHA-256: `{report['protocol_sha256']}`.",
        "Source, registry, all memberships, code/protocol hashes, model/prediction hashes and local MLflow run IDs",
        "are recorded in JSON. Sequential execution used two training threads and bounded DuckDB extraction.",
        "Raw data, model files, predictions, caches and local MLflow are ignored by Git.",
        "",
        "| Seed | Elapsed seconds | Cumulative process peak RSS GiB | MLflow run |",
        "|---|---:|---:|---|",
    ]
    for s in splits:
        lines.append(
            f"| {s['seed']} | {s['elapsed_seconds']:.1f} | {s['peak_process_rss_kib'] / 1024**2:.3f} | `{s['mlflow_run_id']}` |"
        )
    lines += [
        "",
        "RSS is a process high-water mark, including earlier splits in the same process; it is not a per-model allocation.",
        "Cloud local files are not guaranteed across new tasks. Restore raw archive with checksum verification,",
        "validate/ingest and reconstruct only missing memberships against the committed registry when needed.",
        "Preserve existing files when present. Private model/prediction/MLflow artifacts require a separate local backup",
        "if future environments must reuse fitted models; Git contains only code and aggregate evidence.",
        "No final winner, optimal reach, business effect or final holdout performance is claimed.",
        "",
    ]
    means = {
        e: float(
            np.mean(
                [
                    s["evaluation"]["scenarios"][str(e)]["paired_contrasts"][
                        "s_learner_minus_response"
                    ]["difference"][0]
                    * 1000
                    for s in splits
                ]
            )
        )
        for e in (0.8, 0.825, 0.85, 0.875, 0.9)
    }
    counts = [
        sum(
            s["evaluation"]["scenarios"]["0.85"]["s_minus_response_simultaneous_bands"][k][0] > 0
            for s in splits
        )
        for k in range(5)
    ]
    lines += [
        "## Measured findings and their limits",
        "",
        f"At 10% reach, the mean S-minus-response contrast is {means[0.85]:.4f} per 1,000 under e=.85.",
        f"The same contrast is {means[0.8]:.4f} under e=.80 and {means[0.9]:.4f} under e=.90.",
        "Its sign reverses across the predeclared scenarios, so causal superiority is not established.",
        f"Reference-scenario simultaneous bands exclude zero on the positive side in {counts[0]}/5",
        f"splits at 10% reach and {counts[1]}/5 at 20%; none do at 30%, 40% or 50%.",
        "Those counts describe overlapping splits, not independent corroborations or a pooled test.",
        "Higher-reach paired uncertainty supports no clear S-versus-response preference under the working model.",
        "The random policy is one frozen realization; bootstrap uncertainty does not resample its seed.",
        "Model refitting uncertainty and probability calibration remain unverified. Platform/library changes",
        "can change fitted artifacts; bitwise reproducibility is checked within this pinned local environment.",
        "",
    ]
    Path("reports/phase_6_baselines.md").write_text("\n".join(lines))
    stability = [
        "# Phase 6 — descriptive development stability",
        "",
        "Five validation sets overlap; no independent-replication confidence interval is computed.",
        "Ranks below are based on reference-scenario point estimates, not statistically declared winners.",
        "",
        "| Reach | Random first | Response first | S first | Point-estimate orders by split |",
        "|---|---:|---:|---:|---|",
    ]
    for k, q in enumerate(REACH):
        orders = [
            sorted(
                MODELS,
                key=lambda name: s["evaluation"]["scenarios"]["0.85"]["models"][name]["policies"][
                    k
                ]["value"],
                reverse=True,
            )
            for s in splits
        ]
        counts = [sum(o[0] == name for o in orders) for name in MODELS]
        stability.append(
            f"| {q:.0%} | {counts[0]} | {counts[1]} | {counts[2]} | "
            + "; ".join(">".join(o) for o in orders)
            + " |"
        )
    stability += [
        "",
        "## Full-prefix ranking areas: reference-scenario means [ranges]",
        "",
        "| Model | IPW AUUC | IPW Qini area |",
        "|---|---:|---:|",
    ]
    for name in MODELS:
        cells = []
        for metric in ("ipw_auuc", "ipw_qini_area"):
            vals = [s["evaluation"]["scenarios"]["0.85"]["models"][name][metric] for s in splits]
            cells.append(f"{np.mean(vals):.8f} [{min(vals):.8f}, {max(vals):.8f}]")
        stability.append(f"| {name} | " + " | ".join(cells) + " |")
    stability += [
        "",
        "Differences may reflect membership and fitted-model variation. Small or overlapping paired bands",
        "support no clear preference under that scenario. Assumption sensitivity can dominate sampling intervals.",
        "No model or reach is selected for final evaluation in this phase.",
        "",
    ]
    Path("reports/phase_6_stability.md").write_text("\n".join(stability))
    mlflow.set_tracking_uri(Path(tracking_directory).resolve().as_uri())
    for s in splits:
        with mlflow.start_run(run_id=s["mlflow_run_id"]):
            from marketing_uplift.baselines import parameters

            mlflow.log_dict(parameters(report["recipe"], s["seed"]), "lightgbm_parameters.json")
            mlflow.log_dict(
                {
                    "python": platform.python_version(),
                    "numpy": np.__version__,
                    "sklearn": sklearn.__version__,
                    "lightgbm": lightgbm.__version__,
                    "duckdb": duckdb.__version__,
                    "mlflow": mlflow.__version__,
                    "platform": platform.platform(),
                },
                "runtime.json",
            )
            private = Path("artifacts/phase6") / report["protocol_sha256"] / str(s["seed"])
            for name in s["artifact_hashes"]:
                if name.endswith(".npy"):
                    mlflow.log_artifact(str(private / name), "predictions")
            for e, scenario in s["evaluation"]["scenarios"].items():
                for name in MODELS:
                    model = scenario["models"][name]
                    mlflow.log_metrics(
                        {
                            f"e{e}_{name}_{metric}": model[metric]
                            for metric in ("ipw_auuc", "ipw_qini_area")
                        }
                    )
                    mlflow.log_metrics(
                        {
                            f"e{e}_{name}_value_reach{int(100 * p['reach'])}": p["value"]
                            for p in model["policies"]
                        }
                    )
            mlflow.log_artifact("reports/phase_6_baselines.md", "aggregate_reports")
            mlflow.log_artifact("reports/phase_6_stability.md", "aggregate_reports")
