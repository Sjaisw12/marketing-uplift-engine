"""Training-only nuisance-fold, feature-boundary and extraction integration tests."""

import numpy as np
import pytest

from marketing_uplift.advanced import calibration, fit, nuisance_folds, vector_overlap
from marketing_uplift.baselines import predict
from marketing_uplift.data_contract import ContractError


def test_folds_deterministic_balanced_exclusion():
    labels = nuisance_folds(1001, 777)
    np.testing.assert_array_equal(labels, nuisance_folds(1001, 777))
    assert np.ptp(np.bincount(labels)) <= 1
    seen = np.zeros(len(labels), dtype=int)
    for k in range(3):
        fitmask = labels != k
        held = labels == k
        assert not np.any(fitmask & held)
        seen[held] += 1
    assert np.all(seen == 1)


def test_arm_fit_feature_boundary_and_reload(tmp_path):
    from marketing_uplift.baselines import protocol

    recipe = protocol()[0]
    recipe.update(min_data_in_leaf=2, rounds=4)
    rng = np.random.default_rng(44)
    x = rng.normal(size=(200, 12))
    y = (x[:, 0] > 0).astype(int)
    model = fit(x, y, np.arange(200) % 2 == 0, recipe, 4, tmp_path / "arm.txt")
    import lightgbm as lgb

    np.testing.assert_array_equal(
        predict(model, x), predict(lgb.Booster(model_file=str(tmp_path / "arm.txt")), x)
    )
    assert model.feature_name() == [f"f{i}" for i in range(12)]
    with pytest.raises(ContractError):
        fit(np.ones((200, 13)), y, np.ones(200, dtype=bool), recipe, 4, tmp_path / "bad.txt")
    with pytest.raises(ContractError):
        fit(x, y, np.zeros(200, dtype=bool), recipe, 4, tmp_path / "bad.txt")


def test_calibration_edges_zero_one_and_invalid():
    result = calibration(
        np.array([0, 1, 0, 1]), np.array([0.0, 0.1, 0.6, 1.0]), [0.0, 0.1, 0.6, 1.0]
    )
    assert [b["records"] for b in result["bins"]] == [1, 1, 2]
    assert sum(b["visits"] for b in result["bins"]) == 2
    with pytest.raises(ContractError):
        calibration(np.array([0, 1]), np.array([0.0, np.nan]), [0.0, 1.0])


def test_exact_vector_overlap_without_deduplication(source):
    from marketing_uplift import data_contract as dc
    from marketing_uplift.ingestion import ingest
    from marketing_uplift.splits import get_member, split

    config = source[0]
    dc.validate(config, full=True)
    ingest(config)
    registry = split(config)
    spec = registry["development_splits"][0]
    train = get_member(spec["train"], registry["rows"])
    val = get_member(spec["validation"], registry["rows"])
    result = vector_overlap(config, train, val)
    vectors = [tuple(row[:12]) for row in source[1]]
    training = {vectors[i] for i in train}
    validation = {vectors[i] for i in val}
    assert result["shared_vectors"] == len(training & validation)
    assert result["validation_rows_matching_training"] == sum(vectors[i] in training for i in val)


def test_complete_synthetic_pipeline_shared_nuisance_and_resume(source, tmp_path, monkeypatch):
    import json
    import tomllib
    from pathlib import Path

    from marketing_uplift import data_contract as dc
    from marketing_uplift.advanced import one, prepare_folds
    from marketing_uplift.baselines import run_one
    from marketing_uplift.ingestion import ingest
    from marketing_uplift.splits import split

    root = Path(__file__).parents[1]
    config = source[0]
    dc.validate(config, full=True)
    ingest(config)
    registry = split(config)
    recipe = tomllib.loads((root / "configs/baselines.toml").read_text())
    recipe.update(rounds=3, min_data_in_leaf=2, bootstrap_replicates=20)
    settings = tomllib.loads((root / "configs/phase7.toml").read_text())
    settings["replicates"] = 20
    Path("configs").mkdir()
    # Explicit synthetic-only recipe; production files and model protocol are unchanged.
    Path("configs/baselines.toml").write_text(
        "\n".join(f"{k} = {json.dumps(v)}" for k, v in recipe.items())
    )
    monkeypatch.setattr(
        "marketing_uplift.baselines.subprocess.check_output", lambda *a, **k: "synthetic\n"
    )
    spec = registry["development_splits"][0]
    oldsplit = run_one(
        config, recipe, "synthetic6", {}, registry, spec, Path("artifacts/phase6/synthetic6")
    )
    old = {"protocol_sha256": "synthetic6", "splits": [oldsplit]}
    Path("reports/phase_6_metrics.json").write_text(json.dumps(old))
    private = Path("artifacts/phase7/synthetic7")
    prepare_folds(registry, settings, private)
    result = one(config, settings, "synthetic7", {}, registry, spec, old, private)
    assert result["evaluation"]["simultaneous_family_size"] == 10
    assert len(result["models"]) == 7
    assert all(m["features"] == dc.FEATURES for m in result["models"])
    assert len(result["fold_manifest"]["folds"]) == 3
    assert one(config, settings, "synthetic7", {}, registry, spec, old, private) == result
    (private / str(spec["seed"]) / "dr-m0.npy").write_bytes(b"corrupt")
    with pytest.raises(ContractError, match="artifact mismatch"):
        one(config, settings, "synthetic7", {}, registry, spec, old, private)
