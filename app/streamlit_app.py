"""Streamlit entrypoint: presentation of public frozen aggregates, never experiments."""

import sys
from pathlib import Path

# Fixed repository paths, not a user-supplied import/data location. Community Cloud
# installs only app/requirements.txt, not the historical research package.
ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "src"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from app import charts  # noqa: E402
from app.dashboard_data import (  # noqa: E402
    LABELS,
    MODELS,
    REACHES,
    SCENARIOS,
    estimate,
    illustrate,
    load_data,
    observed_rates,
    paired,
    policy_rows,
    sensitivity_rows,
)

REPOSITORY = "https://github.com/Sjaisw12/marketing-uplift-engine"
PAGES = (
    "Overview",
    "Policy comparisons",
    "Sensitivity explorer",
    "Budget illustration",
    "Models & limitations",
)

st.set_page_config(
    page_title="Marketing Uplift | Evidence before spend",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto",
)


def controls(page):
    method, propensity = "dr", 0.85
    with st.sidebar:
        st.subheader("Evaluation assumptions")
        if page != "Sensitivity explorer":
            method = st.selectbox(
                "Saved evaluator",
                ("dr", "ipw"),
                format_func=lambda x: "Shared DR" if x == "dr" else "IPW",
                key="evaluator",
                help="Both are assumption-dependent evaluators.",
            )
            propensity = st.selectbox(
                "Assumed treatment propensity",
                SCENARIOS,
                index=2,
                format_func=lambda x: f"{x:.3f}" + (" · reference" if x == 0.85 else ""),
                key="propensity",
                help="Five saved scenarios only; not verified probabilities.",
            )
        interval = st.selectbox(
            "Saved interval",
            ("simultaneous", "pointwise"),
            key="interval",
            format_func=lambda x: "Simultaneous 95% · 765 contrasts"
            if x == "simultaneous"
            else "Pointwise 95% · individual contrast",
            help="Nominal conditional intervals. Simultaneous coverage retains the original "
            "765-contrast family; pointwise coverage is for one contrast.",
        )
        st.caption(
            "Simultaneous coverage retains all 765 contrasts; display filtering does not shrink it."
        )
        uncertainty = st.selectbox(
            "Uncertainty conditioning",
            ("iid", "stratified"),
            format_func=lambda x: "IID working model · primary"
            if x == "iid"
            else "Fixed-stratum sensitivity · secondary",
            key="uncertainty",
        )
    return dict(method=method, propensity=propensity, interval=interval, uncertainty=uncertainty)


def evidence_note(options, all_scenarios=False):
    if all_scenarios:
        st.caption(
            f"IPW and shared DR · all five saved propensity assumptions · "
            f"{options['interval']} 95% · {options['uncertainty']} working model. "
            "Units: visits per 1,000 eligible records."
        )
    else:
        st.caption(
            f"{'Shared DR' if options['method'] == 'dr' else 'IPW'} · assumed e="
            f"{options['propensity']:.3f} · {options['interval']} 95% · "
            f"{options['uncertainty']} working model. Units: visits per 1,000 eligible records."
        )
    if options["interval"] == "pointwise":
        st.info(
            "Pointwise intervals do not provide simultaneous coverage for multiple comparisons."
        )
    if options["uncertainty"] == "stratified":
        st.warning(
            "Secondary sensitivity fixes observed treatment × visit composition. It does not "
            "replace IID uncertainty; zero conditional variance is not causal certainty."
        )


def show_table(rows):
    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        width="stretch",
        column_config={
            k: st.column_config.NumberColumn(format="%.3f")
            for k in ("Gain / 1,000", "Lower", "Upper")
        },
    )


def overview(data):
    st.title("Evidence before spend")
    st.write(
        "A marketing team wants incremental visits—not just people likely to visit anyway. "
        "Explore the completed Criteo benchmark study without changing its frozen decision."
    )
    cols = st.columns(3)
    for col, (label, n) in zip(
        cols,
        [
            ("Official dataset", data["population"]["source_rows"]),
            ("Development records", data["population"]["development_rows"]),
            ("Final holdout", data["population"]["holdout_rows"]),
        ],
        strict=True,
    ):
        col.metric(label, f"{n:,}")
    with st.container(border=True):
        st.subheader("Frozen primary recommendation: no targeting")
        st.write(
            "Zero advertising assignments. Zero hypothetical spending. No change to this "
            "recommendation based on secondary holdout diagnostics."
        )
        st.caption(
            "Zero gain relative to no targeting is an identity. It does not prove advertising "
            "ineffective or abstention optimal; visits without advertising need not be zero."
        )
    st.subheader("Observed visits by assignment arm")
    control, treated, difference = observed_rates(data)
    cols = st.columns(3)
    cols[0].metric("Control visit rate", f"{100 * control:.4f}%")
    cols[1].metric("Treatment visit rate", f"{100 * treated:.4f}%")
    cols[2].metric(
        "Descriptive difference",
        f"{difference:.4f} pp",
        help="Percentage points, not a relative percent change or verified causal effect.",
    )
    st.altair_chart(charts.visit_rates(control, treated), use_container_width=True)
    s = data["support"]
    st.caption(
        f"Control: {s['control_visits']:,} visits / "
        f"{s['control_nonvisits'] + s['control_visits']:,} records. Treatment: "
        f"{s['treatment_visits']:,} / {s['treatment_nonvisits'] + s['treatment_visits']:,}."
    )
    st.info(
        "Descriptive assignment rates are not exposure effects or verified advertiser-wide lift. "
        "Criteo pools experiments and uses non-uniform privacy subsampling; original assignment "
        "probabilities and experiment identifiers are unavailable."
    )
    st.subheader("From prediction to an accountable decision")
    st.write(
        "The study compares random targeting, treated-response prediction and S/T uplift "
        "rankings at equal reach. All user predictors were f0–f11. The final evaluation is "
        "completed and closed; this dashboard reads saved aggregates only."
    )


def policies(data, options):
    st.title("Policy comparisons")
    st.write(
        "Compare four frozen rankings at the same reach. These are secondary diagnostics, "
        "not a policy-selection or deployment recommendation."
    )
    evidence_note(options)
    selected = st.multiselect(
        "Rankings to display", MODELS, default=list(MODELS), format_func=LABELS.get, key="policies"
    )
    focus = st.select_slider("Focus reach (%)", REACHES, value=20, key="focus_reach")
    rows = [r for r in policy_rows(data, **options) if r["Policy"] in [LABELS[m] for m in selected]]
    if not rows:
        st.info("Select at least one ranking to display saved comparisons.")
        return
    st.altair_chart(charts.intervals(rows), use_container_width=True)
    st.caption(
        "Whiskers are the selected saved interval. Lines join only fixed reach points. "
        "Zero is the no-targeting reference identity; no full-prefix AUUC/Qini is inferred."
    )
    st.subheader(f"Same-reach comparison · {focus}%")
    show_table([r for r in rows if r["Reach (%)"] == focus])
    anchor = estimate(data, "all", 100, **options)
    with st.expander("No-targeting and all-targeting reference policies"):
        st.write(
            "No targeting: 0 gain relative to itself by identity; no statistical interval needed."
        )
        st.write(
            f"All targeting: {anchor.value:.3f} [{anchor.low:.3f}, {anchor.high:.3f}] "
            "visits per 1,000 eligible. This 100% anchor has a different assignment budget."
        )
    with st.expander("All displayed saved reach values"):
        show_table(rows)


def sensitivity(data, options):
    st.title("Sensitivity explorer")
    st.write(
        "Assignment probabilities are unknown. Explore the five predeclared assumptions; "
        "no unsupported propensity or interval is interpolated."
    )
    evidence_note(options, all_scenarios=True)
    model = st.selectbox(
        "Diagnostic policy",
        (*MODELS, "all"),
        index=4,
        format_func=LABELS.get,
        key="sensitivity_policy",
    )
    reach = st.select_slider(
        "Diagnostic reach (%)", REACHES, value=20, disabled=model == "all", key="sensitivity_reach"
    )
    if model == "all":
        reach = 100
        st.caption("100% all-targeting anchor; not equal spending to the 10–50% policies.")
    rows = sensitivity_rows(
        data, model, reach, uncertainty=options["uncertainty"], interval=options["interval"]
    )
    st.altair_chart(charts.intervals(rows, sensitivity=True), use_container_width=True)
    st.caption("Both evaluators are displayed at every saved assumption; no interpolation is used.")
    show_table(rows)
    st.warning(
        "These propensity values are assumptions, not a calibrated uncertainty distribution. "
        "Stable DR does not prove correct nuisances, identification or transportability."
    )


def budget(data, options):
    st.title("Hypothetical budget illustration")
    st.warning(
        "Assumption-dependent illustration only—not validated ROI, deployment guidance or "
        "a new causal estimate. The frozen recommendation remains no targeting."
    )
    evidence_note(options)
    model = st.selectbox(
        "Policy to illustrate", ("none", *MODELS), format_func=LABELS.get, key="budget_policy"
    )
    reach = st.select_slider(
        "Nominal reach (%)", REACHES, value=20, disabled=model == "none", key="budget_reach"
    )
    cols = st.columns(2)
    n = cols[0].number_input(
        "Eligible population (illustrative)",
        min_value=1,
        max_value=1_000_000_000,
        value=100_000,
        step=1000,
        key="population",
    )
    cap = cols[1].number_input(
        "Budget cap (hypothetical currency units)",
        min_value=0.0,
        max_value=1_000_000_000_000.0,
        value=500.0,
        key="budget_cap",
    )
    cols = st.columns(2)
    cost = cols[0].number_input(
        "Cost per assignment (hypothetical)",
        min_value=0.0,
        max_value=1_000_000.0,
        value=0.01,
        step=0.01,
        format="%.4f",
        key="cost",
    )
    value = cols[1].number_input(
        "Value per incremental visit (hypothetical)",
        min_value=0.0,
        max_value=1_000_000.0,
        value=1.0,
        step=0.1,
        key="visit_value",
    )
    try:
        result = illustrate(
            data, model, 0 if model == "none" else reach, n, cost, value, cap, **options
        )
    except ValueError as exc:
        st.error(str(exc))
        return
    st.subheader("Illustrative arithmetic, not a spending recommendation")
    metrics = st.columns(3)
    metrics[0].metric("Advertising assignments", f"{result.assignments:,}")
    metrics[1].metric("Estimated incremental visits", f"{result.incremental_visits:,.3f}")
    metrics[2].metric("Hypothetical spend", f"{result.spend:,.2f} units")
    metrics = st.columns(2)
    metrics[0].metric("Hypothetical net benefit", f"{result.net_value:,.2f} units")
    metrics[1].metric("Unspent budget", f"{result.unspent_budget:,.2f} units")
    if result.scaled_benchmark_bounds is None:
        st.info(
            "No targeting: zero assignments, spend and relative gain by identity. "
            "No statistical CI is implied."
        )
    else:
        low, high = result.scaled_benchmark_bounds
        st.write(
            f"Scaled saved benchmark bounds for incremental visits: [{low:,.3f}, {high:,.3f}]."
        )
        st.caption(
            "These multiply the saved benchmark interval by population / 1,000. They are not "
            "prediction intervals for a new population; transport uncertainty is omitted. "
            "Prices are fixed assumptions."
        )
        st.caption(
            f"ceil(nominal reach × population) gives {100 * result.actual_reach:.4f}% actual "
            "illustrative reach. Rates stay at the nominal saved reach; "
            "small populations can round substantially."
        )
    st.caption(
        "Visits = population × saved gain / 1,000. Spend = assignments × cost. "
        "Net benefit = value × estimated incremental visits − spend. No real people are selected."
    )


def models(data, options):
    st.title("Models, comparisons & limitations")
    st.write(
        "Response predicts who visits. S/T rankings contrast predicted visit probabilities "
        "under assignment versus control; no individual causal response is observed."
    )
    evidence_note(options)
    a = st.selectbox("First ranking", MODELS, index=3, format_func=LABELS.get, key="pair_first")
    b = st.selectbox(
        "Comparison ranking", MODELS, index=2, format_func=LABELS.get, key="pair_second"
    )
    if a == b:
        st.info(
            "A ranking minus itself is zero by identity. "
            "Choose different rankings for a saved paired interval."
        )
    else:
        rows = []
        for reach in REACHES:
            e = paired(data, a, b, reach, **options)
            rows.append(
                {"Reach (%)": reach, "Gain / 1,000": e.value, "Lower": e.low, "Upper": e.high}
            )
        st.subheader(f"Paired difference: {LABELS[a]} minus {LABELS[b]}")
        st.altair_chart(charts.intervals(rows, paired=True), use_container_width=True)
        show_table(rows)
    st.info(
        "At reference e=0.85, all ten simultaneous IPW/shared-DR S-versus-T comparisons "
        "include zero. This is not an equivalence test or a reason to change the primary policy."
    )
    with st.expander("How the models differ", expanded=True):
        st.markdown(
            "- **Treated response:** visit prediction within the assigned arm.\n"
            "- **S-learner:** one model evaluated at a separate intervention input of 1 and 0.\n"
            "- **T-learner:** separate arm models, predicted treatment minus control.\n"
            "- **Random:** frozen random priority, matched reach.\n\n"
            "User predictors were exactly f0–f11. Exposure, outcomes and IDs were excluded. "
            "No model is loaded by this app."
        )
    with st.expander("Why these intervals are conditional", expanded=True):
        st.write(
            "2,000 paired Gaussian-multiplier draws generated the saved intervals. The "
            "simultaneous family contains 765 predeclared contrasts, including nuisance "
            "sensitivity not selectable in this app. Pointwise intervals do not cover the "
            "whole family. These are nominal working-model intervals conditional on fitted "
            "models and fixed policies—not exact randomization intervals or ordinary row bootstrap."
        )
        st.write(
            "Overlapping development splits are not independent experiments. Unknown dependence, "
            "training uncertainty and outcome-stratification limitations remain. Fixed-stratum "
            "sensitivity conditions on observed treatment × visit composition."
        )
    st.subheader("Identification and responsible interpretation")
    st.write(
        "Causal interpretation additionally needs consistency, positivity, exchangeability, "
        "no interference and appropriate nuisance correctness. Hidden experiment-specific "
        "assignment, pooled experiments and non-uniform privacy sampling are not cured by DR. "
        "Assignment effects differ from actual exposure effects. There are no real costs, "
        "revenues, dates or verified customer IDs for ROI, temporal stability or dependence claims."
    )


def main():
    try:
        data = load_data()
    except (OSError, ValueError, TypeError, KeyError):
        st.error(
            "Approved aggregate provenance validation failed. The dashboard is unavailable; "
            "no alternative data source or execution fallback is permitted."
        )
        st.stop()
    with st.sidebar:
        st.markdown("### Marketing Uplift\nEvidence before spend")
        page = st.radio("Explore the evidence", PAGES, key="page")
        st.success("Frozen primary policy: no targeting")
        st.caption("Exploratory controls never change the locked recommendation.")
    st.caption("CRITEO V2.1  /  FROZEN AGGREGATE EVIDENCE")
    st.caption("Primary decision: no targeting. Exploratory controls are diagnostic only.")
    if page == "Overview":
        overview(data)
    else:
        options = controls(page)
        {
            "Policy comparisons": policies,
            "Sensitivity explorer": sensitivity,
            "Budget illustration": budget,
            "Models & limitations": models,
        }[page](data, options)
    with st.expander("Source, provenance & interpretation"):
        st.write(
            "Corrected Criteo Uplift v2.1. Visit is the outcome; conversion is outside scope. "
            "The dashboard uses only the publicly approved, frozen Phase 10 aggregate snapshot."
        )
        st.code("358c331d72df76d0ca1e4fddd36c7c35be32b1a0b2dd0ae12949c5967ac46169", language=None)
        st.caption(
            "Snapshot SHA-256. Historical local-review-only metadata is preserved as provenance; "
            "public disclosure was separately approved. No holdout evaluation is available here."
        )
        st.link_button("Read the case study", REPOSITORY + "/blob/main/docs/CASE_STUDY.md")
    st.divider()
    st.caption(
        "Data: Criteo AI Lab · Diemert et al. (2018), A Large Scale Benchmark for Uplift Modeling. "
        "Criteo-derived aggregates: CC BY-NC-SA 4.0 · software: MIT. No endorsement implied."
    )
    st.markdown(
        "[Dataset](https://huggingface.co/datasets/criteo/criteo-uplift) · "
        "[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) · "
        f"[Model card]({REPOSITORY}/blob/main/docs/MODEL_CARD.md)"
    )


if __name__ == "__main__":
    main()
