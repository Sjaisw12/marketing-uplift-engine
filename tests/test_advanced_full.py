"""Read-only real-data Phase 7 gates; no training or holdout outcome access."""

import hashlib
import json
import os
import tomllib
from pathlib import Path
from urllib.parse import unquote, urlparse

import lightgbm as lgb
import mlflow
import numpy as np
import pyarrow as pa
import pytest

from marketing_uplift.advanced import nuisance_folds, protected, protocol
from marketing_uplift.baselines import predict
from marketing_uplift.data_contract import FEATURES, connection
from marketing_uplift.ingestion import file_sha256, parquet_path
from marketing_uplift.policy_metrics import ranking
from marketing_uplift.splits import get_member, verify_registry

pytestmark = pytest.mark.full_data
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def actual(monkeypatch):
    monkeypatch.chdir(ROOT)
    config = tomllib.loads(Path("configs/project.toml").read_text())
    path = Path(os.environ.get("PHASE7_EVIDENCE", "reports/phase_7_metrics.json"))
    if not path.exists():
        path = Path("reports/phase_7_first_split.json")
    report = json.loads(path.read_text())
    registry = json.loads(Path("artifacts/splits.json").read_text())
    old = json.loads(Path("reports/phase_6_metrics.json").read_text())
    return config, report, registry, old


def source_rows(config, ids, columns):
    with connection(config) as con:
        con.register("ids", pa.table({"row_id": ids}))
        con.read_parquet(str(parquet_path(config))).create_view("source")
        return con.execute(
            "SELECT "
            + ",".join("p." + c for c in columns)
            + " FROM source p JOIN ids USING(row_id) ORDER BY p.row_id"
        ).fetchnumpy()


def test_preservation_protocol_folds_and_mlflow(actual):
    config, report, registry, _ = actual
    assert protected(config) == report["protected_before"]
    assert report["protected_unchanged"]
    assert protocol()[1] == report["protocol_sha256"]
    verify_registry(registry)
    root = Path("artifacts/phase7") / report["protocol_sha256"]
    frozen = json.loads((root / "frozen-folds.json").read_text())
    for spec in registry["development_splits"]:
        foldpath = root / str(spec["seed"]) / "nuisance-folds.npy"
        assert file_sha256(foldpath) == frozen[str(spec["seed"])]["sha256"]
        np.testing.assert_array_equal(
            np.load(foldpath), nuisance_folds(spec["train"]["rows"], spec["seed"] + 3000000)
        )
    for s in report["splits"]:
        d = root / str(s["seed"])
        for name, sha in s["artifact_hashes"].items():
            assert file_sha256(d / name) == sha
        run = mlflow.get_run(s["mlflow_run_id"])
        assert run.info.status == "FINISHED"
        assert run.data.params["protocol_sha256"] == report["protocol_sha256"]
        artifacts = Path(unquote(urlparse(run.info.artifact_uri).path))
        for name, sha in s["artifact_hashes"].items():
            assert file_sha256(artifacts / "private_artifacts" / name) == sha
        for name in ("result.json", "provenance.json", "model_recipe.json"):
            assert (artifacts / name).exists()
        assert s["evaluation"]["simultaneous_family_size"] == 10
        assert s["evaluation"]["multiplier_replicates"] == 2000
        assert len(s["models"]) == 7
        assert all(m["features"] == FEATURES and m["trees"] == 200 for m in s["models"])
        assert s["vector_overlap"]["development_rows_in_repeated_vectors"] == 2151328
        assert 0 < s["vector_overlap"]["validation_rows_matching_training"] < 2376531


def test_model_reload_alignment_and_nuisance_exclusion(actual):
    config, report, registry, old = actual
    for s in report["splits"]:
        spec = next(x for x in registry["development_splits"] if x["seed"] == s["seed"])
        d = Path("artifacts/phase7") / report["protocol_sha256"] / str(s["seed"])
        val = get_member(spec["validation"], registry["rows"])
        train = get_member(spec["train"], registry["rows"])
        positions = np.linspace(0, len(val) - 1, 97, dtype=int)
        raw = source_rows(config, val[positions], FEATURES)
        x = np.column_stack([raw[f] for f in FEATURES])
        model = lgb.Booster(model_file=str(d / "control.txt"))
        np.testing.assert_array_equal(
            predict(model, x), np.load(d / "t-control.npy", mmap_mode="r")[positions]
        )
        olddir = Path("artifacts/phase6") / old["protocol_sha256"] / str(s["seed"])
        np.testing.assert_array_equal(
            np.load(d / "t-scores.npy"),
            np.load(olddir / "response-scores.npy") - np.load(d / "t-control.npy"),
        )
        t = source_rows(config, train, ["treatment"])["treatment"]
        folds = np.load(d / "nuisance-folds.npy", mmap_mode="r")
        oof = np.load(d / "oof.npy", mmap_mode="r")
        for arm in (0, 1):
            mean = np.zeros(len(val))
            for k in range(3):
                pred = np.load(d / f"nuisance-{k}-{arm}.npy", mmap_mode="r")
                mean += pred / 3
                model = lgb.Booster(model_file=str(d / f"nuisance-{k}-{arm}.txt"))
                np.testing.assert_array_equal(predict(model, x), pred[positions])
                mask = (t == arm) & (folds != k)
                recorded = s["fold_manifest"]["folds"][k]["arms"][arm]
                assert hashlib.sha256(mask.tobytes()).hexdigest() == recorded["fit_mask_sha256"]
                assert int(mask.sum()) == recorded["fit_rows"]
                held = np.flatnonzero((t == arm) & (folds == k))
                chosen = held[np.linspace(0, len(held) - 1, 41, dtype=int)]
                assert not mask[chosen].any()
                raw = source_rows(config, train[chosen], FEATURES)
                hx = np.column_stack([raw[f] for f in FEATURES])
                np.testing.assert_array_equal(predict(model, hx), oof[chosen])
            np.testing.assert_array_equal(mean, np.load(d / f"dr-m{arm}.npy"))


def test_formulas_pairing_support_and_phase6_point_reproduction(actual):
    config, report, registry, old = actual
    names = ("random", "response", "s_learner", "t_learner")
    for s in report["splits"]:
        spec = next(x for x in registry["development_splits"] if x["seed"] == s["seed"])
        ids = get_member(spec["validation"], registry["rows"])
        d = Path("artifacts/phase7") / report["protocol_sha256"] / str(s["seed"])
        od = Path("artifacts/phase6") / old["protocol_sha256"] / str(s["seed"])
        raw = source_rows(config, ids, ["treatment", "visit"])
        t, y = raw["treatment"], raw["visit"]
        m0, m1 = np.load(d / "dr-m0.npy"), np.load(d / "dr-m1.npy")
        priorities = np.random.default_rng(s["seed"] + 1000000).random(len(ids))
        orders = {
            name: ranking(
                priorities
                if name == "random"
                else np.load(
                    (d / "t-scores.npy") if name == "t_learner" else od / f"{name}-scores.npy"
                ),
                priorities,
                ids,
            )
            for name in names
        }
        masks = {
            name: [
                np.isin(np.arange(len(ids)), order[: int(np.ceil(q * len(ids)))])
                for q in (0.1, 0.2, 0.3, 0.4, 0.5)
            ]
            for name, order in orders.items()
        }
        osplit = next(x for x in old["splits"] if x["seed"] == s["seed"])
        for method in ("ipw", "dr"):
            for e, scenario in s["evaluation"]["estimates"][method].items():
                p = float(e)
                h0 = (1 - t) * y / (1 - p) if method == "ipw" else m0 + (1 - t) * (y - m0) / (1 - p)
                z = (
                    t * y / p - (1 - t) * y / (1 - p)
                    if method == "ipw"
                    else m1 - m0 + t * (y - m1) / p - (1 - t) * (y - m0) / (1 - p)
                )
                assert scenario["anchors"]["none"]["estimate"] == pytest.approx(
                    h0.mean(), abs=1e-12
                )
                for name in names:
                    if method == "ipw":
                        curve = np.r_[0.0, np.cumsum(z[orders[name]]) / len(y)]
                        area = float(np.trapezoid(curve, dx=1 / len(y)))
                        assert scenario["models"][name]["ipw_auuc"] == pytest.approx(
                            area, abs=1e-10
                        )
                        assert scenario["models"][name]["ipw_qini_area"] == pytest.approx(
                            area - z.mean() / 2, abs=1e-10
                        )
                    for k, row in enumerate(scenario["models"][name]["policies"]):
                        mask = masks[name][k]
                        assert row["value"]["estimate"] == pytest.approx(
                            np.mean(h0 + mask * z), abs=1e-12
                        )
                        assert row["gain_over_none"]["estimate"] == pytest.approx(
                            np.mean(mask * z), abs=1e-12
                        )
                        if method == "ipw" and name != "t_learner":
                            assert row["value"]["estimate"] == pytest.approx(
                                osplit["evaluation"]["scenarios"][e]["models"][name]["policies"][k][
                                    "value"
                                ],
                                abs=1e-12,
                            )
                        if name == "t_learner":
                            paired = (mask.astype(int) - masks["s_learner"][k]) * z
                            actual = row["paired"]["s_learner"]
                            assert actual["estimate"] == pytest.approx(paired.mean(), abs=1e-12)
                            assert actual["standard_error"] == pytest.approx(
                                paired.std(ddof=1) / np.sqrt(len(y)), abs=1e-11
                            )
                assert s["evaluation"]["support"]["t_learner"]["cumulative"][0]["records"] == int(
                    np.ceil(0.1 * len(y))
                )
