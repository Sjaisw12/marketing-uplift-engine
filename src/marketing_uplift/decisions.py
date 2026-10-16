"""Additive Phase 8 execution: freeze, select, persist, then assess; never fit."""

import gc
import hashlib
import json
import resource
import shutil
import subprocess
import time
import tomllib
from pathlib import Path
from urllib.parse import unquote, urlparse

import mlflow
import numpy as np
import pyarrow as pa

from marketing_uplift.advanced import protected as phase7_protected
from marketing_uplift.advanced import protocol as phase7_protocol
from marketing_uplift.data_contract import ContractError, atomic_json, connection, now
from marketing_uplift.decision_engine import (
    apply,
    choose,
    counts,
    feasible,
    id_hash,
)
from marketing_uplift.decision_metrics import coefficient, evaluate, summary
from marketing_uplift.ingestion import file_sha256, parquet_path
from marketing_uplift.robust_metrics import MODELS
from marketing_uplift.splits import get_member, verify_registry

OLD = Path("reports/phase_7_metrics.json")


def memory_status():
    result = {}
    for name in ("memory.max", "memory.peak", "memory.events"):
        path = Path("/sys/fs/cgroup") / name
        if path.exists():
            result[name] = path.read_text().strip()
    return result


def tree_hash(root):
    tree = {str(p.relative_to(root)): file_sha256(p) for p in root.rglob("*") if p.is_file()}
    return {
        "files": len(tree),
        "tree_sha256": hashlib.sha256(json.dumps(tree, sort_keys=True).encode()).hexdigest(),
    }


def protected(config):
    old = json.loads(OLD.read_text())
    current = phase7_protected(config)
    if current != old["protected_before"] or phase7_protocol()[1] != old["protocol_sha256"]:
        raise ContractError("Preserved Phase 7 dependency mismatch")
    paths = [
        Path("configs/phase7.toml"),
        Path("docs/PHASE7_PROTOCOL.md"),
        Path("src/marketing_uplift/advanced.py"),
        Path("src/marketing_uplift/robust_metrics.py"),
        *[p for p in Path("reports").glob("*") if p.is_file() and not p.name.startswith("phase_8")],
    ]
    root = Path("artifacts/phase7") / old["protocol_sha256"]
    paths.append(root / "frozen-folds.json")
    for split in old["splits"]:
        directory = root / str(split["seed"])
        for name, sha in split["artifact_hashes"].items():
            path = directory / name
            if file_sha256(path) != sha:
                raise ContractError("Preserved Phase 7 artifact mismatch")
            paths.append(path)
        paths.append(directory / "result.json")
        run = mlflow.get_run(split["mlflow_run_id"])
        if run.info.status != "FINISHED":
            raise ContractError("Preserved Phase 7 MLflow run unfinished")
        runroot = Path(unquote(urlparse(run.info.artifact_uri).path)).parent
        current[str(runroot)] = tree_hash(runroot)
    for path in paths:
        current[str(path)] = {"bytes": path.stat().st_size, "sha256": file_sha256(path)}
    return current


def protocol():
    paths = [Path("configs/phase8.toml"), Path("docs/PHASE8_PROTOCOL.md")]
    paths.extend(
        Path(__file__).with_name(name)
        for name in ("decisions.py", "decision_engine.py", "decision_metrics.py")
    )
    hashes = {str(p): file_sha256(p) for p in paths}
    hashes["phase7_protocol"] = phase7_protocol()[1]
    digest = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    return tomllib.loads(paths[0].read_text()), digest, hashes


def roles(n, seed):
    labels = np.ones(n, dtype=np.uint8)
    labels[np.random.default_rng(seed).permutation(n)[: n // 2]] = 0
    return labels


def immutable_json(path, value):
    if path.exists():
        if json.loads(path.read_text()) != value:
            raise ContractError(f"Immutable Phase 8 evidence mismatch: {path.name}")
    else:
        atomic_json(path, value)


def freeze(config):
    before = protected(config)
    settings, digest, hashes = protocol()
    if settings["model_order"] != list(MODELS) or settings["reach"] != [
        "0.1",
        "0.2",
        "0.3",
        "0.4",
        "0.5",
    ]:
        raise ContractError("Phase 8 ranking/reach recipe mismatch")
    if settings["replicates"] != 2000 or settings["scenarios"] != [0.8, 0.825, 0.85, 0.875, 0.9]:
        raise ContractError("Phase 8 uncertainty/scenario recipe mismatch")
    registry = json.loads(Path(config["experiment"]["split_registry"]).read_text())
    verify_registry(registry)
    if len(registry["development_splits"]) != 5:
        raise ContractError("Expected five frozen development splits")
    root = Path("artifacts/phase8") / digest
    root.mkdir(parents=True, exist_ok=True)
    immutable_json(root / "protected.json", before)
    manifest = {}
    for spec in registry["development_splits"]:
        ids = get_member(spec["validation"], registry["rows"])
        labels = roles(len(ids), spec["seed"] + settings["role_seed_offset"])
        directory = root / str(spec["seed"])
        directory.mkdir(exist_ok=True)
        path = directory / "roles.npy"
        if path.exists():
            if not np.array_equal(np.load(path), labels):
                raise ContractError("Existing selection/assessment roles changed")
        else:
            np.save(path, labels)
        manifest[str(spec["seed"])] = {
            "validation": spec["validation"],
            "labels_sha256": file_sha256(path),
            "selection_rows": int((labels == 0).sum()),
            "assessment_rows": int((labels == 1).sum()),
            "selection_ids_sha256": id_hash(ids[labels == 0]),
            "assessment_ids_sha256": id_hash(ids[labels == 1]),
        }
    # All role hashes are on disk before any Phase 8 query of T or Y.
    immutable_json(root / "frozen-roles.json", manifest)
    immutable_json(
        root / "protocol.json", {"digest": digest, "files": hashes, "settings": settings}
    )
    return settings, digest, hashes, registry, root, before, manifest


def source_outcomes(config, ids):
    """Call only with explicitly selected frozen development role IDs."""
    with connection(config) as con:
        con.register("role_ids", pa.table({"row_id": ids}))
        con.read_parquet(str(parquet_path(config))).create_view("source")
        rows = con.execute(
            "SELECT p.row_id,p.treatment,p.visit FROM source p "
            "JOIN role_ids USING(row_id) ORDER BY p.row_id"
        ).fetchnumpy()
    if not np.array_equal(rows["row_id"], ids):
        raise ContractError("Development query row alignment failed")
    return rows["treatment"], rows["visit"]


def inputs(seed, ids, mask):
    old6 = json.loads(Path("reports/phase_6_metrics.json").read_text())
    old7 = json.loads(OLD.read_text())
    p6 = Path("artifacts/phase6") / old6["protocol_sha256"] / str(seed)
    p7 = Path("artifacts/phase7") / old7["protocol_sha256"] / str(seed)
    scores = {"random": np.random.default_rng(seed + 1000000).random(len(ids))[mask]}
    for name in MODELS[1:]:
        path = p7 / "t-scores.npy" if name == "t_learner" else p6 / f"{name}-scores.npy"
        a = np.load(path, mmap_mode="r")
        if a.shape != ids.shape:
            raise ContractError("Existing score shape mismatch")
        scores[name] = a[mask]
    probabilities = []
    for path in (p7 / "dr-m0.npy", p7 / "dr-m1.npy", p6 / "s-p0.npy", p6 / "s-p1.npy"):
        a = np.load(path, mmap_mode="r")
        if a.shape != ids.shape:
            raise ContractError("Existing nuisance shape mismatch")
        probabilities.append(a[mask])
    return scores, probabilities


def evaluate_role(config, settings, seed, ids, allids, mask, label):
    scores, probabilities = inputs(seed, allids, mask)
    t, y = source_outcomes(config, ids)
    evidence = evaluate(
        ids,
        scores,
        (t, y, *probabilities),
        settings["scenarios"],
        settings["replicates"],
        seed + settings[f"{label}_multiplier_offset"],
        settings["batch_rows"],
    )
    return evidence


def save_evidence(directory, label, evidence):
    path = directory / f"{label}-uncertainty.npz"
    if path.exists():
        raise ContractError("Partial existing uncertainty needs review; do not overwrite")
    np.savez_compressed(
        path,
        point=evidence["point"],
        lower=evidence["lower"],
        covariance=evidence["covariance"],
        draws=evidence["draws"],
    )


def policy_table(evidence):
    rows = {}
    for model in MODELS:
        for k in range(1, 7):
            key = f"{model}:{k}"
            rows[key] = [
                summary(evidence, coefficient(evidence, model, k, s))
                for s in range(len(evidence["keys"]))
            ]
    rows["none:0"] = [
        summary(evidence, coefficient(evidence, None, 0, s)) for s in range(len(evidence["keys"]))
    ]
    return rows


def policy_hash(evidence, ids, model, k):
    n = len(ids) if k == 6 else counts(len(ids))[k]
    selected = ids[evidence["orders"][model][:n]] if model is not None else ids[:0]
    return id_hash(np.sort(selected))


def comparisons(evidence, application, spec):
    n = evidence["rows"]
    chosen, k = application["model"], application["reach_index"]
    matched = []
    for model in MODELS:
        contrasts = [
            summary(
                evidence, coefficient(evidence, chosen, k, s) - coefficient(evidence, model, k, s)
            )
            for s in range(len(evidence["keys"]))
        ]
        matched.append(
            {
                "model": model,
                "reach_index": k,
                "selected": application["ledger"]["selected"],
                "engine_minus_comparator": contrasts,
            }
        )
    eligible = [
        f"{m}:{j}"
        for m in MODELS
        for j, count in enumerate(counts(n))
        if j and feasible(spec, n, count)
    ]
    eligible.append("none:0")
    if feasible(spec, n, n):
        eligible.append("random:6")  # All four all-target policies are identical.
    return {
        "equal_actual_spending": matched,
        "equal_budget_cap_policy_keys": eligible,
        "all_targeting_feasible": feasible(spec, n, n),
    }


def one(config, settings, digest, hashes, registry, spec, root, manifest):
    seed = spec["seed"]
    directory = root / str(seed)
    provenance = {
        "protocol_sha256": digest,
        "registry_sha256": file_sha256(Path(config["experiment"]["split_registry"])),
        "phase7_report_sha256": file_sha256(OLD),
        "roles": manifest[str(seed)],
    }
    resultpath = directory / "result.json"
    if resultpath.exists():
        result = json.loads(resultpath.read_text())
        if result["provenance"] != provenance:
            raise ContractError("Phase 8 resume provenance mismatch")
        for name, sha in result["artifact_hashes"].items():
            if file_sha256(directory / name) != sha:
                raise ContractError("Phase 8 resume artifact mismatch")
        run = mlflow.get_run(result["mlflow_run_id"])
        if run.info.status != "FINISHED":
            raise ContractError("Phase 8 resume MLflow run unfinished")
        return result
    if (directory / "recommendations.json").exists():
        raise ContractError("Partial Phase 8 split needs review; sealed recommendations preserved")
    start = time.monotonic()
    memory_before = memory_status()
    ids = get_member(spec["validation"], registry["rows"])
    labels = np.load(directory / "roles.npy")
    selection_ids = ids[labels == 0]
    evidence = evaluate_role(config, settings, seed, selection_ids, ids, labels == 0, "selection")
    save_evidence(directory, "selection", evidence)
    decisions = {}
    for economic in settings["economics"]:
        decision = choose(
            evidence["point"],
            evidence["lower"],
            evidence["support"],
            economic,
            len(selection_ids),
            settings["minimum_control_visits"],
        )
        decision["selected_ids_sha256"] = policy_hash(
            evidence, selection_ids, decision["model"], decision["reach_index"]
        )
        decisions[economic["name"]] = decision
    immutable_json(
        directory / "recommendations.json", {"provenance": provenance, "decisions": decisions}
    )
    recommendation_sha = file_sha256(directory / "recommendations.json")
    selection_sealed_at = now()
    selection = {
        "rows": len(selection_ids),
        "uncertainty": evidence["uncertainty"],
        "support": evidence["support"],
        "policies": policy_table(evidence),
        "marginal_point": evidence["point"].tolist(),
        "marginal_lower": evidence["lower"].tolist(),
    }
    del evidence
    gc.collect()
    # Crucial ordering: assessment scores and policy applications before assessment Y query.
    assessment_ids = ids[labels == 1]
    applications = {
        s["name"]: apply(decisions[s["name"]], s, len(assessment_ids))
        for s in settings["economics"]
    }
    ascores, _ = inputs(seed, ids, labels == 1)
    from marketing_uplift.policy_metrics import ranking

    aorders = {m: ranking(ascores[m], ascores["random"], assessment_ids) for m in MODELS}
    for application in applications.values():
        selected = application["ledger"]["selected"]
        m = application["model"]
        application["selected_ids_sha256"] = (
            id_hash(np.sort(assessment_ids[aorders[m][:selected]]))
            if m
            else id_hash(assessment_ids[:0])
        )
    immutable_json(directory / "assessment-applications.json", applications)
    del ascores, aorders
    immutable_json(
        directory / "assessment-start.json",
        {
            "selection_sealed_at": selection_sealed_at,
            "recommendations_sha256": recommendation_sha,
            "applications_sha256": file_sha256(directory / "assessment-applications.json"),
            "assessment_query_started_at": now(),
        },
    )
    # Assessment outcomes are first queried only after both recommendations/applications persist.
    assessed = evaluate_role(config, settings, seed, assessment_ids, ids, labels == 1, "assessment")
    save_evidence(directory, "assessment", assessed)
    for s in settings["economics"]:
        app = applications[s["name"]]
        assert (
            policy_hash(assessed, assessment_ids, app["model"], app["reach_index"])
            == app["selected_ids_sha256"]
        )
        app["comparisons"] = comparisons(assessed, app, s)
    if file_sha256(directory / "recommendations.json") != recommendation_sha:
        raise ContractError("Assessment changed sealed recommendations")
    result = {
        "seed": seed,
        "provenance": provenance,
        "scenario_keys": assessed["keys"],
        "recommendations_sha256": recommendation_sha,
        "selection": selection,
        "decisions": decisions,
        "applications": applications,
        "assessment": {
            "rows": len(assessment_ids),
            "uncertainty": assessed["uncertainty"],
            "support": assessed["support"],
            "policies": policy_table(assessed),
        },
        "elapsed_seconds": time.monotonic() - start,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "free_disk_bytes": shutil.disk_usage(".").free,
        "completed_at": now(),
        "memory_before": memory_before,
        "memory_after": memory_status(),
    }
    mlflow.set_tracking_uri(Path(config["tracking"]["directory"]).resolve().as_uri())
    mlflow.set_experiment("marketing-uplift-phase8-development")
    with mlflow.start_run(run_name=f"phase8-{seed}") as run:
        result["mlflow_run_id"] = run.info.run_id
        mlflow.log_params(
            {
                "protocol_sha256": digest,
                "outer_seed": seed,
                "replicates": settings["replicates"],
                "family_size": 300,
                "hypothetical_economics": True,
                "role_seed": seed + settings["role_seed_offset"],
            }
        )
        mlflow.log_dict(
            {
                "files": hashes,
                "provenance": provenance,
                "git_commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True
                ).strip(),
                "numpy": np.__version__,
            },
            "provenance.json",
        )
        mlflow.log_dict(settings, "settings.json")
        result["artifact_hashes"] = {
            p.name: file_sha256(p)
            for p in directory.iterdir()
            if p.is_file() and p.name != "result.json"
        }
        mlflow.log_dict(result, "result.json")
        for name in result["artifact_hashes"]:
            mlflow.log_artifact(str(directory / name), "private_artifacts")
        mlflow.log_metrics(
            {
                "elapsed_seconds": result["elapsed_seconds"],
                "peak_rss_kib": result["peak_rss_kib"],
                **{
                    f"{name}_selected": app["ledger"]["selected"]
                    for name, app in applications.items()
                },
            }
        )
        atomic_json(resultpath, result)
    return result


def run(config, first_only=False):
    settings, digest, hashes, registry, root, before, manifest = freeze(config)
    if not first_only:
        gatepath = root / "first-split-gate.json"
        firstpath = root / str(registry["development_splits"][0]["seed"]) / "result.json"
        if not gatepath.exists() or json.loads(gatepath.read_text()).get(
            "result_sha256"
        ) != file_sha256(firstpath):
            raise ContractError(
                "Run first split and decisions --verify-first-split before remaining splits"
            )
    results = []
    for spec in registry["development_splits"][: 1 if first_only else 5]:
        print(f"Phase 8 {spec['seed']}: starting/verified resume", flush=True)
        results.append(one(config, settings, digest, hashes, registry, spec, root, manifest))
        if protected(config) != before:
            raise ContractError("Protected Phase 6/7 artifacts changed")
        print(f"Phase 8 {spec['seed']}: completed; protected artifacts unchanged", flush=True)
    result = {
        "status": "first_split_complete" if first_only else "complete",
        "protocol_sha256": digest,
        "protocol_files": hashes,
        "settings": settings,
        "protected_before": before,
        "protected_unchanged": True,
        "roles": manifest,
        "splits": results,
    }
    atomic_json(
        Path("reports/phase_8_first_split.json" if first_only else "reports/phase_8_metrics.json"),
        result,
    )
    return result
