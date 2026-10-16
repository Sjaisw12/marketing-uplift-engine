"""Freeze memberships without reporting or analyzing holdout outcomes."""

import fcntl
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

import duckdb
import numpy as np
import sklearn
from sklearn.model_selection import train_test_split

from marketing_uplift.data_contract import (
    ContractError,
    atomic_json,
    connection,
    contract_signature,
    identity,
    now,
)
from marketing_uplift.ingestion import file_sha256, parquet_path, require_ingestion

MEMBERS = Path("artifacts/memberships")
ALGORITHM = "sklearn.train_test_split/stratify-treatment-x-visit/sorted-u64le/v1"


@contextmanager
def split_lock():
    path = Path(".cache/phase3-splits.lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ContractError("Another split operation is running") from None
        yield


def protocol(config):
    exp = config["experiment"]
    return {
        key: exp[key]
        for key in (
            "holdout_fraction",
            "holdout_seed",
            "development_validation_fraction",
            "development_seeds",
            "stratify_by",
        )
    }


def labels_from_parquet(con, config, rows):
    """Read labels for mechanical stratification only; never emit holdout summaries."""
    labels = np.empty(rows, dtype=np.uint8)
    con.read_parquet(str(parquet_path(config))).create_view("split_source", replace=True)
    reader = con.execute("SELECT row_id, treatment, visit FROM split_source").fetch_record_batch(
        65536
    )
    offset = 0
    for batch in reader:
        ids = batch.column(0).to_numpy()
        if not np.array_equal(ids, np.arange(offset, offset + len(ids), dtype=np.uint64)):
            raise ContractError("Parquet source-row identifiers changed")
        labels[offset : offset + len(ids)] = (
            2 * batch.column(1).to_numpy() + batch.column(2).to_numpy()
        )
        offset += len(ids)
    if offset != rows:
        raise ContractError("Parquet row count changed before splitting")
    return labels


def canonical_ids(ids):
    return np.sort(np.asarray(ids, dtype="<u8"))


def member_spec(name, ids):
    return {
        "path": (MEMBERS / f"{name}.npy").as_posix(),
        "rows": len(ids),
        "sha256": hashlib.sha256(ids.tobytes()).hexdigest(),
        "encoding": "sorted uint64 little-endian row IDs; hash excludes npy header",
    }


def check_member(ids, spec, total):
    if (
        ids.ndim != 1
        or ids.dtype != np.dtype("<u8")
        or len(ids) != spec["rows"]
        or (len(ids) and (ids[-1] >= total or np.any(ids[1:] <= ids[:-1])))
        or hashlib.sha256(ids.tobytes()).hexdigest() != spec["sha256"]
    ):
        raise ContractError(f"Frozen membership is corrupt: {spec['path']}")


def publish_member(ids, spec, total):
    check_member(ids, spec, total)
    path = Path(spec["path"])
    if path.exists():
        check_member(np.load(path, mmap_mode="r", allow_pickle=False), spec, total)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            np.save(stream, ids, allow_pickle=False)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def get_member(spec, total):
    if not Path(spec["path"]).exists():
        raise ContractError(f"Missing frozen membership: {spec['path']}; use split --reconstruct")
    ids = np.load(spec["path"], mmap_mode="r", allow_pickle=False)
    check_member(ids, spec, total)
    return ids


def partition_check(left, right, parent, total):
    """Membership masks bound memory and prove disjointness and exact coverage."""
    mask = np.zeros(total, dtype=np.int8)
    mask[parent] = 1
    if np.any(mask[left] != 1):
        raise ContractError("Partition contains rows outside its parent")
    mask[left] = 0
    if np.any(mask[right] != 1):
        raise ContractError("Partitions overlap or contain rows outside their parent")
    mask[right] = 0
    if np.any(mask):
        raise ContractError("Partition coverage is incomplete")


def initial_members(labels, config):
    exp = config["experiment"]
    if exp["stratify_by"] != ["treatment", "visit"]:
        raise ContractError("Joint treatment x visit stratification is required")
    development, holdout = train_test_split(
        np.arange(len(labels), dtype="<u8"),
        test_size=exp["holdout_fraction"],
        random_state=exp["holdout_seed"],
        stratify=labels,
    )
    development, holdout = canonical_ids(development), canonical_ids(holdout)
    partition_check(development, holdout, np.arange(len(labels)), len(labels))
    return development, holdout


def development_members(development, labels, config, seed):
    train, validation = train_test_split(
        development,
        test_size=config["experiment"]["development_validation_fraction"],
        random_state=seed,
        stratify=labels[development],
    )
    train, validation = canonical_ids(train), canonical_ids(validation)
    partition_check(train, validation, development, len(labels))
    return train, validation


def registry_members(registry):
    yield from registry["memberships"].values()
    for split in registry["development_splits"]:
        yield split["train"]
        yield split["validation"]


def verify_registry(registry):
    if registry["state"] not in {"holdout_sealed", "complete"}:
        raise ContractError("Unrecognized frozen registry state")
    if registry["state"] == "complete":
        seeds = registry["protocol"]["development_seeds"]
        if (
            len(seeds) != 5
            or len(set(seeds)) != 5
            or [entry["seed"] for entry in registry["development_splits"]] != seeds
        ):
            raise ContractError("Frozen development split definitions are incomplete")
    elif registry["development_splits"]:
        raise ContractError("An incompletely sealed registry contains development splits")
    total = registry["rows"]
    for spec in registry_members(registry):
        get_member(spec, total)
    dev = get_member(registry["memberships"]["development"], total)
    holdout = get_member(registry["memberships"]["holdout"], total)
    partition_check(dev, holdout, np.arange(total), total)
    for split in registry["development_splits"]:
        train = get_member(split["train"], total)
        validation = get_member(split["validation"], total)
        # Exact coverage of development proves exclusion of every holdout row.
        partition_check(train, validation, dev, total)


def reconstruct(registry, labels, config):
    """Recompute every hash first, then restore only missing identical memberships."""
    total = len(labels)
    dev, holdout = initial_members(labels, config)
    for name, ids in (("development", dev), ("holdout", holdout)):
        check_member(ids, registry["memberships"][name], total)
    # First pass: do not publish anything unless every frozen split reproduces.
    for split in registry["development_splits"]:
        train, validation = development_members(dev, labels, config, split["seed"])
        check_member(train, split["train"], total)
        check_member(validation, split["validation"], total)
    for spec in registry_members(registry):
        if Path(spec["path"]).exists():
            get_member(spec, total)  # Never replace corrupt local data.
    for name, ids in (("development", dev), ("holdout", holdout)):
        publish_member(ids, registry["memberships"][name], total)
    for split in registry["development_splits"]:
        train, validation = development_members(dev, labels, config, split["seed"])
        publish_member(train, split["train"], total)
        publish_member(validation, split["validation"], total)


def split(config, *, holdout_only=False, verify_only=False, reconstruct_missing=False):
    with split_lock():
        ingestion = require_ingestion(config)
        path = Path(config["experiment"]["split_registry"])
        with connection(config) as con:
            if path.exists():
                registry = json.loads(path.read_text())
                if (
                    registry["source"] != identity(config)
                    or registry["contract_signature"] != contract_signature(config)
                    or registry["row_mapping"] != ingestion["row_mapping"]
                    or registry["protocol"] != protocol(config)
                    or registry["algorithm"] != ALGORITHM
                    or registry["sklearn_version"] != sklearn.__version__
                    or registry["numpy_version"] != np.__version__
                ):
                    raise ContractError(
                        "Frozen split source, protocol, or algorithm changed; refusing replacement"
                    )
                if reconstruct_missing:
                    labels = labels_from_parquet(con, config, registry["rows"])
                    reconstruct(registry, labels, config)
                verify_registry(registry)
            else:
                if verify_only or reconstruct_missing:
                    raise ContractError("No frozen registry exists")
                labels = labels_from_parquet(con, config, ingestion["row_mapping"]["rows"])
                dev, holdout = initial_members(labels, config)
                registry = {
                    "registry_version": 1,
                    "state": "holdout_sealed",
                    "sealed_at_utc": now(),
                    "source": identity(config),
                    "contract_signature": contract_signature(config),
                    "row_mapping": ingestion["row_mapping"],
                    "rows": len(labels),
                    "protocol": protocol(config),
                    "algorithm": ALGORITHM,
                    "sklearn_version": sklearn.__version__,
                    "numpy_version": np.__version__,
                    "duckdb_version": duckdb.__version__,
                    "rounding": "ceil(n * fraction), stratified allocation via sklearn",
                    "memberships": {
                        "development": member_spec("development", dev),
                        "holdout": member_spec("holdout", holdout),
                    },
                    "development_splits": [],
                    "holdout_outcome_analysis": "none; labels used for stratification only",
                }
                for name, ids in (("development", dev), ("holdout", holdout)):
                    publish_member(ids, registry["memberships"][name], len(labels))
                atomic_json(path, registry)  # Seal before any development split creation.
                verify_registry(registry)
            if reconstruct_missing:
                atomic_json(
                    Path("reports/split_reconstruction.json"),
                    {
                        "status": "passed",
                        "verified_at_utc": now(),
                        "source": identity(config),
                        "registry_sha256": file_sha256(path),
                        "memberships_reconstructed_and_hash_matched": len(
                            list(registry_members(registry))
                        ),
                        "membership_count": len(list(registry_members(registry))),
                        "row_mapping": ingestion["row_mapping"],
                        "holdout_excluded_from_all_development_splits": True,
                        "disjointness_and_coverage_verified": True,
                        "frozen_registry_unchanged": True,
                    },
                )
            if holdout_only or verify_only or reconstruct_missing:
                return registry
            seeds = config["experiment"]["development_seeds"]
            if len(seeds) != 5 or len(set(seeds)) != 5:
                raise ContractError("Exactly five distinct development seeds are required")
            if registry["state"] == "complete":
                if [entry["seed"] for entry in registry["development_splits"]] != seeds:
                    raise ContractError("Frozen development split registry is incomplete")
                return registry
            labels = labels_from_parquet(con, config, registry["rows"])
            dev = get_member(registry["memberships"]["development"], registry["rows"])
            for seed in seeds:
                train, validation = development_members(dev, labels, config, seed)
                entry = {
                    "seed": seed,
                    "train": member_spec(f"train-{seed}", train),
                    "validation": member_spec(f"validation-{seed}", validation),
                }
                for role, ids in (("train", train), ("validation", validation)):
                    publish_member(ids, entry[role], registry["rows"])
                registry["development_splits"].append(entry)
            registry.update(state="complete", development_frozen_at_utc=now())
            verify_registry(registry)
            atomic_json(path, registry)
            return registry
