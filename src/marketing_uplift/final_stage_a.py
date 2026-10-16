"""Prepare final development diagnostic fits and an immutable Stage A-only lock."""

import hashlib
import json
import resource
import shutil
import subprocess
import sys
import time
import tomllib
from pathlib import Path
from urllib.parse import unquote, urlparse

import lightgbm as lgb
import mlflow
import numpy as np
import pyarrow

from marketing_uplift.data_contract import FEATURES, ContractError, now
from marketing_uplift.decisions import immutable_json, memory_status, tree_hash
from marketing_uplift.decisions import protected as phase8_protected
from marketing_uplift.decisions import protocol as phase8_protocol
from marketing_uplift.final_access import STAGE_B_BLOCKER, development_batches
from marketing_uplift.final_fit_worker import ids_sha
from marketing_uplift.ingestion import file_sha256
from marketing_uplift.splits import get_member, verify_registry


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def protected(config):
    current = phase8_protected(config)
    old = json.loads(Path("reports/phase_8_metrics.json").read_text())
    if current != old["protected_before"] or phase8_protocol()[1] != old["protocol_sha256"]:
        raise ContractError("Preserved Phase 8 dependencies changed")
    paths = [
        *[p for p in Path("reports").iterdir() if p.is_file() and not p.name.startswith("phase_9")],
        *[p for p in Path("configs").glob("*.toml") if p.name != "phase9.toml"],
        *[p for p in Path("docs").glob("PHASE*PROTOCOL.md") if "PHASE9" not in p.name],
        *[
            p
            for p in Path("src/marketing_uplift").glob("*.py")
            if not p.name.startswith("final_") and p.name != "cli.py"
        ],
        *[p for p in Path("artifacts/phase8").rglob("*") if p.is_file()],
    ]
    for path in paths:
        current[str(path)] = {"bytes": path.stat().st_size, "sha256": file_sha256(path)}
    for experiment in (
        "marketing-uplift-phase8-development",
        "marketing-uplift-phase8-publication",
    ):
        exp = mlflow.get_experiment_by_name(experiment)
        if exp is None:
            raise ContractError("Missing historical Phase 8 experiment")
        for run in mlflow.search_runs(experiment_ids=[exp.experiment_id], output_format="list"):
            if run.info.status != "FINISHED":
                raise ContractError("Historical MLflow run not finished")
            runroot = Path(unquote(urlparse(run.info.artifact_uri).path)).parent
            current[str(runroot)] = tree_hash(runroot)
    return current


def protocol():
    paths = [Path("configs/phase9.toml"), Path("docs/PHASE9_STAGE_A_PROTOCOL.md")]
    paths += sorted(Path("src/marketing_uplift").glob("final_*.py"))
    paths += [
        Path("src/marketing_uplift/cli.py"),
        Path(".github/workflows/stage-a.yml"),
        Path(".github/workflows/stage-b-disabled.yml"),
        Path("uv.lock"),
    ]
    paths += sorted(Path("tests").glob("test_final*.py"))
    hashes = {str(p): file_sha256(p) for p in paths}
    hashes["phase8_protocol"] = phase8_protocol()[1]
    settings = tomllib.loads(paths[0].read_text())
    if (
        settings["stage_b_enabled"]
        or settings["replicates"] != 2000
        or settings["comparison_family_size"] != 765
        or settings["nuisance_folds"] != 3
    ):
        raise ContractError("Stage A protocol or Stage B denial changed")
    return settings, digest(hashes), hashes


def prepare_cache(config, registry, root):
    spec = registry["memberships"]["development"]
    ids = get_member(spec, registry["rows"])
    path = root / "cache-manifest.json"
    if path.exists():
        manifest = json.loads(path.read_text())
        for name, sha in manifest.items():
            if file_sha256(root / name) != sha:
                raise ContractError("Existing Stage A development cache changed")
        return ids, manifest
    names = [f"development-{col}.npy" for col in ("x", "t", "y")]
    if any((root / name).exists() for name in names):
        raise ContractError("Partial Stage A cache requires review; no overwrite")
    n = len(ids)
    x = np.lib.format.open_memmap(root / names[0], mode="w+", dtype="float64", shape=(n, 12))
    t = np.lib.format.open_memmap(root / names[1], mode="w+", dtype="uint8", shape=(n,))
    y = np.lib.format.open_memmap(root / names[2], mode="w+", dtype="uint8", shape=(n,))
    offset = 0
    for batch in development_batches(config, ids, ["row_id", *FEATURES, "treatment", "visit"]):
        end = offset + batch.num_rows
        if not np.array_equal(batch.column(0).to_numpy(), ids[offset:end]):
            raise ContractError("Stage A development alignment failed")
        for j in range(12):
            values = batch.column(j + 1).to_numpy()
            if not np.isfinite(values).all():
                raise ContractError("Nonfinite development feature; no coercion")
            x[offset:end, j] = values
        for target, col in ((t, 13), (y, 14)):
            values = batch.column(col).to_numpy()
            if not np.isin(values, [0, 1]).all():
                raise ContractError("Invalid development label; no coercion")
            target[offset:end] = values
        offset = end
    if offset != n:
        raise ContractError("Incomplete Stage A development extraction")
    for a in (x, t, y):
        a.flush()
    manifest = {name: file_sha256(root / name) for name in names}
    immutable_json(path, manifest)
    return ids, manifest


def prepare_jobs(settings, registry, root, ids, cache):
    n = len(ids)
    t = np.load(root / "development-t.npy", mmap_mode="r")
    y = np.load(root / "development-y.npy", mmap_mode="r")
    folds = np.empty(n, dtype=np.uint8)
    folds[np.random.default_rng(settings["nuisance_fold_seed"]).permutation(n)] = np.arange(n) % 3
    probe = np.linspace(0, n - 1, settings["verification_rows"], dtype=int)
    for name, a in (("nuisance-folds.npy", folds), ("probe-positions.npy", probe)):
        path = root / name
        if path.exists():
            if not np.array_equal(np.load(path), a):
                raise ContractError("Frozen final folds/probe changed")
        else:
            np.save(path, a)
    shared = {
        "directory": str(root),
        "development_ids_sha256": ids_sha(ids),
        "membership": registry["memberships"]["development"],
        "cache": {
            **cache,
            "nuisance-folds.npy": file_sha256(root / "nuisance-folds.npy"),
            "probe-positions.npy": file_sha256(root / "probe-positions.npy"),
        },
        "recipe_sha256": file_sha256(Path("configs/baselines.toml")),
    }
    definitions = [
        ("response", 1, None, settings["model_seed"]),
        ("control", 0, None, settings["model_seed"]),
        ("s_learner", None, None, settings["model_seed"]),
    ]
    definitions += [
        (f"nuisance-{k}-{a}", a, k, settings["nuisance_model_seed"] + 10 * k + a)
        for k in range(3)
        for a in (0, 1)
    ]
    jobs = []
    for name, arm, excluded, seed in definitions:
        mask = np.ones(n, dtype=bool) if arm is None else t == arm
        if excluded is not None:
            mask &= folds != excluded
        job = {
            **shared,
            "name": name,
            "arm": arm,
            "excluded_fold": excluded,
            "seed": seed,
            "fit_rows": int(mask.sum()),
            "fit_visits": int(y[mask].sum()),
            "fit_mask_sha256": hashlib.sha256(mask.tobytes()).hexdigest(),
            "fit_ids_sha256": ids_sha(ids[mask]),
            "features": [*FEATURES, "__intervention_treatment"] if arm is None else FEATURES,
        }
        immutable_json(root / f"{name}-job.json", job)
        jobs.append(job)
    manifest = {
        "folds_sha256": shared["cache"]["nuisance-folds.npy"],
        "algorithm": "PCG64 permutation of sorted development positions; round-robin modulo3",
        "seed": settings["nuisance_fold_seed"],
        "fold_rows": [int((folds == k).sum()) for k in range(3)],
        "jobs": jobs,
    }
    immutable_json(root / "frozen-training.json", manifest)
    return jobs, manifest


def primary_policy(economics, report):
    reasons = {
        str(s["seed"]): {name: d["reason_codes"] for name, d in s["decisions"].items()}
        for s in report["splits"]
    }
    if any(
        d["model"] is not None or d["reach_index"] != 0
        for s in report["splits"]
        for d in s["decisions"].values()
    ):
        raise ContractError("Expected unanimous historical abstention, not policy re-selection")
    return {
        "model": None,
        "ranking": None,
        "reach": 0,
        "advertising_assignments": 0,
        "hypothetical_spending": "0",
        "incremental_gain_relative_to_no_targeting": 0,
        "identity_not_statistical_evidence": True,
        "claim_of_optimality": False,
        "economics": economics,
        "development_reason_codes": reasons,
    }


def run(config):
    started = time.monotonic()
    before = protected(config)
    settings, protocol_sha, hashes = protocol()
    root = Path("artifacts/phase9") / protocol_sha
    root.mkdir(parents=True, exist_ok=True)
    immutable_json(root / "protected.json", before)
    registry = json.loads(Path(config["experiment"]["split_registry"]).read_text())
    verify_registry(registry)
    provenance = {
        "protocol_sha256": protocol_sha,
        "files": hashes,
        "registry_sha256": file_sha256(Path(config["experiment"]["split_registry"])),
        "source": registry["source"],
        "development": registry["memberships"]["development"],
        "holdout_membership_only": registry["memberships"]["holdout"],
        "versions": {
            "python": sys.version,
            "numpy": np.__version__,
            "lightgbm": lgb.__version__,
            "pyarrow": pyarrow.__version__,
            "mlflow": mlflow.__version__,
        },
    }
    prior_provenance = root / "provenance.json"
    provenance["training_code_commit"] = (
        json.loads(prior_provenance.read_text())["training_code_commit"]
        if prior_provenance.exists()
        else subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    )
    immutable_json(prior_provenance, provenance)
    existing = Path("reports/phase9/stage_a.json")
    if existing.exists():
        old = json.loads(existing.read_text())
        verify_lock(config, old)
        return old
    if shutil.disk_usage(".").free < config["resources"]["min_free_disk_bytes"]:
        raise ContractError("Insufficient free disk for final development fits")
    ids, cache = prepare_cache(config, registry, root)
    jobs, training = prepare_jobs(settings, registry, root, ids, cache)
    immutable_json(root / "frozen-protocol.json", {"settings": settings, "hashes": hashes})
    memory_before = memory_status()
    fits = []
    for job in jobs:
        name = job["name"]
        output = root / f"{name}-fit.json"
        if output.exists():
            fit = json.loads(output.read_text())
            if fit["job"] != job or file_sha256(root / f"{name}.txt") != fit["model_sha256"]:
                raise ContractError("Final diagnostic resume fit mismatch")
            print(f"Stage A {name}: verified existing fit", flush=True)
        else:
            print(f"Stage A {name}: development-only fit starting", flush=True)
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "marketing_uplift.final_fit_worker",
                    str(root / f"{name}-job.json"),
                ],
                check=True,
            )
            fit = json.loads(output.read_text())
        fits.append(fit)
    if protected(config) != before:
        raise ContractError("Historical protected artifacts changed during Stage A")
    model_manifest = {
        "protocol_sha256": protocol_sha,
        "development": provenance["development"],
        "training": training,
        "recipe": tomllib.loads(Path("configs/baselines.toml").read_text()),
        "versions": provenance["versions"],
        "models": fits,
    }
    immutable_json(root / "model-manifest.json", model_manifest)
    model_digest = digest(model_manifest)
    old8 = json.loads(Path("reports/phase_8_metrics.json").read_text())
    economics = tomllib.loads(Path("configs/phase8.toml").read_text())["economics"]
    lock = {
        "schema": "stage-a-final-policy-lock/v1",
        "protocol_sha256": protocol_sha,
        "model_manifest_sha256": model_digest,
        "provenance": provenance,
        "primary": primary_policy(economics, old8),
        "secondary": {
            "rankings": ["random", "response", "s_learner", "t_learner"],
            "reach": settings["reach"],
            "anchors": ["none", "all"],
            "never_replace_primary": True,
        },
        "stage_a_approved": True,
        "stage_b_authorized": False,
        "stage_b_enabled": False,
        "stage_b_blocker": STAGE_B_BLOCKER,
        "protected_snapshot_sha256": digest(before),
    }
    lock_sha = digest(lock)
    immutable_json(root / "lock.json", {"lock_sha256": lock_sha, "payload": lock})
    mlflow.set_tracking_uri(Path(config["tracking"]["directory"]).resolve().as_uri())
    mlflow.set_experiment("marketing-uplift-phase9-stage-a")
    with mlflow.start_run(run_name=f"stage-a-{protocol_sha[:12]}") as run_info:
        result = {
            "status": "stage_a_locked_stage_b_disabled",
            "protocol_sha256": protocol_sha,
            "lock_sha256": lock_sha,
            "model_manifest_sha256": model_digest,
            "lock": lock,
            "model_manifest": model_manifest,
            "protected_before": before,
            "protected_unchanged": True,
            "mlflow_run_id": run_info.info.run_id,
            "completed_at": now(),
            "elapsed_seconds": time.monotonic() - started,
            "peak_fit_rss_kib": max(f["peak_rss_kib"] for f in fits),
            "parent_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "memory_before": memory_before,
            "memory_after": memory_status(),
            "free_disk_bytes": shutil.disk_usage(".").free,
            "no_holdout_rows_read": True,
            "no_holdout_predictions": True,
        }
        mlflow.log_params(
            {
                "lock_sha256": lock_sha,
                "model_manifest_sha256": model_digest,
                "protocol_sha256": protocol_sha,
                "development_rows": len(ids),
                "stage_b_enabled": False,
                "models": len(fits),
            }
        )
        mlflow.log_dict(provenance, "provenance.json")
        mlflow.log_dict(lock, "lock.json")
        mlflow.log_dict(model_manifest, "model-manifest.json")
        for fit in fits:
            name = fit["job"]["name"]
            mlflow.log_artifact(str(root / f"{name}.txt"), "models")
        mlflow.log_metrics(
            {
                "elapsed_seconds": result["elapsed_seconds"],
                "peak_fit_rss_kib": result["peak_fit_rss_kib"],
            }
        )
        mlflow.log_dict(result, "stage-a-result.json")
        immutable_json(existing, result)
    return result


def verify_lock(config, report):
    settings, protocol_sha, _ = protocol()
    if (
        protocol_sha != report["protocol_sha256"]
        or report["lock_sha256"] != digest(report["lock"])
        or report["model_manifest_sha256"] != digest(report["model_manifest"])
    ):
        raise ContractError("Stage A lock/protocol/model manifest mismatch")
    if (
        settings["stage_b_enabled"]
        or report["lock"]["stage_b_enabled"]
        or report["lock"]["stage_b_authorized"]
    ):
        raise ContractError("Stage B must remain disabled/unapproved")
    if protected(config) != report["protected_before"]:
        raise ContractError("Historical protected artifacts changed")
    root = Path("artifacts/phase9") / protocol_sha
    for filename, sha in report["model_manifest"]["models"][0]["job"]["cache"].items():
        if file_sha256(root / filename) != sha:
            raise ContractError("Locked development cache/folds changed")
    for name, expected in (
        ("model-manifest.json", report["model_manifest"]),
        ("lock.json", {"lock_sha256": report["lock_sha256"], "payload": report["lock"]}),
    ):
        if json.loads((root / name).read_text()) != expected:
            raise ContractError("Private final lock evidence changed")
    for fit in report["model_manifest"]["models"]:
        name = fit["job"]["name"]
        if file_sha256(root / f"{name}.txt") != fit["model_sha256"]:
            raise ContractError("Locked model changed")
        for filename, sha in fit["probe_hashes"].items():
            if file_sha256(root / filename) != sha:
                raise ContractError("Locked development probe changed")
    return {
        "lock_sha256": report["lock_sha256"],
        "model_manifest_sha256": report["model_manifest_sha256"],
        "models": 9,
        "stage_b_enabled": False,
    }


def verify_public_lock():
    report = json.loads(Path("reports/phase9/stage_a.json").read_text())
    _, sha, _ = protocol()
    if (
        sha != report["protocol_sha256"]
        or digest(report["lock"]) != report["lock_sha256"]
        or digest(report["model_manifest"]) != report["model_manifest_sha256"]
    ):
        raise ContractError("Public Stage A lock mismatch")
    if report["lock"]["stage_b_enabled"] or report["lock"]["stage_b_authorized"]:
        raise ContractError("Stage B is not approved")
    return {
        "lock_sha256": report["lock_sha256"],
        "stage_b_enabled": False,
        "datasets_opened": False,
    }
