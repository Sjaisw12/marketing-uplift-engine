"""Descriptive presentation text derived only from selected frozen aggregate rows."""

from app.dashboard_data import LABELS, paired


def policy_insights(data, rows, reach, options):
    above = sum(row["Lower"] > 0 for row in rows)
    items = [
        (
            "Read the interval, not a league table",
            f"At {reach}% reach, {above} of {len(rows)} displayed saved "
            f"{options['interval']} intervals lie entirely above zero. "
            "This is conditional evidence relative to no targeting, not causal superiority "
            "between rankings. Pointwise coverage does not cover multiple comparisons.",
        )
    ]
    names = {row["Policy"] for row in rows}
    if {LABELS["s_learner"], LABELS["t_learner"]} <= names:
        result = paired(data, "t_learner", "s_learner", reach, **options)
        items.append(
            (
                "Saved paired comparison · T minus S",
                f"{result.value:.3f} visits per 1,000 eligible; saved "
                f"{options['interval']} interval [{result.low:.3f}, {result.high:.3f}]. "
                "This paired contrast, not overlap of separate intervals, compares the rankings. "
                "It does not select a new primary policy.",
            )
        )
    else:
        items.append(
            (
                "Like-for-like diagnostic reach",
                f"All {len(rows)} displayed rankings use the same saved {reach}% reach. "
                "The gain denominator is 1,000 eligible records, not 1,000 "
                "advertising assignments. "
                "Display filtering does not shrink the original 765-comparison family.",
            )
        )
    return items


def sensitivity_summary(rows):
    ranges = {
        method: (
            min(r["Gain / 1,000"] for r in rows if r["Evaluator"] == method),
            max(r["Gain / 1,000"] for r in rows if r["Evaluator"] == method),
        )
        for method in ("IPW", "Shared DR")
    }
    ipw, dr = ranges["IPW"], ranges["Shared DR"]
    relation = (
        "Shared DR varies less than IPW in this display."
        if dr[1] - dr[0] < ipw[1] - ipw[0]
        else "Shared DR does not vary less than IPW in this display."
    )
    return (
        f"For the selected policy/reach, IPW spans {ipw[0]:.3f} to {ipw[1]:.3f}; "
        f"shared DR spans {dr[0]:.3f} to {dr[1]:.3f} visits per 1,000 eligible. "
        f"{relation} These are ranges of five saved point estimates, not confidence intervals. "
        "Propensities are assumed scenarios, not a probability distribution; stability does "
        "not verify nuisance correctness or causal identification."
    )
