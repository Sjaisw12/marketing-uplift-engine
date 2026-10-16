"""Development-only verification of Stage A fits and final diagnostic numerics."""

import hashlib
import json
from pathlib import Path
from urllib.parse import unquote, urlparse

import lightgbm as lgb
import mlflow
import numpy as np

from marketing_uplift.baselines import predict
from marketing_uplift.data_contract import FEATURES, ContractError
from marketing_uplift.final_access import development_batches
from marketing_uplift.final_fit_worker import ids_sha
from marketing_uplift.final_metrics import coefficient, evaluate_arrays
from marketing_uplift.final_stage_a import protocol, verify_lock
from marketing_uplift.ingestion import file_sha256
from marketing_uplift.robust_metrics import MODELS
from marketing_uplift.splits import get_member


def row_reference(bins, arrays, keys):
    """Independent explicit row formulas for SMALL permitted fixtures/probes."""
    t, y, m0, m1, s0, s1 = arrays
    columns = []
    for method, e in keys:
        if method == "ipw":
            h0 = (1 - t) * y / (1 - e)
            z = t * y / e - h0
        else:
            a, b = (m0, m1) if method == "dr" else (s0, s1)
            h0 = a + (1 - t) * (y - a) / (1 - e)
            z = b - a + t * (y - b) / e - (1 - t) * (y - a) / (1 - e)
        columns.append(h0)
        columns.extend([(bins[m] == k) * z for m in range(4) for k in range(6)])
    return np.column_stack(columns)


def check_numerics(result, arrays):
    h = row_reference(result["bins"], arrays, result["keys"])
    mean = h.mean(axis=0)
    cov = np.cov(h, rowvar=False, ddof=1) / len(h)
    np.testing.assert_allclose(result["point"], mean, atol=2e-13, rtol=0)
    np.testing.assert_allclose(result["covariance"], cov, atol=2e-13, rtol=0)
    strat_cov = np.zeros_like(cov)
    t, y = arrays[:2]
    for j in range(4):
        mask = 2 * t + y == j
        n = int(mask.sum())
        if n >= 2:
            strat_cov += (n / len(h)) ** 2 * np.cov(h[mask], rowvar=False, ddof=1) / n
    if result["stratified_covariance"] is not None:
        np.testing.assert_allclose(result["stratified_covariance"], strat_cov, atol=2e-13, rtol=0)
    # Baseline + gain equals direct IPW/DR policy value, rather than a zero visit rate.
    c = coefficient(0, "s_learner", 1, baseline=True)
    np.testing.assert_allclose(c @ result["point"], (h @ c).mean(), atol=2e-13)
    return {
        "maximum_mean_error": float(np.max(np.abs(mean - result["point"]))),
        "maximum_covariance_error": float(np.max(np.abs(cov - result["covariance"]))),
        "maximum_stratified_covariance_error": float(
            np.max(np.abs(strat_cov - result["stratified_covariance"]))
        )
        if result["stratified_covariance"] is not None
        else None,
        "coordinates": h.shape[1],
        "family_size": len(result["family"]),
    }


def verify(config, report):
    receipt = verify_lock(config, report)
    settings, sha, _ = protocol()
    root = Path("artifacts/phase9") / sha
    registry = json.loads(Path(config["experiment"]["split_registry"]).read_text())
    ids = get_member(registry["memberships"]["development"], registry["rows"])
    t = np.load(root / "development-t.npy", mmap_mode="r")
    y = np.load(root / "development-y.npy", mmap_mode="r")
    x = np.load(root / "development-x.npy", mmap_mode="r")
    folds = np.load(root / "nuisance-folds.npy", mmap_mode="r")
    expected = np.empty(len(ids), dtype=np.uint8)
    expected[np.random.default_rng(settings["nuisance_fold_seed"]).permutation(len(ids))] = (
        np.arange(len(ids)) % 3
    )
    np.testing.assert_array_equal(folds, expected)
    positions = np.load(root / "probe-positions.npy")
    raw = []
    for batch in development_batches(
        config, ids[positions], ["row_id", *FEATURES, "treatment", "visit"]
    ):
        raw.append(batch)
    import pyarrow as pa

    table = pa.Table.from_batches(raw)
    np.testing.assert_array_equal(table.column(0).to_numpy(), ids[positions])
    for j in range(12):
        np.testing.assert_array_equal(table.column(j + 1).to_numpy(), x[positions, j])
    np.testing.assert_array_equal(table.column(13).to_numpy(), t[positions])
    np.testing.assert_array_equal(table.column(14).to_numpy(), y[positions])
    probabilities = {}
    for fit in report["model_manifest"]["models"]:
        job = fit["job"]
        mask = np.ones(len(ids), dtype=bool) if job["arm"] is None else t == job["arm"]
        if job["excluded_fold"] is not None:
            mask &= folds != job["excluded_fold"]
        assert int(mask.sum()) == job["fit_rows"]
        assert int(y[mask].sum()) == job["fit_visits"]
        assert ids_sha(ids[mask]) == job["fit_ids_sha256"]
        assert hashlib.sha256(mask.tobytes()).hexdigest() == job["fit_mask_sha256"]
        model = lgb.Booster(model_file=str(root / f"{job['name']}.txt"))
        assert model.feature_name() == job["features"] and model.num_trees() == 200
        for intervention in (0, 1) if job["arm"] is None else (None,):
            label = "p" if intervention is None else f"p{intervention}"
            saved = np.load(root / f"{job['name']}-probe-{label}.npy")
            np.testing.assert_array_equal(saved, predict(model, x[positions], intervention))
            probabilities[(job["name"], label)] = saved
        if job["excluded_fold"] is not None:
            with np.load(root / f"{job['name']}-held-probe.npz") as held:
                p = held["positions"]
                assert not mask[p].any()
                assert np.all(folds[p] == job["excluded_fold"])
                np.testing.assert_array_equal(held["prediction"], predict(model, x[p]))
    arrays = (
        t[positions],
        y[positions],
        np.mean([probabilities[(f"nuisance-{k}-0", "p")] for k in range(3)], axis=0),
        np.mean([probabilities[(f"nuisance-{k}-1", "p")] for k in range(3)], axis=0),
        probabilities[("s_learner", "p0")],
        probabilities[("s_learner", "p1")],
    )
    priorities = np.random.default_rng(settings["random_rank_seed"]).random(len(positions))
    scores = {
        "random": priorities,
        "response": probabilities[("response", "p")],
        "s_learner": arrays[5] - arrays[4],
        "t_learner": probabilities[("response", "p")] - probabilities[("control", "p")],
    }
    assert list(scores) == list(MODELS)
    evaluation = evaluate_arrays(ids[positions], scores, arrays, settings)
    numerical = check_numerics(evaluation, arrays)
    mlflow.set_tracking_uri(Path(config["tracking"]["directory"]).resolve().as_uri())
    run = mlflow.get_run(report["mlflow_run_id"])
    assert run.info.status == "FINISHED"
    artifacts = Path(unquote(urlparse(run.info.artifact_uri).path))
    for fit in report["model_manifest"]["models"]:
        assert (
            file_sha256(artifacts / "models" / f"{fit['job']['name']}.txt") == fit["model_sha256"]
        )
    assert json.loads((artifacts / "model-manifest.json").read_text()) == report["model_manifest"]
    assert json.loads((artifacts / "lock.json").read_text()) == report["lock"]
    if any(Path("artifacts/phase9").rglob("*holdout*.npy")):
        raise ContractError("Unexpected holdout prediction artifact in Stage A")
    return {
        **receipt,
        "development_probe_rows": len(positions),
        "probe_is_correctness_not_out_of_sample_performance": True,
        "numerical_reference": numerical,
        "no_holdout_access": True,
    }
