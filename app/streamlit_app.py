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

from app import charts, design, insights  # noqa: E402
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
    page_title="Marketing Uplift | Decision Intelligence",
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


def open_policy_performance():
    """Navigation only; native callback runs before the radio is constructed."""
    st.session_state["page"] = "Policy comparisons"


def overview(data):
    st.html(
        '<section class="mu-hero"><div class="mu-brand">'
        "Marketing Uplift | Decision Intelligence</div>"
        '<span class="mu-tag">OFFLINE RESEARCH DEMO · FROZEN EVIDENCE</span>'
        "<h1>Smarter Marketing Starts With Evidence</h1>"
        "<p>Explore how machine learning, causal inference and uncertainty can inform advertising "
        "decisions—and why spending nothing can be the appropriate conservative "
        "recommendation.</p></section>"
    )
    with st.container(key="overview_kpis"):
        cols = st.columns(4)
        for col, (label, value, help_text) in zip(
            cols,
            [
                (
                    "Total records",
                    f"{data['population']['source_rows'] / 1e6:.2f}M",
                    "13,979,592 corrected Criteo v2.1 records.",
                ),
                (
                    "Development records",
                    f"{data['population']['development_rows'] / 1e6:.2f}M",
                    "11,882,653 records used to develop the frozen framework.",
                ),
                (
                    "Final holdout records",
                    f"{data['population']['holdout_rows'] / 1e6:.2f}M",
                    "2,096,939 records; one-time evaluation is complete and closed.",
                ),
                (
                    "Frozen primary policy",
                    "No targeting",
                    "Zero assignments and hypothetical spend; "
                    "diagnostics cannot replace this policy.",
                ),
            ],
            strict=True,
        ):
            col.metric(label, value, help=help_text)
    design.panel(
        "Final decision: Retain no targeting",
        "The prespecified conservative framework abstained across all 40 "
        "development scenario/split combinations. "
        "Positive secondary holdout diagnostics do not override that frozen recommendation. "
        "This does not prove advertising ineffective or abstention universally optimal.",
        "teal",
    )
    st.subheader("What the study observed")
    st.caption("Observed visits by assignment arm · descriptive, not a verified causal effect")
    control, treated, difference = observed_rates(data)
    left, right = st.columns([1.5, 1])
    with left:
        st.altair_chart(charts.visit_rates(control, treated), use_container_width=True)
    with right:
        cols = st.columns(2)
        cols[0].metric("Control visit rate", f"{100 * control:.4f}%")
        cols[1].metric("Treatment visit rate", f"{100 * treated:.4f}%")
        st.metric(
            "Descriptive difference",
            f"{difference:.4f} pp",
            help="Percentage points; not relative percent change or verified causal lift.",
        )
    design.panel(
        "Business takeaway · response is not incrementality",
        "The assigned treatment group visited more often in the released sample. "
        "That descriptive gap "
        "does not tell us which people visited because of advertising. Unknown "
        "assignment probabilities "
        "and privacy subsampling limit causal interpretation.",
    )
    with st.expander("Exact observed counts and experiment context"):
        support = data["support"]
        st.write(
            f"Control: {support['control_visits']:,} visits / "
            f"{support['control_visits'] + support['control_nonvisits']:,} records. "
            f"Treatment: {support['treatment_visits']:,} / "
            f"{support['treatment_visits'] + support['treatment_nonvisits']:,}."
        )
        st.write(
            "Criteo pools experiments and uses non-uniform privacy subsampling. "
            "Experiment identifiers and original assignment probabilities are "
            "unavailable. Assignment differs from actual ad exposure."
        )
    st.subheader("How this helps a marketing decision-maker")
    with st.container(key="decision_help"):
        design.cards(
            [
                (
                    "Compare targeting rules",
                    "Inspect random, response and uplift rankings at equal saved "
                    "reach. Separate likely visits from assumption-dependent "
                    "incremental gains.",
                ),
                (
                    "Put uncertainty beside the estimate",
                    "Use saved paired intervals and propensity sensitivity to judge"
                    " how much a conclusion depends on unverified assumptions.",
                ),
                (
                    "See the budget trade-offs",
                    "Explore assignment costs, visit values and unspent budget as "
                    "hypothetical arithmetic. No validated ROI or automatic "
                    "spending decision is implied.",
                ),
                (
                    "Keep the conservative decision",
                    "Positive diagnostics do not override the prespecified "
                    "no-targeting rule. Spending zero remains a valid option when "
                    "evidence is insufficient.",
                ),
            ]
        )
    st.button(
        "Explore policy performance →",
        key="overview_policy_action",
        type="primary",
        on_click=open_policy_performance,
        help="Open the saved secondary policy diagnostics; the primary policy stays unchanged.",
    )
    st.subheader("Why this matters to marketers")
    design.cards(
        [
            (
                "Predict",
                "Distinguish likely visitors from users with higher predicted "
                "assignment contrasts. Only pre-treatment f0–f11 were predictors.",
            ),
            (
                "Evaluate",
                "Compare fixed rankings at equal reach, preserve paired "
                "uncertainty, and test sensitivity to unverified assumptions.",
            ),
            (
                "Decide",
                "Keep a conservative, accountable spending rule. A positive-looking"
                " diagnostic is not a license to select a new winner.",
            ),
        ]
    )
    st.caption(
        "Explore Policy performance for saved comparisons, Sensitivity & robustness"
        " for assumptions, or Budget impact studio for hypothetical arithmetic. Use"
        " the navigation to continue."
    )


def policies(data, options):
    design.heading(
        "02 / Policy performance",
        "Do smarter targeting rules appear to outperform random targeting?",
        "Compare frozen diagnostic rankings at equal reach. Explore saved "
        "evidence—not an approved alternative policy or a causal winner.",
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
    focus_rows = [r for r in rows if r["Reach (%)"] == focus]
    columns = st.columns(len(focus_rows))
    for col, row in zip(columns, focus_rows, strict=True):
        col.metric(
            row["Policy"],
            f"{row['Gain / 1,000']:.3f}",
            help=f"Saved {options['interval']} interval: "
            f"[{row['Lower']:.3f}, {row['Upper']:.3f}] visits per 1,000 eligible records.",
        )
    design.panel(
        "Business takeaway · compare evidence, not just point estimates",
        f"At {focus}% reach, these are saved gains per 1,000 eligible records "
        "relative to no targeting. "
        "Whiskers reflect the selected conditional uncertainty. A larger point "
        "estimate does not establish causal superiority or authorize a new policy.",
    )
    with st.container(key="policy_insights"):
        design.cards(insights.policy_insights(data, focus_rows, focus, options))
    show_table(focus_rows)
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
    design.heading(
        "03 / Sensitivity & robustness",
        "How much should we trust a result when assumptions are uncertain?",
        "Five predeclared propensity scenarios. Two evaluators. One honest view of "
        "what remains unknown.",
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
    design.panel(
        "What changes when the assumption changes?", insights.sensitivity_summary(rows), "violet"
    )
    spreads = {
        method: max(r["Gain / 1,000"] for r in rows if r["Evaluator"] == method)
        - min(r["Gain / 1,000"] for r in rows if r["Evaluator"] == method)
        for method in ("IPW", "Shared DR")
    }
    design.cards(
        [
            (
                "IPW · assumption sensitivity",
                f"Displayed point estimates span {spreads['IPW']:.3f} visits per 1,000 "
                "across the five assumed propensities.",
            ),
            (
                "Shared DR · displayed stability",
                f"Displayed point estimates span {spreads['Shared DR']:.3f} visits per 1,000. "
                "This is a summary of saved points, not a new uncertainty estimate.",
            ),
            (
                "Stable is not identified",
                "Comparative stability does not verify propensity or nuisance "
                "correctness, cure selection bias, or establish causal "
                "identification.",
            ),
        ]
    )
    with st.expander("Exact saved estimates and interval endpoints"):
        show_table(rows)
    st.warning(
        "These propensity values are assumptions, not a calibrated uncertainty distribution. "
        "Stable DR does not prove correct nuisances, identification or transportability."
    )


def budget(data, options):
    design.heading(
        "04 / Budget impact studio",
        "What could different advertising assumptions mean for a hypothetical budget?",
        "An illustration workspace, not an optimizer. Change business assumptions "
        "while the primary recommendation stays fixed.",
    )
    st.warning(
        "Assumption-dependent illustration only—not validated ROI, deployment guidance or "
        "a new causal estimate. The frozen recommendation remains no targeting."
    )
    evidence_note(options)
    design.panel(
        "Try a hypothetical alternative · keep the primary decision fixed",
        "No targeting is the starting baseline. In Policy to illustrate below, choose Random, "
        "Treated response, S-learner or T-learner; then choose a saved reach and set your "
        "audience, budget, cost and visit-value assumptions. Compare the illustrative outputs "
        "with zero spend. Nothing selects users or changes the recommendation.",
    )
    with st.container(border=True, key="budget_inputs"):
        st.subheader("Build an illustrative scenario")
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
    if model != "none":
        design.panel(
            f"Exploratory scenario · {LABELS[model]} at {reach}% reach",
            "The tiles below scale the selected saved aggregate rate to your illustrative "
            "audience. Positive or negative net values are hypothetical arithmetic, not "
            "validated ROI, a new causal estimate or deployment advice.",
            "violet",
        )
    with st.container(key="budget_outputs"):
        metrics = st.columns(3)
        metrics[0].metric("Advertising assignments", f"{result.assignments:,}")
        metrics[1].metric("Estimated incremental visits", f"{result.incremental_visits:,.3f}")
        metrics[2].metric("Hypothetical spend", f"{result.spend:,.2f} units")
        metrics = st.columns(3)
        metrics[0].metric(
            "Hypothetical incremental value", f"{result.net_value + result.spend:,.2f} units"
        )
        metrics[1].metric("Hypothetical net benefit", f"{result.net_value:,.2f} units")
        metrics[2].metric("Unspent budget", f"{result.unspent_budget:,.2f} units")
        st.altair_chart(
            charts.budget_allocation(result.spend, result.unspent_budget), use_container_width=True
        )
    design.panel(
        "Business takeaway · the budget is a ceiling, not a spending target",
        "No targeting spends zero and leaves the entire hypothetical budget available. "
        "Exploratory values use unverified prices and transport assumptions. Even a"
        " positive hypothetical net benefit does not replace the frozen primary "
        "recommendation.",
        "teal",
    )
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
    design.heading(
        "05 / How the engine works",
        "From likely response to a defensible decision",
        "Prediction, evaluation and decision-making answer different questions. "
        "Understand the safeguards behind the saved evidence.",
    )
    design.cards(
        [
            ("Public benchmark", "Corrected Criteo v2.1; pre-treatment predictors only."),
            ("Frozen development", "Five fixed splits; model recipes and policies locked."),
            ("Predict & compare", "Response and S/T rankings; equal saved reach."),
            ("Evaluate once", "IPW / shared DR; conditional paired uncertainty."),
            ("Retain the rule", "No targeting; no holdout-driven reselection."),
        ],
        flow=True,
    )
    design.cards(
        [
            (
                "Treated response",
                "Predict who will visit among assigned users. Likely response need "
                "not imply incrementality.",
            ),
            (
                "S-learner",
                "One outcome model, evaluated under intervention 1 and 0. Their "
                "difference supplies the ranking.",
            ),
            (
                "T-learner",
                "Separate treatment/control outcome models. Their predicted "
                "probability difference supplies the ranking.",
            ),
        ]
    )
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
    with st.expander("Technical detail · model definitions and feature discipline"):
        st.markdown(
            "- **Treated response:** visit prediction within the assigned arm.\n"
            "- **S-learner:** one model evaluated at a separate intervention input of 1 and 0.\n"
            "- **T-learner:** separate arm models, predicted treatment minus control.\n"
            "- **Random:** frozen random priority, matched reach.\n\n"
            "User predictors were exactly f0–f11. Exposure, outcomes and IDs were excluded. "
            "No model is loaded by this app."
        )
    with st.expander("Technical detail · conditional uncertainty and the 765-comparison family"):
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
    design.panel(
        "IPW versus shared doubly robust evaluation",
        "IPW reweights observed assignments under an assumed propensity. Shared DR "
        "combines reweighting with frozen outcome-model predictions. Its "
        "double-robustness property still requires identification assumptions; it "
        "does not remove hidden experiment assignment or selection bias.",
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
    design.apply()
    try:
        data = load_data()
    except (OSError, ValueError, TypeError, KeyError):
        st.error(
            "Approved aggregate provenance validation failed. The dashboard is unavailable; "
            "no alternative data source or execution fallback is permitted."
        )
        st.stop()
    with st.sidebar:
        st.html('<div class="mu-wordmark">Marketing Uplift<span>Decision Intelligence</span></div>')
        page = st.radio(
            "Explore the evidence",
            PAGES,
            key="page",
            format_func={
                "Overview": "Executive overview",
                "Policy comparisons": "Policy performance",
                "Sensitivity explorer": "Sensitivity & robustness",
                "Budget illustration": "Budget impact studio",
                "Models & limitations": "How the engine works",
            }.get,
        )
        st.success("Frozen primary policy: no targeting")
        st.caption("Exploratory controls never change the locked recommendation.")
    if page != "Overview":
        st.caption("FROZEN EVIDENCE / Primary decision: no targeting · Secondary diagnostics only")
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
        "Offline portfolio demonstration · no live advertising, user targeting or "
        "execution controls."
    )
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
