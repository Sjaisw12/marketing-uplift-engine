"""Aggregate arithmetic, deployment isolation and headless Streamlit interaction."""

import ast
import hashlib
import importlib.metadata as metadata
import sys
from decimal import Decimal
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import charts  # noqa: E402
from app import dashboard_data as dd  # noqa: E402


@pytest.fixture
def data():
    return dd.load_data()


def test_pinned_public_loader_and_descriptive_presentation(data):
    assert len(data["comparisons"]) == 1530
    assert data["primary"]["policy"] == "no-targeting"
    c, t, difference = dd.observed_rates(data)
    assert c == pytest.approx(12016 / 314541)
    assert t == pytest.approx(86523 / 1782398)
    assert difference == pytest.approx(1.0341333156248161)
    assert f"{100 * t:.4f}%" == "4.8543%"


def test_loader_fails_closed_for_tampered_or_missing_snapshot(tmp_path, monkeypatch):
    path = tmp_path / "aggregate.json"
    monkeypatch.setattr(dd, "SNAPSHOT", path)
    with pytest.raises(OSError):
        dd.load_data()
    path.write_text('{"row_id": [1], "prediction": [0.9]}')
    with pytest.raises(ValueError, match="checksum"):
        dd.load_data()


@pytest.mark.parametrize("method", ["ipw", "dr"])
@pytest.mark.parametrize("propensity", dd.SCENARIOS)
@pytest.mark.parametrize("interval", ["pointwise", "simultaneous"])
@pytest.mark.parametrize("uncertainty", ["iid", "stratified"])
def test_selects_exact_saved_values(data, method, propensity, interval, uncertainty):
    selected = dd.estimate(data, "s_learner", 20, method, propensity, uncertainty, interval)
    row = next(
        r
        for r in data["comparisons"]
        if (r["contrast"], r["evaluator"], r["propensity_assumption"], r["uncertainty"])
        == ("s_learner:2_minus_none", method, propensity, uncertainty)
    )
    assert selected.value == row["estimate_per_1000"]
    assert selected.low == row[f"{interval}_low_per_1000"]
    assert selected.high == row[f"{interval}_high_per_1000"]


@pytest.mark.parametrize(
    "args",
    [
        ("random", 15, "dr", 0.85),
        ("unknown", 20, "dr", 0.85),
        ("random", 20, "dr", 0.84),
        ("random", 20, "s_dr", 0.85),
        ("all", 20, "dr", 0.85),
        ("random", True, "dr", 0.85),
    ],
)
def test_unsupported_selections_never_interpolate(data, args):
    with pytest.raises(ValueError):
        dd.estimate(data, *args)


def test_saved_paired_contrast_and_sensitivity_grid(data):
    a = dd.paired(data, "t_learner", "s_learner", 10)
    b = dd.paired(data, "s_learner", "t_learner", 10)
    assert a.value == -b.value and a.low == -b.high and a.high == -b.low
    assert a.value == pytest.approx(-0.18963943781579937)
    assert a.low < 0 < a.high
    rows = dd.sensitivity_rows(data, "all", 100)
    assert len(rows) == 10
    assert {r["Assumed propensity"] for r in rows} == {f"{e:.3f}" for e in dd.SCENARIOS}
    with pytest.raises(ValueError, match="different"):
        dd.paired(data, "random", "random", 10)


def test_illustration_scales_eligible_not_targeted_population(data):
    result = dd.illustrate(data, "s_learner", 20, 10_000, ".01", "1", "20")
    saved = dd.estimate(data, "s_learner", 20)
    assert result.assignments == 2000 and result.spend == Decimal("20")
    assert result.incremental_visits == Decimal(str(saved.value)) * 10
    assert result.net_value == result.incremental_visits - 20
    assert result.scaled_benchmark_bounds == (
        Decimal(str(saved.low)) * 10,
        Decimal(str(saved.high)) * 10,
    )
    assert result.unspent_budget == 0


def test_zero_and_negative_values_and_budget_rounding(data):
    primary = dd.illustrate(data, "none", 0, 10_000, ".01", "1", "5")
    assert primary.assignments == primary.spend == primary.net_value == 0
    assert primary.scaled_benchmark_bounds is None
    assert primary.unspent_budget == 5
    negative = dd.illustrate(data, "s_learner", 20, 10_000, ".01", "0", "20")
    assert negative.net_value == -20  # negative expected net value is not clipped
    adverse = dd.illustrate(data, "random", 50, 10_000, "0", "1", "0", method="ipw", propensity=0.9)
    assert adverse.incremental_visits < 0 and adverse.net_value < 0
    free = dd.illustrate(data, "random", 10, 11, "0", "1", "0")
    assert free.assignments == 2 and free.spend == 0  # ceil(.10 * 11)
    with pytest.raises(ValueError, match="No automatic trimming"):
        dd.illustrate(data, "random", 10, 11, ".01", "1", ".019")


@pytest.mark.parametrize(
    "field,value",
    [
        ("population", 0),
        ("population", True),
        ("population", 10.5),
        ("population", 1_000_000_001),
        ("cost", -1),
        ("cost", float("nan")),
        ("visit_value", float("inf")),
        ("visit_value", -1),
        ("budget", -1),
    ],
)
def test_invalid_illustration_inputs(data, field, value):
    args = dict(model="random", reach=10, population=100, cost=0.01, visit_value=1, budget=1)
    args[field] = value
    with pytest.raises(ValueError):
        dd.illustrate(data, **args)


def test_charts_preserve_points_and_saved_bounds(data):
    for rows, flags in [
        (dd.policy_rows(data), {}),
        (dd.sensitivity_rows(data, "all", 100), {"sensitivity": True}),
    ]:
        spec = charts.intervals(rows, **flags).to_dict()
        assert len(next(v for v in spec["datasets"].values() if "Lower" in v[0])) == len(rows)
        if flags:
            assert not any(layer["mark"]["type"] == "line" for layer in spec["layer"])


def test_minimal_deployment_closure_is_pinned_and_has_no_model_stack():
    requirements = [
        Requirement(s)
        for s in (ROOT / "app/requirements.txt").read_text().splitlines()
        if s and not s.startswith("#")
    ]
    pinned = {
        r.name.lower().replace("_", "-"): next(iter(r.specifier)).version for r in requirements
    }
    assert len(pinned) == len(requirements) == 37
    assert not set(pinned) & {"lightgbm", "duckdb", "scikit-learn", "mlflow", "matplotlib"}
    assert pinned["streamlit"] == "1.50.0"
    env = {
        "python_full_version": "3.12.14",
        "python_version": "3.12",
        "platform_system": "Linux",
        "sys_platform": "linux",
        "extra": "",
    }
    for r in requirements:
        assert (
            str(r.specifier).startswith("==") and metadata.version(r.name) == pinned[r.name.lower()]
        )
        for raw in metadata.requires(r.name) or []:
            child = Requirement(raw)
            if child.marker is None or child.marker.evaluate(env):
                name = child.name.lower().replace("_", "-")
                assert name in pinned and pinned[name] in child.specifier, (r.name, child)


def test_application_has_only_presentation_imports_and_no_execution_controls():
    allowed = {
        "sys",
        "pathlib",
        "dataclasses",
        "decimal",
        "portfolio",
        "pandas",
        "altair",
        "streamlit",
        "app",
    }
    forbidden_calls = {
        "file_uploader",
        "secrets",
        "read_parquet",
        "load_model",
        "outcomes",
        "train",
        "fit",
        "evaluate",
        "score_features",
        "production",
        "subprocess",
    }
    for path in (ROOT / "app").glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(x.name.split(".")[0] in allowed for x in node.names)
            if isinstance(node, ast.ImportFrom):
                assert node.module.split(".")[0] in allowed
            if isinstance(node, ast.Attribute):
                assert node.attr not in forbidden_calls, path


def test_headless_pages_controls_and_private_read_sentinels(monkeypatch):
    before = hashlib.sha256(dd.SNAPSHOT.read_bytes()).hexdigest()
    original = Path.open

    def guarded(path, *args, **kwargs):
        assert not any(
            p in str(path)
            for p in ("stage-b-private", "data/raw/", "data/processed/", "artifacts/", "mlruns/")
        ), str(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    # A deployment must not need any research/execution modules, even if installed.
    for name in (
        "lightgbm",
        "duckdb",
        "marketing_uplift",
        "production_adapter",
        "stage_b_activation",
        "stage_b_continuation",
        "execution_safeguards",
    ):
        monkeypatch.setitem(sys.modules, name, None)
    at = AppTest.from_file(str(ROOT / "app/streamlit_app.py"), default_timeout=20).run()
    assert not at.exception
    assert any(m.value == "4.8543%" for m in at.metric)
    for page in (
        "Policy comparisons",
        "Sensitivity explorer",
        "Budget illustration",
        "Models & limitations",
    ):
        at.radio(key="page").set_value(page).run()
        assert not at.exception
        assert "no targeting" in at.sidebar.success[0].value
    at.selectbox(key="evaluator").set_value("ipw").run()
    at.selectbox(key="propensity").set_value(0.9).run()
    at.selectbox(key="interval").set_value("pointwise").run()
    at.selectbox(key="uncertainty").set_value("stratified").run()
    assert not at.exception and at.warning
    at.radio(key="page").set_value("Policy comparisons").run()
    at.multiselect(key="policies").set_value([]).run()
    assert not at.exception and any("Select at least one" in x.value for x in at.info)
    at.radio(key="page").set_value("Budget illustration").run()
    at.selectbox(key="budget_policy").set_value("s_learner").run()
    at.number_input(key="budget_cap").set_value(0.0).run()
    assert not at.exception and at.error
    assert hashlib.sha256(dd.SNAPSHOT.read_bytes()).hexdigest() == before


def test_app_provenance_error_shows_no_private_details(tmp_path, monkeypatch):
    bad = tmp_path / "missing.json"
    monkeypatch.setattr(dd, "SNAPSHOT", bad)
    at = AppTest.from_file(str(ROOT / "app/streamlit_app.py"), default_timeout=20).run()
    assert not at.exception and len(at.error) == 1
    assert "provenance validation failed" in at.error[0].value
    assert str(bad) not in at.error[0].value
