"""Aggregate-only portfolio verification; no real data, models or executor access."""

import copy
import csv
import hashlib
import json
from pathlib import Path

import pytest

from portfolio.presentation import (
    FIGURES,
    SNAPSHOT_SHA256,
    comparison,
    load_snapshot,
    render,
    t_minus_s,
    validate_snapshot,
)

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "reports/portfolio/aggregate_results.json"


@pytest.fixture
def aggregate():
    return load_snapshot(SNAPSHOT)


def test_reviewed_aggregate_identity_and_known_results(aggregate):
    assert hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest() == SNAPSHOT_SHA256
    assert aggregate["population"]["holdout_rows"] == 2_096_939
    assert len(aggregate["comparisons"]) == 2 * 765
    ipw = comparison(aggregate, "random", 100, method="ipw")
    dr = comparison(aggregate, "random", 100)
    assert ipw["estimate_per_1000"] == pytest.approx(10.341310853208265)
    assert dr["estimate_per_1000"] == pytest.approx(7.419188764769597)
    assert dr["simultaneous_low_per_1000"] == pytest.approx(6.376046936926798)
    assert aggregate["primary"]["identity_not_optimality_proof"] is True


@pytest.mark.parametrize(
    "mutation,match",
    [
        (lambda d: d.update(predictions=[0.2, 0.3]), "allowlisted"),
        (lambda d: d["comparisons"][0].update(row_id=123), "allowlisted"),
        (lambda d: d["comparisons"].pop(), "Incomplete"),
        (lambda d: d["comparisons"].append(d["comparisons"][0]), "duplicate"),
        (lambda d: d["comparisons"][0].update(estimate_per_1000=float("nan")), "Nonfinite"),
        (lambda d: d["comparisons"][0].update(standard_error_per_1000=-1), "Negative"),
        (lambda d: d["comparisons"][0].update(simultaneous_low_per_1000=100), "Reversed"),
        (lambda d: d["comparisons"][0].update(simultaneous_high_per_1000=100), "inconsistent"),
        (lambda d: d["support"].update(control_visits=0), "Invalid"),
        (lambda d: d["population"].update(holdout_rows=2), "reconcile"),
        (lambda d: d["methodology"].update(reference_propensity=0.9), "methodology"),
        (lambda d: d["methodology"].update(simultaneous_family_size=10), "methodology"),
        (lambda d: d["primary"].update(assignments=1), "primary"),
    ],
)
def test_rejects_disclosure_and_methodology_failures(aggregate, mutation, match):
    changed = copy.deepcopy(aggregate)
    mutation(changed)
    with pytest.raises(ValueError, match=match):
        validate_snapshot(changed)


def test_changed_snapshot_is_rejected_before_rendering(tmp_path):
    path = tmp_path / "changed.json"
    path.write_bytes(SNAPSHOT.read_bytes() + b" ")
    with pytest.raises(ValueError, match="checksum"):
        load_snapshot(path)


def test_paired_contrast_reversal_swaps_interval_endpoints(aggregate):
    result = t_minus_s(aggregate, 10)
    assert result["estimate_per_1000"] == pytest.approx(-0.18963943781579937)
    assert result["simultaneous_low_per_1000"] == pytest.approx(-0.6271804394620559)
    assert result["simultaneous_high_per_1000"] == pytest.approx(0.24790156383045722)
    for method in ("ipw", "dr"):
        for reach in (10, 20, 30, 40, 50):
            row = t_minus_s(aggregate, reach, method)
            assert row["simultaneous_low_per_1000"] < 0 < row["simultaneous_high_per_1000"]


def test_render_is_deterministic_and_never_reads_private_assets(aggregate, tmp_path, monkeypatch):
    from matplotlib.figure import Figure

    # Fail immediately if rendering attempts to enter a dataset, fitted model,
    # checkpoint, executor or private storage interface. Aggregate plots need none.
    original_open = Path.open

    def guarded_open(path, *args, **kwargs):
        text = str(path)
        assert not any(
            part in text
            for part in (
                "stage-b-private",
                "/data/raw/",
                "/data/processed/",
                "/artifacts/",
                "/mlruns/",
            )
        ), text
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    original_save = Figure.savefig

    def checked_save(fig, *args, **kwargs):
        # Regression gate for clipped y-axis labels, legends and long captions.
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        # get_tightbbox includes drawn labels, unlike findobj(Text), which also
        # includes unused ticks outside the current axis limits.
        box = fig.get_tightbbox(renderer).transformed(fig.dpi_scale_trans)
        assert box.x0 >= -2 and box.x1 <= fig.bbox.width + 2, args[0]
        assert box.y0 >= -2 and box.y1 <= fig.bbox.height + 2, args[0]
        return original_save(fig, *args, **kwargs)

    monkeypatch.setattr(Figure, "savefig", checked_save)
    first = render(aggregate, tmp_path / "first")
    second = render(aggregate, tmp_path / "second")
    assert first == second
    assert len(first["files"]) == 2 * len(FIGURES) + 1
    for name in FIGURES:
        png = (tmp_path / "first" / f"{name}.png").read_bytes()
        assert png.startswith(b"\x89PNG\r\n\x1a\n") and len(png) > 10_000
        svg = (tmp_path / "first" / f"{name}.svg").read_text()
        assert "<svg" in svg and "<script" not in svg
    with (tmp_path / "first/diagnostic_comparisons.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1530
    assert float(rows[0]["estimate_per_1000"]) == aggregate["comparisons"][0]["estimate_per_1000"]
    assert json.loads((tmp_path / "first/figure_manifest.json").read_text()) == first


def test_presentation_module_has_no_execution_imports():
    import ast

    tree = ast.parse((ROOT / "src/portfolio/presentation.py").read_text())
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            roots.add((node.module or "").split(".")[0])
    assert roots <= {
        "argparse",
        "csv",
        "hashlib",
        "json",
        "math",
        "itertools",
        "pathlib",
        "matplotlib",
    }


def test_saved_figure_inventory_and_disclosure_fields(aggregate):
    directory = ROOT / "reports/portfolio/figures"
    manifest = json.loads((directory / "figure_manifest.json").read_text())
    assert manifest["snapshot_sha256"] == SNAPSHOT_SHA256
    for name, expected in manifest["files"].items():
        path = directory / name
        assert path.stat().st_size < 2_000_000
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
    text = SNAPSHOT.read_text()
    for forbidden in (
        "/workspace/",
        "/Users/",
        "uplift-private-checkpoint-transfer",
        '"signature"',
        '"row_id"',
        '"predictions"',
        '"binding"',
    ):
        assert forbidden not in text
    assert aggregate["support"]["control_visits"] == 12_016
    assert aggregate["support"]["treatment_visits"] == 86_523


def test_portfolio_document_links_resolve():
    import re

    paths = [
        ROOT / "README.md",
        *[
            ROOT / "docs" / name
            for name in (
                "ARCHITECTURE.md",
                "CASE_STUDY.md",
                "MODEL_CARD.md",
                "PORTFOLIO_REVIEW.md",
            )
        ],
        ROOT / "reports/portfolio/README.md",
    ]
    for path in paths:
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if not target.startswith(("https://", "http://", "#")):
                assert (path.parent / target.split("#")[0]).exists(), (path, target)
