"""Render the reviewed aggregate snapshot without importing any experiment machinery.

No model loading, outcome access, statistical resampling, fitting or network calls.
Intervals are copied from the completed evaluation, never recalculated here.
"""

import argparse
import csv
import hashlib
import json
import math
from itertools import combinations, product
from pathlib import Path

SNAPSHOT_SHA256 = "358c331d72df76d0ca1e4fddd36c7c35be32b1a0b2dd0ae12949c5967ac46169"
MODELS = ("random", "response", "s_learner", "t_learner")
LABELS = ("Random", "Treated response", "S-learner", "T-learner")
COLORS = ("#788899", "#c27425", "#007f82", "#7752a3")
SCENARIOS = (0.8, 0.825, 0.85, 0.875, 0.9)
FIELDS = (
    "estimate_per_1000",
    "standard_error_per_1000",
    "pointwise_low_per_1000",
    "pointwise_high_per_1000",
    "simultaneous_low_per_1000",
    "simultaneous_high_per_1000",
)
FIGURES = (
    "descriptive_rates",
    "policy_reach",
    "uncertainty_intervals",
    "propensity_sensitivity",
    "s_vs_t",
    "architecture",
)


def _keys(obj, expected):
    if not isinstance(obj, dict) or set(obj) != set(expected):
        raise ValueError("Unexpected aggregate schema: fields missing or not allowlisted")


def validate_snapshot(data):
    """Reject unknown fields, missing comparisons, duplicates and invalid saved intervals."""
    _keys(
        data,
        (
            "schema",
            "publication_status",
            "provenance",
            "population",
            "support",
            "primary",
            "methodology",
            "comparisons",
        ),
    )
    if data["schema"] != 1 or data["publication_status"] != "local-review-only":
        raise ValueError("Only the local review snapshot is supported")
    _keys(
        data["provenance"],
        (
            "evaluation_commit",
            "execution_lock_sha256",
            "result_manifest_sha256",
            "source_aggregate_sha256",
            "model_manifest_sha256",
            "dataset_sha256",
        ),
    )
    for key, value in data["provenance"].items():
        if not isinstance(value, str) or len(value) != (40 if key == "evaluation_commit" else 64):
            raise ValueError("Invalid provenance identity")
        if any(c not in "0123456789abcdef" for c in value):
            raise ValueError("Invalid provenance identity")
    _keys(data["population"], ("source_rows", "development_rows", "holdout_rows"))
    _keys(
        data["support"],
        (
            "control_nonvisits",
            "control_visits",
            "treatment_nonvisits",
            "treatment_visits",
        ),
    )
    if any(
        type(v) is not int or v <= 0
        for v in [
            *data["population"].values(),
            *data["support"].values(),
        ]
    ):
        raise ValueError("Invalid population/support counts")
    pop = data["population"]
    if (
        sum(data["support"].values()) != pop["holdout_rows"]
        or pop["development_rows"] + pop["holdout_rows"] != pop["source_rows"]
    ):
        raise ValueError("Population counts do not reconcile")
    _keys(
        data["primary"],
        (
            "policy",
            "assignments",
            "hypothetical_spending",
            "incremental_gain_relative_to_none",
            "identity_not_optimality_proof",
        ),
    )
    if data["primary"] != {
        "policy": "no-targeting",
        "assignments": 0,
        "hypothetical_spending": 0,
        "incremental_gain_relative_to_none": 0,
        "identity_not_optimality_proof": True,
    }:
        raise ValueError("Frozen primary recommendation changed")
    m = data["methodology"]
    _keys(
        m,
        (
            "reference_propensity",
            "propensity_scenarios",
            "reaches",
            "replicates",
            "confidence",
            "simultaneous_family_size",
            "iid_critical",
            "stratified_critical",
            "stratified_status",
            "units",
        ),
    )
    expected = {
        "reference_propensity": 0.85,
        "propensity_scenarios": list(SCENARIOS),
        "reaches": [0.1, 0.2, 0.3, 0.4, 0.5],
        "replicates": 2000,
        "confidence": 0.95,
        "simultaneous_family_size": 765,
        "stratified_status": "defined",
        "units": "estimated incremental visits per 1000 eligible records",
    }
    if any(m[k] != v for k, v in expected.items()) or any(
        type(m[k]) not in (int, float) or not math.isfinite(m[k]) or m[k] <= 0
        for k in ("iid_critical", "stratified_critical")
    ):
        raise ValueError("Frozen evaluation methodology changed")
    names = {f"{model}:{k}_minus_none" for model, k in product(MODELS, range(1, 6))}
    names |= {f"{a}_minus_{b}:{k}" for (a, b), k in product(combinations(MODELS, 2), range(1, 6))}
    names.add("all_minus_none")
    expected_keys = set(product(("iid", "stratified"), ("ipw", "dr", "s_dr"), SCENARIOS, names))
    seen = set()
    for row in data["comparisons"]:
        _keys(row, ("contrast", "evaluator", "propensity_assumption", "uncertainty", *FIELDS))
        key = (row["uncertainty"], row["evaluator"], row["propensity_assumption"], row["contrast"])
        if key not in expected_keys or key in seen:
            raise ValueError("Missing, duplicate or unexpected comparison")
        seen.add(key)
        if any(type(row[k]) not in (float, int) or not math.isfinite(row[k]) for k in FIELDS):
            raise ValueError("Nonfinite or nonnumeric aggregate statistic")
        if row["standard_error_per_1000"] < 0:
            raise ValueError("Negative standard error")
        for kind in ("pointwise", "simultaneous"):
            if row[f"{kind}_low_per_1000"] > row[f"{kind}_high_per_1000"]:
                raise ValueError("Reversed saved interval")
        est, se = row["estimate_per_1000"], row["standard_error_per_1000"]
        critical = m[f"{row['uncertainty']}_critical"]
        if not all(
            math.isclose(
                row[f"simultaneous_{side}_per_1000"],
                est + sign * critical * se,
                abs_tol=1e-10,
                rel_tol=1e-10,
            )
            for side, sign in (("low", -1), ("high", 1))
        ):
            raise ValueError("Saved simultaneous interval inconsistent with frozen critical value")
    if seen != expected_keys:
        raise ValueError("Incomplete predeclared comparison family")
    return data


def load_snapshot(path, expected_sha=SNAPSHOT_SHA256):
    path = Path(path)
    if path.is_symlink() or path.stat().st_size > 2_000_000:
        raise ValueError("Expected a small regular aggregate JSON file")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError("Aggregate snapshot checksum mismatch")
    return validate_snapshot(json.loads(raw))


def comparison(data, model, reach, method="dr", e=0.85, uncertainty="iid"):
    name = "all_minus_none" if reach == 100 else f"{model}:{reach // 10}_minus_none"
    return next(
        r
        for r in data["comparisons"]
        if (r["evaluator"], r["propensity_assumption"], r["uncertainty"], r["contrast"])
        == (method, e, uncertainty, name)
    )


def t_minus_s(data, reach, method="dr"):
    """Reverse the SAVED paired contrast, including swapping and negating endpoints."""
    row = next(
        r
        for r in data["comparisons"]
        if (r["evaluator"], r["propensity_assumption"], r["uncertainty"], r["contrast"])
        == (method, 0.85, "iid", f"s_learner_minus_t_learner:{reach // 10}")
    )
    result = dict(row, estimate_per_1000=-row["estimate_per_1000"])
    for kind in ("pointwise", "simultaneous"):
        result[f"{kind}_low_per_1000"] = -row[f"{kind}_high_per_1000"]
        result[f"{kind}_high_per_1000"] = -row[f"{kind}_low_per_1000"]
    return result


def render(data, output):
    """Deterministic standalone PNG/SVG figures and a complete aggregate CSV."""
    validate_snapshot(data)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    matplotlib.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": "#c4ced8",
            "text.color": "#182d43",
            "axes.labelcolor": "#182d43",
            "xtick.color": "#405366",
            "ytick.color": "#405366",
            "figure.facecolor": "#fbfcfe",
            "axes.facecolor": "#fbfcfe",
            "savefig.facecolor": "#fbfcfe",
            "svg.hashsalt": "uplift-portfolio-v1",
        }
    )
    files = []

    def save(fig, name, title, caption):
        fig.suptitle(title, x=0.07, ha="left", y=0.97, fontsize=19, fontweight="bold")
        fig.text(0.07, 0.025, caption, fontsize=9, va="bottom", color="#405366", linespacing=1.5)
        fig.subplots_adjust(
            left=0.25 if name == "uncertainty_intervals" else 0.09,
            right=0.96,
            bottom=0.19,
            top=0.81,
            wspace=0.32,
        )
        for ax in fig.axes:
            ax.set_axisbelow(True)
            if ax.axison:
                ax.grid(axis="y", color="#dce3eb", linewidth=0.7, alpha=0.8)
        for ext in ("png", "svg"):
            path = output / f"{name}.{ext}"
            fig.savefig(
                path,
                dpi=180,
                metadata=(
                    {"Software": "portfolio"}
                    if ext == "png"
                    else {"Date": None, "Creator": "portfolio"}
                ),
            )
            if ext == "svg":
                # Matplotlib emits trailing spaces in path commands. Normalize
                # insignificant XML whitespace for reviewable, clean Git diffs.
                path.write_text(
                    "\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n"
                )
            files.append(path)
        plt.close(fig)

    h = data["support"]
    counts = [
        h["control_nonvisits"] + h["control_visits"],
        h["treatment_nonvisits"] + h["treatment_visits"],
    ]
    visits = [h["control_visits"], h["treatment_visits"]]
    rates = [v / n * 100 for v, n in zip(visits, counts, strict=True)]
    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.bar(
        ["Control assignment", "Treatment assignment"],
        rates,
        width=0.48,
        color=[COLORS[0], COLORS[2]],
    )
    for bar, rate, n, v in zip(bars, rates, counts, visits, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            rate + 0.14,
            f"{rate:.4f}%\n{v:,} visits / {n:,} records",
            ha="center",
            fontsize=12,
        )
    ax.set_ylim(0, 6.4)
    ax.set_ylabel("Observed visit rate (%)")
    save(
        fig,
        "descriptive_rates",
        "Observed visits differ by assignment arm",
        f"Holdout: 2,096,939 records. Difference: {rates[1] - rates[0]:.4f} percentage points.\n"
        "Descriptive arm contrast; this alone does not establish a causal assignment effect.",
    )

    fig, (ax, anchor) = plt.subplots(1, 2, figsize=(12, 6), gridspec_kw={"width_ratios": [4, 1]})
    reach = [10, 20, 30, 40, 50]
    for model, label, color in zip(MODELS, LABELS, COLORS, strict=True):
        vals = [comparison(data, model, k)["estimate_per_1000"] for k in reach]
        ax.plot(
            [0, *reach], [0, *vals], "o-", color=color, label=label, linewidth=2.1, markersize=5
        )
    ax.scatter([0], [0], color="#182d43", marker="s", zorder=5)
    ax.set(
        xlabel="Targeting reach (% of eligible records)",
        ylabel="Estimated incremental visits / 1,000 eligible",
        xticks=[0, *reach],
        title="Fixed-reach diagnostic policies",
    )
    ax.legend(loc="lower right", frameon=False, fontsize=10)
    a = comparison(data, "random", 100)
    # Keep the entire all-targeting interval visible on the shared scale.
    ax.set_ylim(-0.4, a["simultaneous_high_per_1000"] * 1.08)
    anchor.errorbar(
        [100],
        [a["estimate_per_1000"]],
        yerr=[
            [a["estimate_per_1000"] - a["simultaneous_low_per_1000"]],
            [a["simultaneous_high_per_1000"] - a["estimate_per_1000"]],
        ],
        fmt="D",
        color="#182d43",
        capsize=5,
    )
    anchor.set(
        xticks=[100],
        xlim=(90, 110),
        xlabel="Reach (%)",
        title="All-targeting\nanchor",
        ylim=ax.get_ylim(),
    )
    save(
        fig,
        "policy_reach",
        "Positive diagnostic gains do not select a deployment policy",
        "Shared DR; assumed e = 0.85. Lines join fixed reach points; no full-prefix area claim.\n"
        "All-targeting: different budget, 95% simultaneous bar. Primary policy: no targeting.",
    )

    fig, ax = plt.subplots(figsize=(12, 7))
    selected = [
        (m, k, label, color)
        for m, label, color in zip(MODELS, LABELS, COLORS, strict=True)
        for k in (10, 50)
    ]
    selected.append(("random", 100, "All-targeting anchor", "#182d43"))
    for pos, (m, k, label, color) in enumerate(selected):
        row = comparison(data, m, k)
        ax.plot(
            [row["simultaneous_low_per_1000"], row["simultaneous_high_per_1000"]],
            [pos, pos],
            color=color,
            linewidth=2,
        )
        ax.plot(
            [row["pointwise_low_per_1000"], row["pointwise_high_per_1000"]],
            [pos, pos],
            color=color,
            linewidth=7,
            solid_capstyle="butt",
        )
        ax.plot(
            row["estimate_per_1000"], pos, "o", color="#fbfcfe", markeredgecolor=color, markersize=5
        )
    ax.set(
        yticks=range(9),
        yticklabels=[f"{label} / {k}%" for _, k, label, _ in selected],
        xlabel="Estimated incremental visits / 1,000 eligible",
    )
    ax.invert_yaxis()
    ax.axvline(0, color="#788899", linestyle="--")
    ax.legend(
        handles=[
            Line2D([0], [0], color="#405366", lw=7, label="Pointwise 95%"),
            Line2D([0], [0], color="#405366", lw=2, label="Simultaneous 95% / 765 contrasts"),
        ],
        loc="lower right",
        bbox_to_anchor=(1, 1.02),
        ncol=2,
        frameon=False,
        fontsize=10,
    )
    save(
        fig,
        "uncertainty_intervals",
        "Intervals answer different comparison questions",
        "Shared DR; assumed e = 0.85. Fixed endpoints shown; all reaches in aggregate tables.\n"
        "2,000 paired Gaussian draws; nominal IID model conditional on fitted models and policies.",
    )

    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    for ax, methods in zip(axes, [("ipw", "dr", "s_dr"), ("dr", "s_dr")], strict=True):
        for method, label, color in zip(
            ("ipw", "dr", "s_dr"),
            ("IPW", "Shared DR", "Final-S DR sensitivity"),
            (COLORS[1], COLORS[2], COLORS[3]),
            strict=True,
        ):
            if method not in methods:
                continue
            a = [comparison(data, "random", 100, method=method, e=e) for e in SCENARIOS]
            ax.plot(SCENARIOS, [r["estimate_per_1000"] for r in a], "o-", color=color, label=label)
            ax.fill_between(
                SCENARIOS,
                [r["simultaneous_low_per_1000"] for r in a],
                [r["simultaneous_high_per_1000"] for r in a],
                alpha=0.10,
                color=color,
            )
        ax.axvline(0.85, color="#788899", linestyle=":")
        ax.set(
            xlabel="Assumed constant treatment propensity",
            xticks=SCENARIOS,
            title="All-targeting minus none"
            if len(methods) == 3
            else "Nuisance sensitivity (zoom)",
        )
        ax.legend(frameon=False, fontsize=9, loc="lower left")
    axes[0].axhline(0, color="#788899", linestyle="--")
    axes[0].set_ylabel("Estimated incremental visits / 1,000 eligible")
    save(
        fig,
        "propensity_sensitivity",
        "Assignment assumptions materially change the IPW estimate",
        "Shading: 95% simultaneous bands / 765 contrasts. Right panel has a different scale.\n"
        "e = 0.80–0.90: assumptions, not a distribution. Stable DR does not prove identification.",
    )

    fig, axes = plt.subplots(1, 2, figsize=(12, 6), sharey=True)
    for ax, method in zip(axes, ("ipw", "dr"), strict=True):
        vals = [t_minus_s(data, k, method) for k in reach]
        ax.axhline(0, color="#788899", linestyle="--")
        ax.errorbar(
            reach,
            [r["estimate_per_1000"] for r in vals],
            yerr=[
                [r["estimate_per_1000"] - r["simultaneous_low_per_1000"] for r in vals],
                [r["simultaneous_high_per_1000"] - r["estimate_per_1000"] for r in vals],
            ],
            color=COLORS[3],
            fmt="o",
            capsize=5,
            linewidth=1.7,
        )
        for k, row in zip(reach, vals, strict=True):
            ax.plot(
                [k, k],
                [row["pointwise_low_per_1000"], row["pointwise_high_per_1000"]],
                color=COLORS[3],
                linewidth=5,
            )
        ax.set(
            xlabel="Targeting reach (%)",
            xticks=reach,
            title="IPW" if method == "ipw" else "Shared DR",
        )
    axes[0].set_ylabel("T-minus-S incremental visits / 1,000 eligible")
    save(
        fig,
        "s_vs_t",
        "No reliable S-versus-T difference in the simultaneous family",
        "Assumed e = 0.85. Thin: simultaneous 95%; thick: pointwise 95%.\n"
        "Nominal working-model intervals conditional on fitted models and fixed policies.\n"
        "All simultaneous bands include zero. Paired contrasts; no winner reselection.",
    )

    fig, ax = plt.subplots(figsize=(13, 6.8))
    ax.set_axis_off()
    boxes = [
        (
            0.01,
            0.58,
            "01  DATA CONTRACT",
            "Pinned Criteo v2.1\nSHA-256 + 13.98M rows\nTyped Parquet; no row deletion",
        ),
        (
            0.35,
            0.58,
            "02  FROZEN DEVELOPMENT",
            "11.88M records; 5 fixed splits\nf0–f11 only; response / S / T\n"
            "Training-only nuisance + MLflow",
        ),
        (
            0.69,
            0.58,
            "03  DECISION LOCK",
            "Budget + uncertainty + sensitivity\n40 / 40 development abstentions\n"
            "Primary policy: no targeting",
        ),
        (
            0.01,
            0.04,
            "04  ONE-TIME FINAL CHECK",
            "2.10M holdout; fixed models\nFeature-only prediction seal\n"
            "Owner-verified encrypted backup",
        ),
        (
            0.35,
            0.04,
            "05  LOCKED EVALUATION",
            "Signed continuation + durable journal\nIPW / DR; 5 propensity assumptions\n"
            "2,000 draws; 765 comparisons",
        ),
        (
            0.69,
            0.04,
            "06  PORTFOLIO",
            "Reviewed aggregate snapshot only\nReproducible figures + case study\n"
            "No execution or model selection",
        ),
    ]
    for x, y, title, body in boxes:
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                0.29,
                0.33,
                boxstyle="round,pad=0.01",
                linewidth=1,
                edgecolor="#b5c6d5",
                facecolor="#eef3f8",
            )
        )
        ax.text(x + 0.016, y + 0.265, title, fontsize=10, weight="bold")
        ax.text(x + 0.016, y + 0.17, body, fontsize=10, va="top", linespacing=1.65)
    for start, end in [
        ((0.30, 0.75), (0.34, 0.75)),
        ((0.64, 0.75), (0.68, 0.75)),
        ((0.30, 0.20), (0.34, 0.20)),
        ((0.64, 0.20), (0.68, 0.20)),
    ]:
        ax.add_patch(
            FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=15, color="#007f82")
        )
    ax.text(
        0.5,
        0.46,
        "15% holdout excluded throughout development; no policy reselection after evaluation",
        ha="center",
        fontsize=10,
        weight="bold",
        color="#007f82",
    )
    save(
        fig,
        "architecture",
        "From a benchmark file to a defensible decision",
        "Rows intact; historical experiments and final results immutable. Aggregate plots only.\n"
        "Offline analysis; no production deployment or real advertising economics claimed.",
    )

    table = output / "diagnostic_comparisons.csv"
    with table.open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(data["comparisons"][0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(data["comparisons"])
    files.append(table)
    evidence = {
        "schema": 1,
        "snapshot_sha256": SNAPSHOT_SHA256,
        "matplotlib_version": matplotlib.__version__,
        "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        "interval_source": "saved evaluation aggregates; no resampling or outcome access",
    }
    (output / "figure_manifest.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    )
    return evidence


def main():
    parser = argparse.ArgumentParser(
        description="Render portfolio figures from saved aggregates only"
    )
    parser.add_argument(
        "--input", type=Path, default=Path("reports/portfolio/aggregate_results.json")
    )
    parser.add_argument("--output", type=Path, default=Path("reports/portfolio/figures"))
    args = parser.parse_args()
    # Do not allow a presentation command to write over its source snapshot.
    if args.output.resolve() == args.input.resolve() or args.output.is_symlink():
        parser.error("Expected a separate regular output directory")
    try:
        evidence = render(load_snapshot(args.input), args.output)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Portfolio validation failed: {exc}\n")
    print(
        f"Rendered {len(FIGURES)} figures (PNG + SVG) and aggregate CSV; "
        f"snapshot {evidence['snapshot_sha256']}"
    )
