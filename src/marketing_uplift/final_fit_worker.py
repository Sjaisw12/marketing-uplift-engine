"""One sequential development-only diagnostic refit per process."""

import gc
import hashlib
import json
import resource
import sys
import time
import tomllib
from pathlib import Path

import lightgbm as lgb
import numpy as np

from marketing_uplift.baselines import design, parameters, predict
from marketing_uplift.data_contract import FEATURES, ContractError, atomic_json
from marketing_uplift.final_access import check_development_ids
from marketing_uplift.ingestion import file_sha256
from marketing_uplift.splits import get_member


def ids_sha(ids):
    return hashlib.sha256(np.asarray(ids, dtype="<u8").tobytes()).hexdigest()


def fit_model(x, t, y, mask, recipe, seed, is_s=False):
    if x.shape != (len(y), 12) or not mask.any() or len(np.unique(y[mask])) != 2:
        raise ContractError("Invalid diagnostic model data/support")
    if is_s and not mask.all():
        raise ContractError("Final S recipe requires all development records")
    matrix = design(x, t) if is_s else x[mask]
    target = y if is_s else y[mask]
    names = [*FEATURES, "__intervention_treatment"] if is_s else FEATURES
    data = lgb.Dataset(matrix, label=target, feature_name=names, free_raw_data=True)
    model = lgb.train(parameters(recipe, seed), data, num_boost_round=recipe["rounds"])
    del data, matrix, target
    gc.collect()
    return model


def run(jobpath):
    job = json.loads(Path(jobpath).read_text())
    directory = Path(job["directory"])
    name = job["name"]
    resultpath = directory / f"{name}-fit.json"
    modelpath = directory / f"{name}.txt"
    if resultpath.exists() or modelpath.exists():
        raise ContractError("Worker refuses to overwrite any existing final model/receipt")
    config = tomllib.loads(Path("configs/project.toml").read_text())
    registry = json.loads(Path(config["experiment"]["split_registry"]).read_text())
    ids = get_member(registry["memberships"]["development"], registry["rows"])
    check_development_ids(ids, ids)
    if ids_sha(ids) != job["development_ids_sha256"]:
        raise ContractError("Worker development membership mismatch")
    cache = job["cache"]
    for filename, sha in cache.items():
        if file_sha256(directory / filename) != sha:
            raise ContractError("Worker development cache hash mismatch")
    x, t, y = [
        np.load(directory / f"development-{col}.npy", mmap_mode="r") for col in ("x", "t", "y")
    ]
    folds = np.load(directory / "nuisance-folds.npy", mmap_mode="r")
    mask = np.ones(len(t), dtype=bool) if job["arm"] is None else t == job["arm"]
    if job["excluded_fold"] is not None:
        mask &= folds != job["excluded_fold"]
    if (
        hashlib.sha256(mask.tobytes()).hexdigest() != job["fit_mask_sha256"]
        or ids_sha(ids[mask]) != job["fit_ids_sha256"]
    ):
        raise ContractError("Worker fit inclusion/exclusion mismatch")
    recipe = tomllib.loads(Path("configs/baselines.toml").read_text())
    if file_sha256(Path("configs/baselines.toml")) != job["recipe_sha256"]:
        raise ContractError("Worker frozen recipe mismatch")
    started = time.monotonic()
    model = fit_model(x, t, y, mask, recipe, job["seed"], job["arm"] is None)
    if model.feature_name() != job["features"] or model.num_trees() != recipe["rounds"]:
        raise ContractError("Final model feature/round contract failed")
    model.save_model(str(modelpath))
    probe = np.load(directory / "probe-positions.npy")
    loaded = lgb.Booster(model_file=str(modelpath))
    outputs = {}
    for intervention in (0, 1) if job["arm"] is None else (None,):
        p = predict(model, x[probe], intervention)
        np.testing.assert_array_equal(p, predict(loaded, x[probe], intervention))
        label = "p" if intervention is None else f"p{intervention}"
        predpath = directory / f"{name}-probe-{label}.npy"
        np.save(predpath, p)
        outputs[predpath.name] = file_sha256(predpath)
    if job["excluded_fold"] is not None:
        held = (t == job["arm"]) & (folds == job["excluded_fold"])
        assert not np.any(mask & held)
        # OOF correctness probe only: no training/validation performance selection.
        selected = np.flatnonzero(held)
        selected = selected[np.linspace(0, len(selected) - 1, 41, dtype=int)]
        hp = predict(model, x[selected])
        np.testing.assert_array_equal(hp, predict(loaded, x[selected]))
        path = directory / f"{name}-held-probe.npz"
        np.savez(path, positions=selected, prediction=hp)
        outputs[path.name] = file_sha256(path)
    result = {
        "job": job,
        "model_sha256": file_sha256(modelpath),
        "model_bytes": modelpath.stat().st_size,
        "trees": model.num_trees(),
        "feature_order": model.feature_name(),
        "probe_hashes": outputs,
        "reload_bit_identical": True,
        "elapsed_seconds": time.monotonic() - started,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    atomic_json(resultpath, result)
    return result


if __name__ == "__main__":
    result = run(sys.argv[1])
    print(
        json.dumps(
            {
                "model": result["job"]["name"],
                "seconds": result["elapsed_seconds"],
                "peak_rss_kib": result["peak_rss_kib"],
            }
        ),
        flush=True,
    )
