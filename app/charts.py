"""Responsive Vega-Lite charts of saved estimates and saved interval endpoints."""

import altair as alt
import pandas as pd

POLICIES = ["Random", "Treated response", "S-learner", "T-learner"]
PALETTE = ["#64748B", "#B45309", "#0F766E", "#7C3AED"]


def intervals(rows, *, sensitivity=False, paired=False):
    frame = pd.DataFrame(rows)
    x = "Assumed propensity" if sensitivity else "Reach (%)"
    color = "Evaluator" if sensitivity else "Policy"
    colors = (["Shared DR", "IPW"], ["#0F766E", "#B45309"]) if sensitivity else (POLICIES, PALETTE)
    base = alt.Chart(frame).encode(
        x=alt.X(f"{x}:O", title=x, sort=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y(
            "Gain / 1,000:Q",
            title=("Paired difference" if paired else "Estimated gain") + " / 1,000 eligible",
            scale=alt.Scale(zero=True),
        ),
        tooltip=[
            alt.Tooltip(f"{x}:O"),
            alt.Tooltip("Gain / 1,000:Q", format=".3f"),
            alt.Tooltip("Lower:Q", format=".3f"),
            alt.Tooltip("Upper:Q", format=".3f"),
        ],
    )
    if not paired:
        base = base.encode(
            color=alt.Color(
                f"{color}:N", title=None, scale=alt.Scale(domain=colors[0], range=colors[1])
            ),
            tooltip=[
                alt.Tooltip(f"{color}:N"),
                alt.Tooltip(f"{x}:O"),
                alt.Tooltip("Gain / 1,000:Q", format=".3f"),
                alt.Tooltip("Lower:Q", format=".3f"),
                alt.Tooltip("Upper:Q", format=".3f"),
            ],
        )
    if sensitivity:
        base = base.encode(xOffset=alt.XOffset("Evaluator:N"))
    title = ("Paired difference" if paired else "Estimated gain") + " / 1,000 eligible"
    rules = base.mark_rule(strokeWidth=2, color="#7C3AED" if paired else alt.Undefined).encode(
        y=alt.Y("Lower:Q", title=title, scale=alt.Scale(zero=True)), y2="Upper:Q"
    )
    points = base.mark_point(filled=True, size=85, color="#7C3AED" if paired else alt.Undefined)
    layers = [rules, points]
    if not sensitivity and not paired:
        layers.insert(0, base.mark_line(strokeWidth=2, opacity=0.65))
    zero = (
        alt.Chart(pd.DataFrame({"zero": [0]}))
        .mark_rule(color="#64748B", strokeDash=[5, 4])
        .encode(y=alt.Y("zero:Q", title=title))
    )
    return (
        alt.layer(zero, *layers)
        .properties(height=350)
        .configure_legend(orient="bottom", columns=2, labelLimit=220)
        .configure_axis(labelFontSize=12, titleFontSize=12)
    )


def visit_rates(control, treated):
    data = pd.DataFrame(
        {
            "Assignment": ["Control", "Treatment"],
            "Observed visit rate (%)": [100 * control, 100 * treated],
        }
    )
    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(
                "Assignment:N",
                title=None,
                sort=["Control", "Treatment"],
                axis=alt.Axis(labelAngle=0),
            ),
            y=alt.Y("Observed visit rate (%):Q", scale=alt.Scale(zero=True)),
            color=alt.Color(
                "Assignment:N",
                scale=alt.Scale(domain=["Control", "Treatment"], range=["#64748B", "#0F766E"]),
                legend=None,
            ),
            tooltip=["Assignment", alt.Tooltip("Observed visit rate (%):Q", format=".4f")],
        )
        .properties(height=260)
    )
