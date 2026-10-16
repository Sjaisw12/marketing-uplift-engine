"""Stage A data boundary; both real holdout interfaces are deliberately disabled."""

import json
from pathlib import Path

import numpy as np
import pyarrow as pa

from marketing_uplift.data_contract import FEATURES, ContractError, connection
from marketing_uplift.ingestion import parquet_path
from marketing_uplift.splits import get_member


class StageBDisabled(ContractError):
    pass


STAGE_B_BLOCKER = (
    "Stage B disabled: no verified separate approval bound to the exact lock/model manifest "
    "and no independently durable atomic create-once execution receipt service. "
    "Boolean flags, local files and environment variables cannot authorize holdout access."
)


def require_stage_b(*args, **kwargs):
    # Fail before opening any dataset, model, approval payload or receipt path.
    raise StageBDisabled(STAGE_B_BLOCKER)


def score_holdout_features(*args, **kwargs):
    """Future feature-only entry point; Stage A cannot score real holdout records."""
    require_stage_b(*args, **kwargs)


def evaluate_holdout_outcomes(*args, **kwargs):
    """Future outcome-only entry point; no functional real holdout reader exists."""
    require_stage_b(*args, **kwargs)


def begin_execution(*args, **kwargs):
    """Future durable receipt operation; do not create a fake local receipt."""
    require_stage_b(*args, **kwargs)


def check_development_ids(ids, allowed):
    ids = np.asarray(ids)
    if ids.ndim != 1 or ids.dtype.kind not in "iu" or len(ids) == 0:
        raise ContractError("Stage A requires nonempty integer development IDs")
    if np.any(ids[1:] <= ids[:-1]):
        raise ContractError("Development IDs must be unique and sorted")
    positions = np.searchsorted(allowed, ids)
    if np.any(positions >= len(allowed)) or not np.array_equal(allowed[positions], ids):
        raise ContractError("Stage A denies IDs outside the frozen development membership")


def development_batches(config, ids, columns):
    """Explicit whitelist/ID check before any Parquet connection is opened."""
    registry = json.loads(Path(config["experiment"]["split_registry"]).read_text())
    allowed = get_member(registry["memberships"]["development"], registry["rows"])
    check_development_ids(ids, allowed)
    if (
        not columns
        or len(set(columns)) != len(columns)
        or any(c not in ["row_id", *FEATURES, "treatment", "visit"] for c in columns)
    ):
        raise ContractError("Invalid Stage A development projection")
    with connection(config) as con:
        con.register("stage_a_ids", pa.table({"row_id": ids}))
        con.read_parquet(str(parquet_path(config))).create_view("stage_a_source")
        projection = ",".join("p." + c for c in columns)
        reader = con.execute(
            f"SELECT {projection} FROM stage_a_source p "
            "JOIN stage_a_ids USING(row_id) ORDER BY p.row_id"
        ).fetch_record_batch(config["resources"]["batch_rows"])
        yield from reader
