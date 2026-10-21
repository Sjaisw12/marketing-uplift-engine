"""Focused presentation regressions; never reads private study artifacts."""

from decimal import Decimal
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app import charts, design
from app import dashboard_data as dd

ROOT = Path(__file__).resolve().parents[1]


def test_html_components_escape_text_and_reject_arbitrary_styles(monkeypatch):
    captured = []
    monkeypatch.setattr(design.st, "html", captured.append)
    design.heading("<section>", "Plain title", "<script>unsafe</script>")
    design.panel("<title>", "<img src=x>", "teal")
    design.cards([("<node>", "A & B")], flow=True)
    assert all("<script>" not in s and "<img" not in s for s in captured)
    assert "&lt;title&gt;" in captured[-2]
    assert "A &amp; B" in captured[-1]
    with pytest.raises(ValueError, match="tone"):
        design.panel("Title", "Body", '" onclick="unsafe')


def test_design_has_responsive_layout_and_visible_keyboard_focus():
    assert "max-width:700px" in design.CSS
    assert "max-width:1100px" in design.CSS
    assert '[data-testid="stCaptionContainer"] {opacity:1!important;}' in design.CSS
    assert "focus-visible" in design.CSS
    assert "prefers-reduced-motion" in design.CSS
    assert "#0B1730" in design.CSS
    assert "#2563EB" in design.CSS
    assert "@import" not in design.CSS and "url(" not in design.CSS
    assert "display:none" not in design.CSS


@pytest.mark.parametrize(
    "foreground,background",
    [("182640", "FFFFFF"), ("52627A", "F6F8FC"), ("DCE5F5", "0B1730"), ("B2C1D8", "0B1730")],
)
def test_core_text_palette_meets_normal_text_contrast(foreground, background):
    def luminance(hex_color):
        values = [int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4)]
        linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in values]
        return sum(c * weight for c, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True))

    a, b = sorted((luminance(foreground), luminance(background)))
    assert (b + 0.05) / (a + 0.05) >= 4.5


def test_policy_semantic_colors_are_distinct_and_saved_points_unchanged():
    assert len(set(charts.PALETTE)) == 4
    rows = dd.policy_rows(dd.load_data())
    spec = charts.intervals(rows).to_dict()
    saved = next(values for values in spec["datasets"].values() if "Lower" in values[0])
    assert saved == rows


def test_budget_allocation_preserves_values_including_zero():
    for spend, unspent in [(Decimal("0"), Decimal("500")), (Decimal("200.25"), Decimal("299.75"))]:
        spec = charts.budget_allocation(spend, unspent).to_dict()
        saved = next(iter(spec["datasets"].values()))
        assert [r["Currency units"] for r in saved] == [float(spend), float(unspent)]
        assert all(r["Budget"] == "Budget cap" for r in saved)


def test_redesigned_navigation_insights_and_budget_outputs():
    at = AppTest.from_file(str(ROOT / "app/streamlit_app.py"), default_timeout=20).run()
    assert not at.exception
    assert [m.value for m in at.metric][:4] == ["13.98M", "11.88M", "2.10M", "No targeting"]
    assert any(m.value == "4.8543%" for m in at.metric)
    at.radio(key="page").set_value("Policy comparisons").run()
    at.select_slider(key="focus_reach").set_value(40).run()
    assert not at.exception and len(at.metric) == 4
    saved = dd.estimate(dd.load_data(), "t_learner", 40)
    assert at.metric[-1].value == f"{saved.value:.3f}"
    at.radio(key="page").set_value("Budget illustration").run()
    assert not at.exception
    assert any(
        m.label == "Hypothetical incremental value" and m.value == "0.00 units" for m in at.metric
    )
    at.selectbox(key="budget_policy").set_value("s_learner").run()
    assert not at.exception
    result = dd.illustrate(dd.load_data(), "s_learner", 20, 100_000, 0.01, 1, 500)
    assert any(
        m.label == "Hypothetical incremental value"
        and m.value == f"{result.net_value + result.spend:,.2f} units"
        for m in at.metric
    )
    assert "no targeting" in at.sidebar.success[0].value
