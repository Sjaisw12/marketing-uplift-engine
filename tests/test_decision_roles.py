"""Auxiliary roles and sequential leakage contracts, without real data or training."""

import json
from contextlib import nullcontext
from types import SimpleNamespace

import numpy as np

from marketing_uplift import decisions
from marketing_uplift.decision_engine import apply, choose
from marketing_uplift.decision_metrics import evaluate
from marketing_uplift.robust_metrics import MODELS


def test_roles_are_balanced_outcome_blind_and_reconstructible():
    a = decisions.roles(1001, 42)
    assert (a == 0).sum() == 500 and (a == 1).sum() == 501
    np.testing.assert_array_equal(a, decisions.roles(1001, 42))
    assert not np.array_equal(a, decisions.roles(1001, 43))
    # API takes no outcome/feature input and never changes parent membership order.
    ids = np.arange(1001)
    np.testing.assert_array_equal(np.sort(np.r_[ids[a == 0], ids[a == 1]]), ids)


def test_pipeline_persists_decisions_and_applications_before_assessment_query(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    n, seed = 201, 42
    root = tmp_path / "private"
    d = root / str(seed)
    d.mkdir(parents=True)
    np.save(d / "roles.npy", decisions.roles(n, seed + 6000000))
    rng = np.random.default_rng(5)
    scores = {m: rng.random(n) for m in MODELS}
    probs = [rng.random(n) for _ in range(4)]
    t, y = rng.binomial(1, 0.85, n), rng.binomial(1, 0.2, n)
    events = []
    monkeypatch.setattr(decisions, "get_member", lambda *_: np.arange(n))
    monkeypatch.setattr(decisions, "file_sha256", lambda p: "synthetic-sha")
    monkeypatch.setattr(
        decisions,
        "inputs",
        lambda seed, ids, mask: ({m: a[mask] for m, a in scores.items()}, [a[mask] for a in probs]),
    )
    settings = dict(
        scenarios=[0.8, 0.825, 0.85, 0.875, 0.9],
        replicates=2000,
        batch_rows=31,
        role_seed_offset=6000000,
        minimum_control_visits=30,
        economics=[
            dict(name="toy", cost=".01", value="1", budget_per_record=".005", maximum_reach=".5")
        ],
    )

    def role(config, settings, seed, ids, allids, mask, label):
        if label == "assessment":
            assert (d / "recommendations.json").exists()
            assert (d / "assessment-applications.json").exists()
            sealed = json.loads((d / "recommendations.json").read_text())
            events.append(sealed)
        return evaluate(
            ids,
            {m: a[mask] for m, a in scores.items()},
            (t[mask], y[mask], *[a[mask] for a in probs]),
            settings["scenarios"],
            2000,
            seed,
        )

    monkeypatch.setattr(decisions, "evaluate_role", role)
    for name in (
        "set_tracking_uri",
        "set_experiment",
        "log_params",
        "log_dict",
        "log_artifact",
        "log_metrics",
    ):
        monkeypatch.setattr(decisions.mlflow, name, lambda *a, **k: None)
    monkeypatch.setattr(
        decisions.mlflow,
        "start_run",
        lambda **k: nullcontext(SimpleNamespace(info=SimpleNamespace(run_id="synthetic"))),
    )
    monkeypatch.setattr(decisions.subprocess, "check_output", lambda *a, **k: "synthetic-commit")
    result = decisions.one(
        {"experiment": {"split_registry": "unused"}, "tracking": {"directory": "mlruns"}},
        settings,
        "digest",
        {},
        {"rows": n},
        {"seed": seed, "validation": {}},
        root,
        {str(seed): {}},
    )
    assert events[0]["decisions"] == result["decisions"]
    # Even hostile assessment evidence cannot enter the pure decision/application interfaces.
    decision = result["decisions"]["toy"]
    assert (
        apply(decision, settings["economics"][0], 101)["reach_index"]
        == result["applications"]["toy"]["reach_index"]
    )
    assert "assessment" not in choose.__code__.co_varnames

    # Change every assessment label and rerun in a distinct output directory.
    # The sealed selection recommendation and outcome-blind application must be identical.
    labels = decisions.roles(n, seed + 6000000)
    y[labels == 1] = 1 - y[labels == 1]
    root = tmp_path / "second_private"
    d = root / str(seed)
    d.mkdir(parents=True)
    np.save(d / "roles.npy", labels)
    changed = decisions.one(
        {"experiment": {"split_registry": "unused"}, "tracking": {"directory": "mlruns"}},
        settings,
        "digest",
        {},
        {"rows": n},
        {"seed": seed, "validation": {}},
        root,
        {str(seed): {}},
    )
    assert changed["decisions"] == result["decisions"]
    for field in ("model", "reach_index", "ledger", "selected_ids_sha256"):
        assert changed["applications"]["toy"][field] == result["applications"]["toy"][field]
