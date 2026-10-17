"""Bounded prediction/seal kernels, tested only with synthetic or development batches."""

import os
import shutil
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pyarrow as pa

from execution_safeguards.bundle import atomic_json
from execution_safeguards.checkpoints import snapshot, verify_files
from execution_safeguards.interfaces import NAMES
from execution_safeguards.protocol import Denied, file_hash
from marketing_uplift.baselines import predict
from marketing_uplift.data_contract import FEATURES
from marketing_uplift.final_metrics import evaluate_arrays
from marketing_uplift.policy_metrics import ranking, reach_bins
from marketing_uplift.robust_metrics import MODELS

from .parquet import ids_sha


def load_models(root, plan):
    models = {}
    if set(plan["models"]) != set(NAMES):
        raise Denied("Exactly nine frozen models required")
    for name in NAMES:
        path = Path(root) / plan["model_root"] / f"{name}.txt"
        expected = plan["models"][name]
        if file_hash(path) != expected["sha256"]:
            raise Denied("Frozen model bytes changed")
        model = lgb.Booster(model_file=str(path))
        if model.feature_name() != expected["features"] or model.num_trees() != 200:
            raise Denied("Frozen model feature/recipe contract changed")
        models[name] = model
    return models


def score_batches(batches, ids, models, root, settings, binding, min_free_bytes=8589934592):
    n = len(ids)
    root = Path(root)
    if not 2 <= n <= 2096939 or ids.dtype != np.dtype("<u8") or np.any(ids[1:] <= ids[:-1]):
        raise Denied("Unexpected cohort size/ID mapping")
    if set(models) != set(NAMES):
        raise Denied("Missing frozen model")
    # 128 bytes/record for arrays, plus explicit NumPy/header margin.
    ancestor = root.parent
    while not ancestor.exists():
        ancestor = ancestor.parent
    if shutil.disk_usage(ancestor).free < min_free_bytes + 128 * n + 1048576:
        raise Denied("Insufficient disk for bounded prediction artifacts")
    root.mkdir(parents=True, exist_ok=False)
    shapes = {
        "ids": (np.uint64, (n,)),
        "scores": (np.float64, (4, n)),
        "orders": (np.int64, (4, n)),
        "bins": (np.uint8, (4, n)),
        "memberships": (np.bool_, (4, 5, n)),
        "nuisance": (np.float64, (4, n)),
    }
    arrays = {
        k: np.lib.format.open_memmap(root / f"{k}.npy", mode="w+", dtype=d, shape=s)
        for k, (d, s) in shapes.items()
    }
    offset = 0
    for batch in batches:
        if batch.schema.names != ["row_id", *FEATURES] or list(batch.schema.types) != [
            pa.uint64(),
            *[pa.float64()] * 12,
        ]:
            raise Denied("Only source ID and exactly f0-f11 may enter prediction")
        size = len(batch)
        sl = slice(offset, offset + size)
        if not np.array_equal(batch.column(0).to_numpy(), ids[sl]):
            raise Denied("Scoring row alignment mismatch")
        x = np.column_stack([batch.column(j + 1).to_numpy() for j in range(12)])
        if x.shape != (size, 12) or not np.isfinite(x).all():
            raise Denied("Invalid user features")
        response = predict(models["response"], x)
        control = predict(models["control"], x)
        s0, s1 = predict(models["s_learner"], x, 0), predict(models["s_learner"], x, 1)
        # Preserve Stage A three-model averaging order exactly.
        m0 = np.mean([predict(models[f"nuisance-{k}-0"], x) for k in range(3)], axis=0)
        m1 = np.mean([predict(models[f"nuisance-{k}-1"], x) for k in range(3)], axis=0)
        arrays["ids"][sl] = ids[sl]
        arrays["scores"][1:, sl] = [response, s1 - s0, response - control]
        arrays["nuisance"][:, sl] = [m0, m1, s0, s1]
        offset += size
    if offset != n:
        raise Denied("Incomplete prediction stream; partial files require review")
    arrays["scores"][0] = np.random.default_rng(settings["random_rank_seed"]).random(n)
    for j in range(4):
        order = ranking(arrays["scores"][j], arrays["scores"][0], ids)
        arrays["orders"][j] = order
        arrays["bins"][j] = reach_bins(order)
        for k in range(1, 6):
            arrays["memberships"][j, k - 1] = arrays["bins"][j] < k
    for name, array in arrays.items():
        array.flush()
        with (root / f"{name}.npy").open("rb") as stream:
            os.fsync(stream.fileno())
    manifest = snapshot(root, [f"{k}.npy" for k in shapes], binding)
    atomic_json(root / "prediction-seal.json", manifest)
    return manifest


def read_seal(root, manifest, binding, expected_ids_sha):
    if manifest["binding"] != binding:
        raise Denied("Seal belongs to another model/policy/cohort/receipt")
    # Legacy generic byte verifier expects the canonical three-field snapshot schema.
    verify_files(root, {k: manifest[k] for k in ("schema", "binding", "files")})
    names = {"ids", "scores", "orders", "bins", "memberships", "nuisance"}
    if set(manifest["files"]) != {f"{k}.npy" for k in names}:
        raise Denied("Incomplete policy seal")
    a = {k: np.load(Path(root) / f"{k}.npy", mmap_mode="r", allow_pickle=False) for k in names}
    n = len(a["ids"])
    if (
        not 2 <= n <= 2096939
        or a["ids"].ndim != 1
        or a["ids"].dtype != np.dtype("<u8")
        or np.any(a["ids"][1:] <= a["ids"][:-1])
        or ids_sha(a["ids"]) != expected_ids_sha
    ):
        raise Denied("Sealed source IDs changed")
    for name, shape in {
        "scores": (4, n),
        "orders": (4, n),
        "bins": (4, n),
        "memberships": (4, 5, n),
        "nuisance": (4, n),
    }.items():
        expected_dtype = {
            "scores": np.float64,
            "orders": np.int64,
            "bins": np.uint8,
            "memberships": np.bool_,
            "nuisance": np.float64,
        }[name]
        if a[name].shape != shape or a[name].dtype != np.dtype(expected_dtype):
            raise Denied("Sealed array layout changed")
        if name in ("scores", "nuisance") and not np.isfinite(a[name]).all():
            raise Denied("Nonfinite sealed prediction")
    for j in range(4):
        order = ranking(a["scores"][j], a["scores"][0], a["ids"])
        if not np.array_equal(order, a["orders"][j]) or not np.array_equal(
            reach_bins(order), a["bins"][j]
        ):
            raise Denied("Sealed ranking changed")
        for k in range(1, 6):
            if not np.array_equal(a["memberships"][j, k - 1], a["bins"][j] < k):
                raise Denied("Sealed membership changed")
    return a


def evaluate_sealed(outcome_batches, root, manifest, binding, expected_ids_sha, settings):
    """Array/kernel evaluation only; real holdout outcome entry point remains denied."""
    sealed = read_seal(root, manifest, binding, expected_ids_sha)
    n = len(sealed["ids"])
    t = np.empty(n, dtype=np.uint8)
    y = np.empty(n, dtype=np.uint8)
    offset = 0
    for batch in outcome_batches:
        if (
            batch.schema.names != ["row_id", "treatment", "visit"]
            or list(batch.schema.types) != [pa.uint64(), pa.uint8(), pa.uint8()]
            or any(c.null_count for c in batch.columns)
            or not np.isin(batch.column(1).to_numpy(), [0, 1]).all()
            or not np.isin(batch.column(2).to_numpy(), [0, 1]).all()
        ):
            raise Denied("Outcome projection/values changed; no coercion")
        size = len(batch)
        sl = slice(offset, offset + size)
        if not np.array_equal(batch.column(0).to_numpy(), sealed["ids"][sl]):
            raise Denied("Outcome/decision alignment mismatch")
        t[sl] = batch.column(1).to_numpy()
        y[sl] = batch.column(2).to_numpy()
        offset += size
    if offset != n:
        raise Denied("Incomplete outcomes; no partial evaluation")
    scores = dict(zip(MODELS, sealed["scores"], strict=True))
    result = evaluate_arrays(sealed["ids"], scores, (t, y, *sealed["nuisance"]), settings)
    if not np.array_equal(result["bins"], sealed["bins"]):
        raise Denied("Evaluator changed policy decisions")
    return result
