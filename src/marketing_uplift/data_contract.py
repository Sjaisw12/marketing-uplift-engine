"""Strict, bounded full-file contract checks; no exploratory or effect analysis."""

import csv
import gzip
import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import numpy as np

from marketing_uplift.acquisition import AcquisitionError, verify

FEATURES = [f"f{i}" for i in range(12)]
FLAGS = ["treatment", "visit", "conversion", "exposure"]
COLUMNS = FEATURES + FLAGS
DTYPE = np.dtype(
    [("row_id", "<u8")] + [(c, "<f8") for c in FEATURES] + [(c, "u1") for c in FLAGS], align=False
)
VALIDATION = Path("reports/validation.json")
INGESTION = Path("reports/ingestion.json")


class ContractError(Exception):
    """The pipeline must stop and preserve evidence for review."""


def now():
    return datetime.now(UTC).isoformat()


def atomic_json(path, value):
    import os
    import tempfile

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def source_path(config):
    return Path(config["data"]["raw_directory"]) / config["data"]["filename"]


def identity(config):
    return {
        key: config["data"][key]
        for key in ("repository", "filename", "revision", "sha256", "size_bytes")
    }


def contract_signature(config):
    return signature(
        {
            "data": config["data"],
            "contract": config["contract"],
            "row_mapping": "source-record-ordinal-zero-based/canonical-v1",
        }
    )


def connection(config):
    resources = config.get("resources", {})
    if shutil.disk_usage(Path.cwd()).free < resources.get("min_free_disk_bytes", 8589934592):
        raise ContractError("Insufficient free disk space for bounded Phase 3 staging")
    # Single-threaded source scanning is part of the stable row-ID contract.
    if resources.get("duckdb_threads", 1) != 1:
        raise ContractError("Deterministic source ingestion requires duckdb_threads=1")
    con = duckdb.connect(
        config={
            "threads": 1,
            "memory_limit": resources.get("duckdb_memory_limit", "2GB"),
            "temp_directory": str(Path(".cache/duckdb").resolve()),
            "max_temp_directory_size": resources.get("max_temp_directory_size", "6GB"),
            "preserve_insertion_order": True,
        }
    )
    return con


def verified_source(config):
    data = config["data"]
    if data["filename"] != "criteo-research-uplift-v2.1.csv.gz":
        raise ContractError("Incorrect corrected-v2.1 basename")
    if config["contract"]["feature_columns"] != FEATURES:
        raise ContractError("Feature allowlist must be exactly f0-f11")
    if set(config["contract"]["raw_columns"]) != set(COLUMNS):
        raise ContractError("Configured raw schema must contain the exact 16 columns")
    path = source_path(config)
    verify(path, data["size_bytes"], data["sha256"])
    with gzip.open(path, "rt", newline="", encoding="utf-8") as stream:
        header = next(csv.reader(stream, strict=True), [])
    if len(header) != 16 or len(set(header)) != 16 or set(header) != set(COLUMNS):
        raise ContractError("CSV header has missing, unexpected, or duplicate columns")
    return header


def source_record_audit(config):
    """Independently count CSV records, including blank or ragged records."""
    count = 0
    malformed = 0
    with gzip.open(source_path(config), "rt", newline="", encoding="utf-8") as stream:
        records = csv.reader(stream, strict=True)
        next(records)
        for record in records:
            count += 1
            malformed += len(record) != 16
    return {"records": count, "wrong_field_count": malformed, "parser": "stdlib csv strict"}


def raw_view(con, config, header):
    # Header is checked before DuckDB can rename duplicate columns. No inference,
    # ignored errors, padded records, replacements, or tolerance for broken rows.
    con.read_csv(
        str(source_path(config)),
        header=True,
        sep=",",
        compression="gzip",
        columns={c: "VARCHAR" for c in header},
        auto_detect=False,
        strict_mode=True,
        null_padding=False,
        ignore_errors=False,
        parallel=False,
    ).create_view("raw")


def typed_query():
    fields = [f'CAST("{c}" AS DOUBLE) AS "{c}"' for c in FEATURES]
    fields += [f'CAST("{c}" AS UTINYINT) AS "{c}"' for c in FLAGS]
    return (
        "SELECT CAST(row_number() OVER () - 1 AS UBIGINT) AS row_id, "
        + ", ".join(fields)
        + " FROM raw"
    )


def mapping_digest(reader):
    """Canonical little-endian per-row bytes, independent of Arrow batch size."""
    digest = hashlib.sha256()
    count = 0
    for batch in reader:
        records = np.empty(batch.num_rows, dtype=DTYPE)
        for name in DTYPE.names:
            values = batch.column(batch.schema.get_field_index(name))
            if values.null_count:
                raise ContractError("Null value found in typed mapping")
            records[name] = values.to_numpy(zero_copy_only=False)
        expected = np.arange(count, count + batch.num_rows, dtype=np.uint64)
        if not np.array_equal(records["row_id"], expected):
            raise ContractError("Source-row identifier mapping is not contiguous and ordered")
        digest.update(records.tobytes())
        count += batch.num_rows
    return {
        "rows": count,
        "sha256": digest.hexdigest(),
        "encoding": "row_id:<u8,f0-f11:<f8,flags:u1;packed;source-order;v1",
    }


def save_failure(report, error):
    report.update(status="failed", error=error, recorded_at_utc=now())
    path = Path("reports/contract_failures") / (now().replace(":", "-") + ".json")
    atomic_json(path, report)
    return path


def validate(config, *, full=False):
    if not full:
        raise ContractError(
            "Full-file contract validation requires --full; no sampled pass is allowed"
        )
    report = {
        "source": identity(config),
        "contract_signature": contract_signature(config),
        "scope": "mechanical full-file contract only; no holdout analysis",
    }
    try:
        header = verified_source(config)
        report["raw_header_order"] = header
        report["independent_csv_audit"] = source_record_audit(config)
        audit = report["independent_csv_audit"]
        if audit["wrong_field_count"] or audit["records"] != config["data"]["rows"]:
            raise ContractError("Independent CSV record count or field-width check failed")
        with connection(config) as con:
            raw_view(con, config, header)
            expressions = ["count(*) AS rows"]
            keys = []
            for column in COLUMNS:
                checks = {
                    "missing": f'"{column}" IS NULL',
                    "unparseable": (
                        f'"{column}" IS NOT NULL AND TRY_CAST("{column}" AS DOUBLE) IS NULL'
                    ),
                    "nonfinite": f'NOT isfinite(TRY_CAST("{column}" AS DOUBLE))',
                }
                if column in FLAGS:
                    checks["invalid_binary"] = f"\"{column}\" NOT IN ('0', '1')"
                for check, condition in checks.items():
                    keys.append((column, check))
                    expressions.append(f"count(*) FILTER (WHERE {condition})")
            expressions += [f'avg(TRY_CAST("{c}" AS DOUBLE))' for c in ("treatment", "visit")]
            result = con.execute("SELECT " + ", ".join(expressions) + " FROM raw").fetchone()
            counts = {c: {} for c in COLUMNS}
            for (column, check), value in zip(keys, result[1:], strict=False):
                counts[column][check] = value
            report["observed_rows"] = result[0]
            report["quality_counts"] = counts
            # Nonfinite means are represented safely in failure evidence.
            rates = {
                c: (float(v) if v is not None and np.isfinite(v) else None)
                for c, v in zip(("treatment", "visit"), result[-2:], strict=True)
            }
            report["reference_rates"] = rates
            errors = []
            if result[0] != config["data"]["rows"]:
                errors.append("row count mismatch")
            if any(value for checks in counts.values() for value in checks.values()):
                errors.append("missing, nonnumeric, nonfinite, or nonbinary values")
            for c in ("treatment", "visit"):
                low, high = config["contract"][f"{c}_rate_bounds"]
                if rates[c] is None or not low <= rates[c] <= high:
                    errors.append(f"{c} reference rate outside configured bounds")
            if errors:
                raise ContractError("; ".join(errors))
            report["row_mapping"] = mapping_digest(
                con.execute(typed_query()).fetch_record_batch(
                    config.get("resources", {}).get("batch_rows", 65536)
                )
            )
        # Bind the completed scans to the same compressed bytes.
        verify(source_path(config), config["data"]["size_bytes"], config["data"]["sha256"])
        report.update(
            status="passed",
            validated_at_utc=now(),
            expected_rows=config["data"]["rows"],
            row_id="zero-based CSV data-record ordinal; not a customer ID or feature",
            coercions="explicit finite float64 parsing and exact 0/1 integer parsing only",
            rows_dropped=0,
            rows_deduplicated=0,
            values_imputed=0,
        )
        atomic_json(VALIDATION, report)
        return report
    except (ContractError, AcquisitionError, duckdb.Error, OSError, EOFError, csv.Error) as error:
        message = str(error) if isinstance(error, ContractError) else type(error).__name__
        failure = save_failure(report, message)
        raise ContractError(f"Validation stopped: {message}; evidence: {failure}") from None


def require_validation(config):
    if not VALIDATION.exists():
        raise ContractError("Run full validation before ingestion")
    evidence = json.loads(VALIDATION.read_text())
    if evidence.get("status") != "passed" or evidence.get(
        "contract_signature"
    ) != contract_signature(config):
        raise ContractError("Validation evidence does not match current source/contract")
    return evidence
