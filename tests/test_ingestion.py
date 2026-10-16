"""Verify value/ID fidelity, duplicate preservation, and feature leakage boundaries."""

import json

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from marketing_uplift import data_contract as dc
from marketing_uplift.features import assert_feature_columns, select_features
from marketing_uplift.ingestion import ingest, parquet_path, require_ingestion


def test_parquet_preserves_every_value_identifier_and_duplicate(source):
    config, rows, _ = source
    raw = dc.validate(config, full=True)
    evidence = ingest(config)
    table = pq.read_table(parquet_path(config))
    assert table.num_rows == len(rows)
    assert table["row_id"].to_pylist() == list(range(len(rows)))
    for j, name in enumerate(dc.COLUMNS):
        assert table[name].to_pylist() == [float(row[j]) for row in rows]
    assert evidence["row_mapping"] == raw["row_mapping"]
    assert evidence["rows_deduplicated"] == 0
    assert require_ingestion(config)["status"] == "passed"
    assert ingest(config)["parquet_sha256"] == evidence["parquet_sha256"]
    features = select_features(table)
    assert features.column_names == dc.FEATURES
    assert not set(dc.FLAGS + ["row_id"]) & set(features.column_names)


def test_parquet_id_value_swap_is_detected(source):
    config = source[0]
    dc.validate(config, full=True)
    ingest(config)
    path = parquet_path(config)
    table = pq.read_table(path)
    values = table["f0"].to_pylist()
    values[0], values[1] = values[1], values[0]
    table = table.set_column(table.column_names.index("f0"), "f0", pa.array(values))
    pq.write_table(table, path)
    with pytest.raises(dc.ContractError, match="mapping mismatch"):
        ingest(config)
    with pytest.raises(dc.ContractError, match="changed"):
        require_ingestion(config)


def test_ingestion_requires_matching_validation(source):
    config = source[0]
    with pytest.raises(dc.ContractError, match="full validation"):
        ingest(config)
    dc.validate(config, full=True)
    config["contract"]["visit_rate_bounds"] = [0.1, 0.9]
    with pytest.raises(dc.ContractError, match="does not match"):
        ingest(config)


@pytest.mark.parametrize("extra", ["exposure", "treatment", "visit", "conversion", "row_id"])
def test_leakage_gate_rejects_each_forbidden_column(extra):
    with pytest.raises(dc.ContractError, match="exactly f0-f11"):
        assert_feature_columns(dc.FEATURES + [extra])


def test_ingestion_does_not_modify_validation_evidence(source):
    config = source[0]
    dc.validate(config, full=True)
    before = json.loads(dc.VALIDATION.read_text())
    ingest(config)
    assert json.loads(dc.VALIDATION.read_text()) == before


def test_default_analysis_access_excludes_holdout(source):
    from marketing_uplift.features import development_relation
    from marketing_uplift.splits import get_member, split

    config = source[0]
    dc.validate(config, full=True)
    ingest(config)
    registry = split(config, holdout_only=True)
    with dc.connection(config) as con:
        with pytest.raises(dc.ContractError, match="Freeze all development"):
            development_relation(con, config)
    registry = split(config)
    with dc.connection(config) as con:
        relation = development_relation(con, config)
        observed = {row[0] for row in relation.project("row_id").fetchall()}
    assert observed == set(get_member(registry["memberships"]["development"], 80))
    assert not observed & set(get_member(registry["memberships"]["holdout"], 80))


def test_fresh_parquet_reconstruction_has_identical_row_mapping(source):
    config = source[0]
    dc.validate(config, full=True)
    first = ingest(config)
    parquet_path(config).unlink()
    second = ingest(config)
    assert second["row_mapping"] == first["row_mapping"]
    assert second["parquet_sha256"] == first["parquet_sha256"]
