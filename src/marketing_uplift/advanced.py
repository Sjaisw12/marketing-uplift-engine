"""Additive Phase 7 models and training-only cross-fitted nuisance evaluation."""

import gc
import hashlib
import json
import resource
import subprocess
import time
import tomllib
from pathlib import Path
from urllib.parse import unquote, urlparse

import lightgbm as lgb
import mlflow
import numpy as np
import pyarrow as pa

from marketing_uplift.baselines import diagnostics, extract, parameters, predict, snapshot
from marketing_uplift.baselines import protocol as baseline_protocol
from marketing_uplift.data_contract import FEATURES, ContractError, atomic_json, connection, now
from marketing_uplift.ingestion import file_sha256, parquet_path
from marketing_uplift.robust_metrics import evaluate
from marketing_uplift.splits import verify_registry

PHASE6 = Path("reports/phase_6_metrics.json")


def protected(config):
    old = json.loads(PHASE6.read_text())
    current = snapshot(config)
    if current != old["protected_inputs"]:
        raise ContractError("Phase 6 protected source changed")
    paths = [
        Path("uv.lock"),
        Path("configs/project.toml"),
        Path("configs/baselines.toml"),
        Path("docs/PHASE6_PROTOCOL.md"),
        Path("src/marketing_uplift/baselines.py"),
        Path("src/marketing_uplift/policy_metrics.py"),
        *Path("reports").glob("phase_6*"),
    ]
    mlflow.set_tracking_uri(Path(config["tracking"]["directory"]).resolve().as_uri())
    for result in old["splits"]:
        directory = Path("artifacts/phase6") / old["protocol_sha256"] / str(result["seed"])
        for name, sha in result["artifact_hashes"].items():
            if file_sha256(directory / name) != sha:
                raise ContractError("Phase 6 artifact changed")
            paths.append(directory / name)
        run = mlflow.get_run(result["mlflow_run_id"])
        if run.info.status != "FINISHED":
            raise ContractError("Phase 6 run is not finished")
        runroot = Path(unquote(urlparse(run.info.artifact_uri).path)).parent
        tree = {
            str(p.relative_to(runroot)): file_sha256(p) for p in runroot.rglob("*") if p.is_file()
        }
        current[str(runroot)] = {
            "files": len(tree),
            "tree_sha256": hashlib.sha256(json.dumps(tree, sort_keys=True).encode()).hexdigest(),
        }
    for p in paths:
        current[str(p)] = {"bytes": p.stat().st_size, "sha256": file_sha256(p)}
    if baseline_protocol()[1] != old["protocol_sha256"]:
        raise ContractError("Phase 6 protocol changed")
    return current


def protocol():
    paths = [
        Path("configs/phase7.toml"),
        Path("docs/PHASE7_PROTOCOL.md"),
        Path(__file__),
        Path(__file__).with_name("robust_metrics.py"),
    ]
    hashes = {str(p): file_sha256(p) for p in paths}
    hashes["phase6_protocol"] = baseline_protocol()[1]
    digest = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    return tomllib.loads(paths[0].read_text()), digest, hashes


def nuisance_folds(n, seed, count=3):
    labels = np.empty(n, dtype=np.uint8)
    labels[np.random.default_rng(seed).permutation(n)] = np.arange(n) % count
    return labels


def prepare_folds(registry, settings, root):
    manifest = {}
    for spec in registry["development_splits"]:
        directory = root / str(spec["seed"])
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "nuisance-folds.npy"
        expected = nuisance_folds(
            spec["train"]["rows"], spec["seed"] + settings["fold_seed_offset"]
        )
        if path.exists():
            if not np.array_equal(np.load(path, mmap_mode="r"), expected):
                raise ContractError("Existing nuisance folds changed")
        else:
            np.save(path, expected)
        manifest[str(spec["seed"])] = {"rows": len(expected), "sha256": file_sha256(path)}
    path = root / "frozen-folds.json"
    if path.exists() and json.loads(path.read_text()) != manifest:
        raise ContractError("Frozen nuisance-fold manifest changed")
    if not path.exists():
        atomic_json(path, manifest)
    return manifest


def calibration(y, p, edges):
    if not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ContractError("Invalid calibration probabilities")
    bins = np.minimum(np.searchsorted(edges, p, side="right") - 1, len(edges) - 2)
    return {
        "metrics": diagnostics(y, p),
        "bins": [
            {
                "lower": edges[k],
                "upper": edges[k + 1],
                "records": int((bins == k).sum()),
                "visits": int(y[bins == k].sum()),
                "mean_prediction": float(p[bins == k].mean()) if (bins == k).any() else None,
            }
            for k in range(len(edges) - 1)
        ],
    }


def fit(x, y, mask, recipe, seed, path):
    if x.shape[1] != 12 or not mask.any() or len(np.unique(y[mask])) != 2:
        raise ContractError("Insufficient arm data or invalid feature matrix")
    data = lgb.Dataset(x[mask], label=y[mask], feature_name=FEATURES, free_raw_data=True)
    model = lgb.train(parameters(recipe, seed), data, num_boost_round=recipe["rounds"])
    model.save_model(str(path))
    del data
    gc.collect()
    return model


def vector_overlap(config, train, validation):
    with connection(config) as con:
        con.register(
            "ids",
            pa.table(
                {
                    "row_id": np.concatenate((train, validation)),
                    "is_train": np.r_[
                        np.ones(len(train), dtype=np.uint8),
                        np.zeros(len(validation), dtype=np.uint8),
                    ],
                }
            ),
        )
        con.read_parquet(str(parquet_path(config))).create_view("source")
        features = ",".join("p." + f for f in FEATURES)
        query = f"""WITH vectors AS (
          SELECT {features},sum(i.is_train)::BIGINT AS nt,
                 count(*)-sum(i.is_train)::BIGINT AS nv
          FROM source p JOIN ids i USING(row_id) GROUP BY {features})
          SELECT count(*) FILTER(WHERE nt>0),count(*) FILTER(WHERE nv>0),
                 count(*) FILTER(WHERE nt>0 AND nv>0),
                 coalesce(sum(nv) FILTER(WHERE nt>0),0),
                 coalesce(sum(nt+nv) FILTER(WHERE nt+nv>1),0) FROM vectors"""
        row = con.execute(query).fetchone()
    return dict(
        zip(
            (
                "training_distinct_vectors",
                "validation_distinct_vectors",
                "shared_vectors",
                "validation_rows_matching_training",
                "development_rows_in_repeated_vectors",
            ),
            map(int, row),
            strict=True,
        )
    )


def one(config, settings, digest, hashes, registry, spec, old, root):
    seed = spec["seed"]
    directory = root / str(seed)
    resultpath = directory / "result.json"
    provenance = {
        "protocol_sha256": digest,
        "phase6_protocol": old["protocol_sha256"],
        "phase6_report_sha256": file_sha256(PHASE6),
        "train": spec["train"],
        "validation": spec["validation"],
        "registry_sha256": file_sha256(Path(config["experiment"]["split_registry"])),
    }
    if resultpath.exists():
        result = json.loads(resultpath.read_text())
        if result["provenance"] != provenance:
            raise ContractError("Phase 7 resume provenance mismatch")
        for name, sha in result["artifact_hashes"].items():
            if file_sha256(directory / name) != sha:
                raise ContractError("Phase 7 artifact mismatch")
        return result
    directory.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    recipe = tomllib.loads(Path("configs/baselines.toml").read_text())
    x, t, y, trainids = extract(config, spec["train"], registry["rows"], directory, "train")
    vx, vt, vy, ids = extract(config, spec["validation"], registry["rows"], directory, "validation")
    folds = np.load(directory / "nuisance-folds.npy", mmap_mode="r")
    if not np.array_equal(folds, nuisance_folds(len(t), seed + settings["fold_seed_offset"])):
        raise ContractError("Nuisance fold definition mismatch")
    foldmanifest = {
        "seed": seed + settings["fold_seed_offset"],
        "algorithm": "PCG64 permutation of sorted training positions, round robin modulo3",
        "outer_training": spec["train"],
        "fold_labels_sha256": file_sha256(directory / "nuisance-folds.npy"),
        "folds": [],
    }
    for k in range(3):
        foldmanifest["folds"].append(
            {
                "fold": k,
                "held_rows": int((folds == k).sum()),
                "arms": [
                    {
                        "arm": a,
                        "fit_rows": int(((t == a) & (folds != k)).sum()),
                        "fit_visits": int(y[(t == a) & (folds != k)].sum()),
                        "fit_mask_sha256": hashlib.sha256(
                            ((t == a) & (folds != k)).tobytes()
                        ).hexdigest(),
                        "seed": seed + settings["nuisance_seed_offset"] + 10 * k + a,
                    }
                    for a in (0, 1)
                ],
            }
        )
    atomic_json(directory / "fold-manifest.json", foldmanifest)
    oldsplit = next(s for s in old["splits"] if s["seed"] == seed)
    olddir = Path("artifacts/phase6") / old["protocol_sha256"] / str(seed)
    result = {
        "seed": seed,
        "provenance": provenance,
        "fold_manifest": foldmanifest,
        "models": [],
        "validation_rows": len(vt),
        "training_rows": len(t),
        "diagnostics": {},
    }
    mlflow.set_tracking_uri(Path(config["tracking"]["directory"]).resolve().as_uri())
    mlflow.set_experiment("marketing-uplift-phase7-development")
    with mlflow.start_run(run_name=f"phase7-{seed}") as run:
        result["mlflow_run_id"] = run.info.run_id
        mlflow.log_params(
            {
                **settings,
                "outer_seed": seed,
                "protocol_sha256": digest,
                "phase6_run_id": oldsplit["mlflow_run_id"],
            }
        )
        mlflow.log_dict(
            {
                "provenance": provenance,
                "protocol_files": hashes,
                "git_commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
                "lightgbm": lgb.__version__,
                "numpy": np.__version__,
            },
            "provenance.json",
        )
        model = fit(x, y, t == 0, recipe, seed, directory / "control.txt")
        p0 = predict(model, vx)
        np.save(directory / "t-control.npy", p0)
        result["models"].append(
            {
                "name": "control",
                "rows": int((t == 0).sum()),
                "seed": seed,
                "trees": model.num_trees(),
                "features": model.feature_name(),
            }
        )
        del model
        gc.collect()
        oof = np.empty(len(t))
        seen = np.zeros(len(t), dtype=np.uint8)
        avg = [np.zeros(len(vt)), np.zeros(len(vt))]
        for k in range(3):
            for arm in (0, 1):
                then = time.monotonic()
                mask = (t == arm) & (folds != k)
                held = (t == arm) & (folds == k)
                path = directory / f"nuisance-{k}-{arm}.txt"
                model = fit(
                    x, y, mask, recipe, seed + settings["nuisance_seed_offset"] + 10 * k + arm, path
                )
                vp = predict(model, vx)
                np.save(directory / f"nuisance-{k}-{arm}.npy", vp)
                avg[arm] += vp / 3
                oof[held] = predict(model, x[held])
                seen[held] += 1
                result["models"].append(
                    {
                        "name": path.stem,
                        "rows": int(mask.sum()),
                        "seed": seed + settings["nuisance_seed_offset"] + 10 * k + arm,
                        "trees": model.num_trees(),
                        "features": model.feature_name(),
                        "seconds": time.monotonic() - then,
                    }
                )
                del model, vp, mask, held
                gc.collect()
                print(f"Phase 7 {seed}: nuisance fold {k} arm {arm} complete", flush=True)
        if not np.all(seen == 1):
            raise ContractError("OOF exclusion/coverage failed")
        np.save(directory / "oof.npy", oof)
        for arm in (0, 1):
            np.save(directory / f"dr-m{arm}.npy", avg[arm])
        priorities = np.random.default_rng(seed + recipe["random_seed_offset"]).random(len(ids))
        response = np.load(olddir / "response-scores.npy", mmap_mode="r")
        sscore = np.load(olddir / "s_learner-scores.npy", mmap_mode="r")
        alt0, alt1 = (
            np.load(olddir / "s-p0.npy", mmap_mode="r"),
            np.load(olddir / "s-p1.npy", mmap_mode="r"),
        )
        tscore = response - p0
        np.save(directory / "t-scores.npy", tscore)
        scores = {
            "random": priorities,
            "response": response,
            "s_learner": sscore,
            "t_learner": tscore,
        }
        fitmanifest = {
            p.name: file_sha256(p)
            for p in directory.iterdir()
            if p.is_file()
            and p.suffix in (".npy", ".txt")
            and not p.name.startswith(("train-", "validation-"))
        }
        atomic_json(directory / "fit-manifest.json", fitmanifest)
        result["evaluation"] = evaluate(
            vt,
            vy,
            ids,
            scores,
            avg[0],
            avg[1],
            alt0,
            alt1,
            settings["scenarios"],
            settings["replicates"],
            seed + settings["multiplier_seed_offset"],
        )
        for e, scenario in oldsplit["evaluation"]["scenarios"].items():
            for name in ("random", "response", "s_learner"):
                new = result["evaluation"]["estimates"]["ipw"][e]["models"][name]
                for a, b in zip(new["policies"], scenario["models"][name]["policies"], strict=True):
                    if not np.isclose(a["value"]["estimate"], b["value"], rtol=0, atol=1e-12):
                        raise ContractError("Phase 6 point estimate failed reproduction")
        edges = settings["calibration_edges"]
        for arm in (0, 1):
            mask = vt == arm
            result["diagnostics"][f"t_arm_{arm}"] = calibration(
                vy[mask], (p0 if arm == 0 else response)[mask], edges
            )
            result["diagnostics"][f"dr_arm_{arm}"] = calibration(vy[mask], avg[arm][mask], edges)
            result["diagnostics"][f"oof_arm_{arm}"] = calibration(y[t == arm], oof[t == arm], edges)
            result["diagnostics"][f"s_arm_{arm}"] = calibration(
                vy[mask], (alt0 if arm == 0 else alt1)[mask], edges
            )
        result["vector_overlap"] = vector_overlap(config, trainids, ids)
        result["elapsed_seconds"] = time.monotonic() - start
        result["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        result["completed_at"] = now()
        result["artifact_hashes"] = {
            p.name: file_sha256(p)
            for p in directory.iterdir()
            if p.is_file()
            and p.name != "result.json"
            and not p.name.startswith(("train-", "validation-"))
        }
        mlflow.log_dict(parameters(recipe, seed), "model_recipe.json")
        mlflow.log_dict(result, "result.json")
        for name in result["artifact_hashes"]:
            mlflow.log_artifact(str(directory / name), "private_artifacts")
        mlflow.log_metrics(
            {"elapsed_seconds": result["elapsed_seconds"], "peak_rss_kib": result["peak_rss_kib"]}
        )
        for method in ("ipw", "dr"):
            for name, modelrows in result["evaluation"]["estimates"][method]["0.85"][
                "models"
            ].items():
                mlflow.log_metrics(
                    {
                        f"{method}_{name}_gain_{int(p['reach'] * 100)}": p["gain_over_none"][
                            "estimate"
                        ]
                        for p in modelrows["policies"]
                    }
                )
        atomic_json(resultpath, result)
    del x, t, y, vx, vt, vy
    gc.collect()
    for role in ("train", "validation"):
        for col in ("x", "t", "y"):
            (directory / f"{role}-{col}.npy").unlink()
    return result


def run(config, first_only=False):
    before = protected(config)
    settings, digest, hashes = protocol()
    registry = json.loads(Path(config["experiment"]["split_registry"]).read_text())
    verify_registry(registry)
    old = json.loads(PHASE6.read_text())
    prepare_folds(registry, settings, Path("artifacts/phase7") / digest)
    results = []
    for spec in registry["development_splits"][: 1 if first_only else 5]:
        print(f"Phase 7 split {spec['seed']}: starting/verified resume", flush=True)
        results.append(
            one(
                config,
                settings,
                digest,
                hashes,
                registry,
                spec,
                old,
                Path("artifacts/phase7") / digest,
            )
        )
        if protected(config) != before:
            raise ContractError("Protected Phase 6 inputs changed")
        print(f"Phase 7 split {spec['seed']}: complete; protected inputs unchanged", flush=True)
    result = {
        "status": "first_split_complete" if first_only else "complete",
        "protocol_sha256": digest,
        "protocol_files": hashes,
        "settings": settings,
        "protected_before": before,
        "protected_unchanged": True,
        "splits": results,
    }
    atomic_json(
        Path("reports/phase_7_first_split.json" if first_only else "reports/phase_7_metrics.json"),
        result,
    )
    return result
