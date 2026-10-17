"""Explicit-projection Parquet adapter. Real holdout entry points are disabled."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pyarrow as pa

from execution_safeguards.protocol import Denied, file_hash
from marketing_uplift.data_contract import FEATURES, connection
from marketing_uplift.final_access import check_development_ids
from marketing_uplift.splits import get_member

from .plan import deny_execution


def ids_sha(ids):
    h = hashlib.sha256()
    for start in range(0, len(ids), 65536):
        h.update(ids[start : start + 65536].tobytes())
    return h.hexdigest()


def _batches(path, ids, columns, config):
    """Shared dormant query kernel, tested on synthetic Parquet/development IDs only."""
    if (
        columns not in [["row_id", *FEATURES], ["row_id", "treatment", "visit"]]
        or ids.dtype != np.dtype("<u8")
        or ids.ndim != 1
        or len(ids) == 0
        or np.any(ids[1:] <= ids[:-1])
    ):
        raise Denied("Invalid projection or source-row identifiers")
    offset = 0
    with connection(config) as con:
        con.register("selected_ids", pa.table({"row_id": ids}))
        con.read_parquet(str(path)).create_view("source_rows")
        query = "SELECT " + ",".join("p." + c for c in columns)
        query += " FROM source_rows p JOIN selected_ids USING(row_id) ORDER BY p.row_id"
        for batch in con.execute(query).fetch_record_batch(config["resources"]["batch_rows"]):
            expected_types = [pa.uint64()] + (
                [pa.float64()] * 12 if len(columns) == 13 else [pa.uint8()] * 2
            )
            if list(batch.schema.types) != expected_types or batch.schema.names != columns:
                raise Denied("Parquet projection type/schema mismatch; no coercion")
            if any(batch.column(i).null_count for i in range(batch.num_columns)):
                raise Denied("Null record; no dropping or imputation")
            actual = batch.column(0).to_numpy()
            if not np.array_equal(actual, ids[offset : offset + len(actual)]):
                raise Denied("Missing, duplicated or misaligned source records")
            for i in range(1, batch.num_columns):
                a = batch.column(i).to_numpy()
                if not np.isfinite(a).all() or (len(columns) == 3 and not np.isin(a, [0, 1]).all()):
                    raise Denied("Problematic numeric record; stop for review")
            offset += len(actual)
            yield batch
    if offset != len(ids):
        raise Denied("Incomplete source-row selection")


class ParquetAdapter:
    def __init__(self, root, plan):
        self.root, self.plan = Path(root), plan

    def _development(self, ids, config):
        registry = json.loads((self.root / config["experiment"]["split_registry"]).read_text())
        spec = dict(registry["memberships"]["development"])
        spec["path"] = str(self.root / spec["path"])
        allowed = get_member(spec, registry["rows"])
        check_development_ids(ids, allowed)  # before source opening/query
        path = self.root / self.plan["parquet"]["path"]
        if file_hash(path) != self.plan["parquet"]["sha256"]:
            raise Denied("Changed Parquet byte identity")
        return path

    def development_features(self, ids, config):
        path = self._development(ids, config)
        return _batches(path, ids, ["row_id", *FEATURES], config)

    def holdout_features(self, *args, **kwargs):
        deny_execution()

    def holdout_outcomes(self, *args, **kwargs):
        deny_execution()
