"""Stage A rejects any holdout access before I/O; no local boolean bypass."""

import json
from pathlib import Path

import numpy as np
import pytest

from marketing_uplift import final_access
from marketing_uplift.data_contract import ContractError


@pytest.mark.parametrize(
    "api", ["score_holdout_features", "evaluate_holdout_outcomes", "begin_execution"]
)
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"approved": True},
        {"stage_b_enabled": True, "lock_sha256": "claimed", "model_manifest_sha256": "claimed"},
    ],
)
def test_all_real_holdout_interfaces_fail_closed(api, payload, monkeypatch):
    monkeypatch.setenv("STAGE_B_APPROVED", "true")
    monkeypatch.setattr(final_access, "connection", lambda *_: pytest.fail("Opened a dataset"))
    monkeypatch.setattr(
        Path, "open", lambda *a, **k: pytest.fail("Opened a local approval/receipt/data file")
    )
    with pytest.raises(final_access.StageBDisabled, match="Stage B disabled"):
        getattr(final_access, api)(**payload)


def test_reject_holdout_or_mixed_ids_before_connection(tmp_path, monkeypatch):
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({"rows": 10, "memberships": {"development": {}}}))
    config = {"experiment": {"split_registry": str(registry)}}
    monkeypatch.setattr(final_access, "get_member", lambda *_: np.array([0, 2, 4, 6, 8]))
    monkeypatch.setattr(
        final_access, "connection", lambda *_: pytest.fail("Opened Parquet for unauthorized IDs")
    )
    for ids in (np.array([1]), np.array([0, 1]), np.array([0, 0]), np.array([8, 2])):
        with pytest.raises(ContractError):
            list(final_access.development_batches(config, ids, ["row_id", "visit"]))
    with pytest.raises(ContractError, match="projection"):
        list(final_access.development_batches(config, np.array([0]), ["row_id", "exposure"]))


def test_disabled_workflow_cannot_be_enabled_by_dispatch_boolean():
    text = Path(".github/workflows/stage-b-disabled.yml").read_text()
    assert "if: ${{ false }}" in text
    assert "inputs:" not in text and "uplift" not in text
    stage_a = Path(".github/workflows/stage-a.yml").read_text()
    assert "make acquire" not in stage_a and "--reconstruct" not in stage_a
    assert "--verify-public-lock" in stage_a
