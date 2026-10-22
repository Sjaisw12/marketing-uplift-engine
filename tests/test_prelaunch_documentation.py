"""Presentation/proposal boundaries; no experimental computation or private IO."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_exploration_proposals_are_explicitly_unexecuted_and_development_only():
    doc = " ".join((ROOT / "docs/DEVELOPMENT_EXPLORATION_FEASIBILITY.md").read_text().split())
    assert "execution NOT approved and NOT performed" in doc
    assert "240 coordinates" in doc
    assert "300 marginal coordinates" in doc
    assert "765 two-sided diagnostic contrasts" in doc
    assert "whole-arm denominators" in doc.lower()
    assert "sample_cov(psi)/N" in doc
    assert "No alternative recommendation is reported" in doc


def test_arm_balance_plan_avoids_unnecessary_outcomes_and_causal_conclusions():
    doc = " ".join((ROOT / "docs/ARM_BALANCE_FEASIBILITY.md").read_text().split())
    assert "not executed" in doc
    assert "Y is not needed" in doc
    assert "row_id,treatment" in doc
    assert "p*(1-p)*(d1/e + d0/(1-e))" in doc
    assert "cannot identify" in doc
    assert "No such conclusion is reported here" in doc


def test_readme_identity_preview_and_unlaunched_status_are_clear():
    doc = (ROOT / "README.md").read_text()
    assert "OpenAI Codex assisted" in doc
    assert "Sanyam Jaiswal" in doc
    assert "PR #16" in doc
    assert "**Live URL:** not configured" in doc
    assert "Local Streamlit development dashboard" in doc
    assert (ROOT / "docs/images/decision-lab-overview.png").is_file()
    assert "React, TypeScript and Vite" in doc
