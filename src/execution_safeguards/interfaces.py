"""Synthetic-only array interfaces; no Parquet reader or real holdout access."""

import hashlib
import json
import os
from pathlib import Path

import numpy as np

from marketing_uplift.baselines import predict
from marketing_uplift.final_metrics import evaluate_arrays
from marketing_uplift.policy_metrics import ranking, reach_bins
from marketing_uplift.robust_metrics import MODELS

from .checkpoints import snapshot, verify_files
from .protocol import Denied, digest, file_hash

NAMES = ["response", "control", "s_learner"] + [
    f"nuisance-{fold}-{arm}" for fold in range(3) for arm in range(2)
]
FEATURES = [f"f{i}" for i in range(12)]


def array_sha(array):
    return digest(
        {
            "dtype": array.dtype.str,
            "shape": list(array.shape),
            "bytes_sha256": hashlib.sha256(array.tobytes()).hexdigest(),
        }
    )


class SyntheticModel:
    """Deterministic fixture predictor, never a substitute for a final fitted model."""

    def __init__(self, path):
        self.values = json.loads(Path(path).read_text())
        if self.values.get("synthetic_fixture_model") is not True:
            raise Denied("Only declared synthetic predictors are supported")

    def predict(self, x, **kwargs):
        if x.shape[1] != len(self.values["weights"]):
            raise Denied("Predictor feature contract")
        return 1 / (1 + np.exp(-(x @ np.array(self.values["weights"]) + self.values["bias"])))


def score_synthetic(ids, x, columns, model_paths, expected_hashes, settings, expected_ids_sha):
    if (
        columns != FEATURES
        or x.shape != (len(ids), 12)
        or len(ids) < 2
        or len(ids) > 4096
        or ids.dtype != np.dtype("uint64")
        or np.any(ids[1:] <= ids[:-1])
        or not np.isfinite(x).all()
        or array_sha(ids) != expected_ids_sha
        or set(model_paths) != set(NAMES)
    ):
        raise Denied("Synthetic feature/ID contract or alignment")
    p = {}
    for name in NAMES:
        path = Path(model_paths[name])
        if file_hash(path) != expected_hashes[name]:
            raise Denied("Changed model identity")
        model = SyntheticModel(path)
        if name == "s_learner":
            p["s0"], p["s1"] = predict(model, x, 0), predict(model, x, 1)
        else:
            p[name] = predict(model, x)
    p["m0"] = np.mean([p[f"nuisance-{fold}-0"] for fold in range(3)], axis=0)
    p["m1"] = np.mean([p[f"nuisance-{fold}-1"] for fold in range(3)], axis=0)
    priorities = np.random.default_rng(settings["random_rank_seed"]).random(len(ids))
    scores = {
        "random": priorities,
        "response": p["response"],
        "s_learner": p["s1"] - p["s0"],
        "t_learner": p["response"] - p["control"],
    }
    orders = {name: ranking(scores[name], priorities, ids) for name in MODELS}
    bins = np.array([reach_bins(orders[name]) for name in MODELS])
    memberships = np.array([[bins[j] < k for k in range(1, 6)] for j in range(4)])
    return {
        "ids": ids,
        "scores": np.array([scores[m] for m in MODELS]),
        "orders": np.array([orders[m] for m in MODELS]),
        "bins": bins,
        "memberships": memberships,
        "nuisance": np.array([p["m0"], p["m1"], p["s0"], p["s1"]]),
    }


def save_predictions(root, values, binding):
    root = Path(root)
    root.mkdir(exist_ok=False, parents=True)
    for name, array in values.items():
        with (root / f"{name}.npy").open("xb") as stream:
            np.save(stream, array, allow_pickle=False)
            stream.flush()
            os.fsync(stream.fileno())
    return snapshot(root, [f"{name}.npy" for name in values], binding)


def load_predictions(root, manifest, binding):
    if manifest["binding"] != binding:
        raise Denied("Checkpoint belongs to different receipt/lock")
    verify_files(root, manifest)
    names = {"ids", "scores", "orders", "bins", "memberships", "nuisance"}
    if set(manifest["files"]) != {f"{n}.npy" for n in names}:
        raise Denied("Incomplete prediction seal")
    return {n: np.load(Path(root) / f"{n}.npy", allow_pickle=False) for n in names}


def validate_predictions(sealed, expected_ids_sha=None):
    n = len(sealed["ids"])
    if (
        not 2 <= n <= 4096
        or sealed["scores"].shape != (4, n)
        or sealed["nuisance"].shape != (4, n)
        or sealed["memberships"].shape != (4, 5, n)
        or (expected_ids_sha is not None and array_sha(sealed["ids"]) != expected_ids_sha)
    ):
        raise Denied("Invalid sealed alignment/layout")
    scores = dict(zip(MODELS, sealed["scores"], strict=True))
    # Pure, unchanged kernel reconstructs ranks for its sufficient statistics. Verify
    # byte-identical agreement with the pre-outcome sealed decisions; never substitute.
    for j, name in enumerate(MODELS):
        order = ranking(scores[name], scores["random"], sealed["ids"])
        if (
            not np.array_equal(order, sealed["orders"][j])
            or not np.array_equal(reach_bins(order), sealed["bins"][j])
            or not np.array_equal(
                np.array([sealed["bins"][j] < k for k in range(1, 6)]), sealed["memberships"][j]
            )
        ):
            raise Denied("Sealed ranking/membership mismatch")
    return scores


def evaluate_synthetic(sealed, t, y, settings):
    scores = validate_predictions(sealed)
    result = evaluate_arrays(sealed["ids"], scores, (t, y, *sealed["nuisance"]), settings)
    if not np.array_equal(result["bins"], sealed["bins"]):
        raise Denied("Evaluation changed policy membership")
    return result
