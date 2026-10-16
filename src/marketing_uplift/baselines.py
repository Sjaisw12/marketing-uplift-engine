"""Development-only fixed LightGBM baselines; private artifacts, aggregate reports."""

import gc
import hashlib
import json
import resource
import subprocess
import time
import tomllib
from pathlib import Path

import lightgbm as lgb
import mlflow
import numpy as np
import pyarrow as pa
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score

from marketing_uplift.data_contract import FEATURES, ContractError, atomic_json, connection, now
from marketing_uplift.development_ate import analysis_snapshot
from marketing_uplift.features import assert_feature_columns
from marketing_uplift.ingestion import file_sha256, parquet_path
from marketing_uplift.policy_metrics import evaluate, ranking
from marketing_uplift.splits import get_member, split

RECIPE = Path("configs/baselines.toml")


def snapshot(config):
    result = analysis_snapshot(config)
    for name in ("development_ate.json", "development_ate.md", "phase_5_development_ate.md"):
        p = Path("reports") / name
        result[str(p)] = {"bytes": p.stat().st_size, "sha256": file_sha256(p)}
    return result


def protocol():
    with RECIPE.open("rb") as f:
        recipe = tomllib.load(f)
    paths = [
        RECIPE,
        Path("docs/PHASE6_PROTOCOL.md"),
        Path(__file__),
        Path(__file__).with_name("policy_metrics.py"),
        Path("uv.lock"),
    ]
    hashes = {str(p): file_sha256(p) for p in paths}
    digest = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    return recipe, digest, hashes


def extract(config, member, total, directory, role):
    """Join only explicit frozen training/validation IDs; materialize in canonical order."""
    ids = get_member(member, total)
    n = len(ids)
    x = np.lib.format.open_memmap(
        directory / f"{role}-x.npy", mode="w+", dtype="float64", shape=(n, 12)
    )
    t = np.lib.format.open_memmap(directory / f"{role}-t.npy", mode="w+", dtype="uint8", shape=(n,))
    y = np.lib.format.open_memmap(directory / f"{role}-y.npy", mode="w+", dtype="uint8", shape=(n,))
    with connection(config) as con:
        con.register("selected_ids", pa.table({"row_id": ids}))
        con.read_parquet(str(parquet_path(config))).create_view("source")
        columns = ",".join("p." + c for c in ["row_id", *FEATURES, "treatment", "visit"])
        reader = con.execute(
            f"SELECT {columns} FROM source p JOIN selected_ids USING(row_id) ORDER BY row_id"
        ).fetch_record_batch(config["resources"]["batch_rows"])
        start = 0
        for batch in reader:
            end = start + batch.num_rows
            if not np.array_equal(batch.column(0).to_numpy(), ids[start:end]):
                raise ContractError("Extracted row-to-ID alignment failed")
            for j in range(12):
                x[start:end, j] = batch.column(j + 1).to_numpy()
            t[start:end] = batch.column(13).to_numpy()
            y[start:end] = batch.column(14).to_numpy()
            start = end
        if (
            start != n
            or not np.isfinite(x).all()
            or not np.isin(t, [0, 1]).all()
            or not np.isin(y, [0, 1]).all()
        ):
            raise ContractError("Incomplete or invalid model input; no coercion permitted")
    x.flush()
    t.flush()
    y.flush()
    return x, t, y, ids


def parameters(recipe, seed):
    return {
        "objective": "binary",
        "metric": "binary_logloss",
        "boosting_type": "gbdt",
        **{
            k: recipe[k]
            for k in (
                "learning_rate",
                "num_leaves",
                "min_data_in_leaf",
                "max_bin",
                "bin_construct_sample_cnt",
                "num_threads",
            )
        },
        "deterministic": True,
        "force_col_wise": True,
        "histogram_pool_size": 256,
        "feature_fraction": 1.0,
        "bagging_fraction": 1.0,
        "bagging_freq": 0,
        "seed": seed,
        "data_random_seed": seed,
        "feature_fraction_seed": seed,
        "bagging_seed": seed,
        "verbosity": -1,
    }


def design(x, treatment=None):
    assert_feature_columns(FEATURES if x.shape[1] == 12 else [])
    if treatment is None:
        return x
    if np.ndim(treatment) == 0:
        treatment = np.full(len(x), treatment)
    if len(treatment) != len(x) or not np.isin(treatment, [0, 1]).all():
        raise ContractError("Invalid separately supplied intervention")
    return np.column_stack((x, treatment))


def predict(model, x, intervention=None, batch=65536):
    out = np.empty(len(x))
    for start in range(0, len(x), batch):
        end = min(start + batch, len(x))
        out[start:end] = model.predict(design(x[start:end], intervention), num_threads=2)
    if not np.isfinite(out).all() or np.any((out < 0) | (out > 1)):
        raise ContractError("Invalid predicted probabilities")
    return out


def diagnostics(y, p):
    return {
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "brier": float(brier_score_loss(y, p)),
        "roc_auc": float(roc_auc_score(y, p)),
        "average_precision": float(average_precision_score(y, p)),
    }


def run_one(config, recipe, digest, hashes, registry, spec, root):
    seed = spec["seed"]
    directory = root / str(seed)
    output = directory / "result.json"
    provenance = {
        "protocol_sha256": digest,
        "registry_sha256": file_sha256(Path(config["experiment"]["split_registry"])),
        "train": spec["train"],
        "validation": spec["validation"],
        "source": registry["source"],
    }
    if output.exists():
        old = json.loads(output.read_text())
        if old["provenance"] != provenance:
            raise ContractError("Resume provenance mismatch")
        for name, sha in old["artifact_hashes"].items():
            if file_sha256(directory / name) != sha:
                raise ContractError("Resume model/prediction artifact mismatch")
        return old
    directory.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    x, t, y, _ = extract(config, spec["train"], registry["rows"], directory, "train")
    vx, vt, vy, ids = extract(config, spec["validation"], registry["rows"], directory, "validation")
    gc.collect()
    priorities = np.random.default_rng(seed + recipe["random_seed_offset"]).random(len(ids))
    orders = {"random": ranking(priorities, priorities, ids)}
    results = {"seed": seed, "provenance": provenance, "predictive": {}, "models": {}}
    mlflow.set_tracking_uri(Path(config["tracking"]["directory"]).resolve().as_uri())
    mlflow.set_experiment(config["tracking"]["experiment_name"])
    with mlflow.start_run(run_name=f"phase6-{seed}") as run:
        results["mlflow_run_id"] = run.info.run_id
        mlflow.log_params(
            {
                **recipe,
                "split_seed": seed,
                "protocol_sha256": digest,
                "lightgbm_version": lgb.__version__,
            }
        )
        mlflow.log_dict(
            {
                **provenance,
                "protocol_files": hashes,
                "git_commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
            },
            "provenance.json",
        )
        for name in ("response", "s_learner"):
            then = time.monotonic()
            if name == "response":
                mask = t == 1
                matrix, target = design(x[mask]), y[mask]
                columns = FEATURES
            else:
                matrix, target = design(x, t), y
                columns = [*FEATURES, "__intervention_treatment"]
            dataset = lgb.Dataset(matrix, label=target, feature_name=columns, free_raw_data=True)
            model = lgb.train(parameters(recipe, seed), dataset, num_boost_round=recipe["rounds"])
            del dataset, matrix, target
            gc.collect()
            model.save_model(str(directory / f"{name}.txt"))
            if name == "response":
                score = predict(model, vx)
                results["predictive"][name] = diagnostics(vy[vt == 1], score[vt == 1])
            else:
                p1, p0 = predict(model, vx, 1), predict(model, vx, 0)
                score = p1 - p0
                results["predictive"][name] = diagnostics(vy, np.where(vt == 1, p1, p0))
                np.save(directory / "s-p1.npy", p1)
                np.save(directory / "s-p0.npy", p0)
            np.save(directory / f"{name}-scores.npy", score)
            orders[name] = ranking(score, priorities, ids)
            results["models"][name] = {
                "seconds": time.monotonic() - then,
                "training_rows": int((t == 1).sum()) if name == "response" else len(t),
                "trees": model.num_trees(),
                "features": model.feature_name(),
            }
            mlflow.log_metrics({f"{name}_{k}": v for k, v in results["predictive"][name].items()})
            mlflow.log_artifact(str(directory / f"{name}.txt"), "models")
            del model, score
            gc.collect()
        results["evaluation"] = evaluate(
            vt,
            vy,
            orders,
            [recipe["reference_propensity"], *recipe["sensitivity_propensities"]],
            recipe["bootstrap_replicates"],
            seed + recipe["bootstrap_seed_offset"],
        )
        results["validation_rows"] = len(vy)
        results["validation_treatment_n"] = int(vt.sum())
        results["validation_control_n"] = int((1 - vt).sum())
        results["elapsed_seconds"] = time.monotonic() - started
        results["peak_process_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        results["completed_at"] = now()
        results["artifact_hashes"] = {
            p.name: file_sha256(p)
            for p in directory.iterdir()
            if p.name.endswith(("-scores.npy", ".txt", "-p1.npy", "-p0.npy"))
        }
        mlflow.log_dict(results, "results.json")
        mlflow.log_metrics(
            {
                "elapsed_seconds": results["elapsed_seconds"],
                "peak_process_rss_kib": results["peak_process_rss_kib"],
            }
        )
        atomic_json(output, results)
    # Only newly created private extraction caches are removed; original data stay intact.
    del x, t, y, vx, vt, vy
    gc.collect()
    for role in ("train", "validation"):
        for column in ("x", "t", "y"):
            (directory / f"{role}-{column}.npy").unlink()
    return results


def run(config, first_only=False):
    before = snapshot(config)
    registry = split(config, verify_only=True)
    recipe, digest, hashes = protocol()
    root = Path("artifacts/phase6") / digest
    results = []
    for spec in registry["development_splits"][: 1 if first_only else 5]:
        print(f"Phase 6 split {spec['seed']}: starting/verified resume", flush=True)
        results.append(run_one(config, recipe, digest, hashes, registry, spec, root))
        if snapshot(config) != before:
            raise ContractError("Protected input changed during execution")
        print(f"Phase 6 split {spec['seed']}: complete; protected inputs unchanged", flush=True)
    report = {
        "status": "first_split_verified" if first_only else "completed",
        "protocol_sha256": digest,
        "protocol_files": hashes,
        "recipe": recipe,
        "protected_inputs": before,
        "protected_inputs_unchanged": True,
        "splits": results,
    }
    atomic_json(
        Path("reports/phase_6_first_split.json" if first_only else "reports/phase_6_metrics.json"),
        report,
    )
    return report
