"""Lossless typed staging with a verified source-row mapping."""

import hashlib
import json
from pathlib import Path

import duckdb

from marketing_uplift.data_contract import (
    COLUMNS,
    FEATURES,
    FLAGS,
    INGESTION,
    ContractError,
    atomic_json,
    connection,
    contract_signature,
    identity,
    mapping_digest,
    now,
    raw_view,
    require_validation,
    typed_query,
    verified_source,
)


def parquet_path(config):
    return Path(config["data"]["processed_directory"]) / "criteo-v2.1.parquet"


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_parquet(con, path, batch_rows=65536):
    con.read_parquet(str(path)).create_view("staged", replace=True)
    schema = con.execute("DESCRIBE staged").fetchall()
    expected = [("row_id", "UBIGINT")] + [(c, "DOUBLE") for c in FEATURES]
    expected += [(c, "UTINYINT") for c in FLAGS]
    if [(row[0], row[1]) for row in schema] != expected:
        raise ContractError("Parquet schema differs from declared typed schema")
    result = mapping_digest(con.execute("SELECT * FROM staged").fetch_record_batch(batch_rows))
    return result


def require_ingestion(config):
    validation = require_validation(config)
    if not INGESTION.exists() or not parquet_path(config).exists():
        raise ContractError("Verified Parquet and ingestion evidence are required")
    report = json.loads(INGESTION.read_text())
    if (
        report.get("contract_signature") != contract_signature(config)
        or report.get("row_mapping") != validation["row_mapping"]
        or report.get("status") != "passed"
        or file_sha256(parquet_path(config)) != report["parquet_sha256"]
    ):
        raise ContractError("Parquet bytes or ingestion provenance changed")
    return report


def ingest(config):
    validation = require_validation(config)
    header = verified_source(config)
    target = parquet_path(config)
    temporary = target.with_suffix(".parquet.partial")
    target.parent.mkdir(parents=True, exist_ok=True)
    if temporary.exists():
        raise ContractError("Incomplete Parquet staging exists; inspect it before retrying")
    existed = target.exists()
    try:
        with connection(config) as con:
            if not existed:
                raw_view(con, config, header)
                con.execute(
                    "COPY (" + typed_query() + ") TO ? "
                    "(FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 65536)",
                    [str(temporary)],
                )
            mapping = inspect_parquet(
                con,
                target if existed else temporary,
                config.get("resources", {}).get("batch_rows", 65536),
            )
            if mapping != validation["row_mapping"]:
                raise ContractError("Raw-to-Parquet row-to-identifier mapping mismatch")
        if not existed:
            temporary.replace(target)
        report = {
            "status": "passed",
            "source": identity(config),
            "contract_signature": contract_signature(config),
            "verified_at_utc": now(),
            "parquet_path": target.as_posix(),
            "parquet_size_bytes": target.stat().st_size,
            "parquet_sha256": file_sha256(target),
            "row_mapping": mapping,
            "columns": ["row_id"] + COLUMNS,
            "rows_dropped": 0,
            "rows_deduplicated": 0,
            "values_imputed": 0,
            "raw_to_parquet_mapping_verified": True,
        }
        atomic_json(INGESTION, report)
        return report
    except duckdb.Error as error:
        # DuckDB errors can include raw records. Preserve type, never row contents.
        raise ContractError(f"Parquet ingestion stopped: {type(error).__name__}") from None
    finally:
        temporary.unlink(missing_ok=True)
