"""Read-only evidence checks; never fit models or query sealed holdout outcomes."""

import json
import math
import os
import tomllib
from pathlib import Path

import lightgbm as lgb
import mlflow
import numpy as np
import pyarrow as pa
import pytest

from marketing_uplift.baselines import predict, protocol, snapshot
from marketing_uplift.data_contract import FEATURES, connection
from marketing_uplift.ingestion import file_sha256, parquet_path
from marketing_uplift.policy_metrics import MODELS, ranking, weights
from marketing_uplift.splits import get_member, verify_registry

pytestmark = pytest.mark.full_data
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def evidence(monkeypatch):
    monkeypatch.chdir(ROOT)
    config = tomllib.loads(Path("configs/project.toml").read_text())
    path = Path(os.environ.get("PHASE6_EVIDENCE", "reports/phase_6_metrics.json"))
    if not path.exists():
        path = Path("reports/phase_6_first_split.json")
    report = json.loads(path.read_text())
    registry = json.loads(Path("artifacts/splits.json").read_text())
    return config, report, registry


def test_protected_inputs_protocol_and_tracking(evidence):
    config, report, registry = evidence
    assert snapshot(config) == report["protected_inputs"]
    assert report["protected_inputs_unchanged"]
    assert protocol()[1] == report["protocol_sha256"]
    verify_registry(registry)
    assert len(report["splits"]) == (5 if report["status"] == "completed" else 1)
    mlflow.set_tracking_uri(Path(config["tracking"]["directory"]).resolve().as_uri())
    for s in report["splits"]:
        run = mlflow.get_run(s["mlflow_run_id"])
        assert run.info.status == "FINISHED"
        assert run.data.params["protocol_sha256"] == report["protocol_sha256"]
        assert s["models"]["response"]["training_rows"] == 8080205
        assert s["models"]["s_learner"]["training_rows"] == 9506122
        assert all(m["trees"] == 200 for m in s["models"].values())
        assert s["models"]["response"]["features"] == FEATURES
        assert s["models"]["s_learner"]["features"] == [*FEATURES, "__intervention_treatment"]


def test_saved_models_prediction_alignment_and_artifact_hashes(evidence):
    config, report, registry = evidence
    for s in report["splits"]:
        d = Path("artifacts/phase6") / report["protocol_sha256"] / str(s["seed"])
        spec = next(x for x in registry["development_splits"] if x["seed"] == s["seed"])
        ids = get_member(spec["validation"], registry["rows"])
        indices = np.linspace(0, len(ids) - 1, 97, dtype=int)
        with connection(config) as con:
            con.register("ids", pa.table({"row_id": ids[indices]}))
            con.read_parquet(str(parquet_path(config))).create_view("source")
            result = con.execute(
                "SELECT "
                + ",".join("p." + f for f in FEATURES)
                + " FROM source p JOIN ids USING(row_id) ORDER BY p.row_id"
            ).fetchnumpy()
        x = np.column_stack([result[f] for f in FEATURES])
        for name, sha in s["artifact_hashes"].items():
            assert file_sha256(d / name) == sha
        response = lgb.Booster(model_file=str(d / "response.txt"))
        sc = np.load(d / "response-scores.npy", mmap_mode="r")
        np.testing.assert_array_equal(predict(response, x), sc[indices])
        model = lgb.Booster(model_file=str(d / "s_learner.txt"))
        p1, p0 = np.load(d / "s-p1.npy", mmap_mode="r"), np.load(d / "s-p0.npy", mmap_mode="r")
        np.testing.assert_array_equal(predict(model, x, 1), p1[indices])
        np.testing.assert_array_equal(predict(model, x, 0), p0[indices])
        np.testing.assert_array_equal(p1 - p0, np.load(d / "s_learner-scores.npy"))


def test_policy_results_against_independent_row_aggregations(evidence):
    config, report, registry = evidence
    for s in report["splits"]:
        d = Path("artifacts/phase6") / report["protocol_sha256"] / str(s["seed"])
        spec = next(x for x in registry["development_splits"] if x["seed"] == s["seed"])
        ids = get_member(spec["validation"], registry["rows"])
        with connection(config) as con:
            con.register("ids", pa.table({"row_id": ids}))
            con.read_parquet(str(parquet_path(config))).create_view("source")
            data = con.execute(
                "SELECT treatment,visit FROM source JOIN ids USING(row_id) ORDER BY row_id"
            ).fetchnumpy()
        t, y = data["treatment"], data["visit"]
        assert len(t) == 2376531
        assert int(t.sum()) == 2020052
        assert int((t * y).sum()) == 98060
        assert int(((1 - t) * y).sum()) == 13618
        priorities = np.random.default_rng(s["seed"] + 1000000).random(len(ids))
        for name in MODELS:
            score = (
                priorities if name == "random" else np.load(d / f"{name}-scores.npy", mmap_mode="r")
            )
            order = ranking(score, priorities, ids)
            for e, scenario in s["evaluation"]["scenarios"].items():
                e = float(e)
                w = weights(t, y, e)
                base = np.mean((1 - t) * y / (1 - e))
                model = scenario["models"][name]
                # Independent trapezoid integration of the full cumulative curve.
                curve = np.r_[0, np.cumsum(w[order]) / len(t)]
                assert model["ipw_auuc"] == pytest.approx(
                    np.trapezoid(curve, dx=1 / len(t)), abs=1e-10
                )
                for p in model["policies"]:
                    selected = order[: math.ceil(p["reach"] * len(t))]
                    assert p["selected"] == len(selected)
                    assert p["treatment_n"] == int(t[selected].sum())
                    assert p["value"] == pytest.approx(base + w[selected].sum() / len(t), abs=1e-12)
                    assert p["gain_over_none"] == pytest.approx(
                        w[selected].sum() / len(t), abs=1e-12
                    )
