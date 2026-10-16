"""Feature export boundary: no interventions, outcomes, exposure, or identifiers."""

from marketing_uplift.data_contract import FEATURES, ContractError


def assert_feature_columns(columns):
    if list(columns) != FEATURES:
        raise ContractError("Feature export must contain exactly f0-f11 in canonical order")


def select_features(table):
    """Return only approved predictors from a PyArrow table; never learn transforms."""
    result = table.select(FEATURES)
    assert_feature_columns(result.column_names)
    return result


def development_relation(con, config):
    """Default analysis boundary: join only verified development row memberships."""
    import pyarrow as pa

    from marketing_uplift.ingestion import parquet_path
    from marketing_uplift.splits import get_member, split

    registry = split(config, verify_only=True)
    if registry["state"] != "complete":
        raise ContractError("Freeze all development splits before exposing analysis data")
    ids = get_member(registry["memberships"]["development"], registry["rows"])
    con.register("_development_ids", pa.table({"row_id": ids}))
    con.read_parquet(str(parquet_path(config))).create_view("_audited_source", replace=True)
    return con.sql("SELECT p.* FROM _audited_source p JOIN _development_ids d USING (row_id)")
