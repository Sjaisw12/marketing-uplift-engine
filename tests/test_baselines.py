"""Small LightGBM integration fixtures; no real-data recipe changes."""

import lightgbm as lgb
import numpy as np
import pytest

from marketing_uplift.baselines import design, parameters, predict, protocol
from marketing_uplift.data_contract import ContractError


def test_frozen_recipe_and_intervention_boundary():
    recipe, digest, hashes = protocol()
    assert recipe["rounds"] == 200 and recipe["min_data_in_leaf"] == 1000
    assert recipe["bootstrap_replicates"] == 2000 and len(digest) == 64
    assert hashes
    x = np.zeros((12, 12))
    assert design(x).shape == (12, 12)
    assert design(x, 1).shape == (12, 13)
    with pytest.raises(ContractError):
        design(np.zeros((12, 13)))
    with pytest.raises(ContractError):
        design(x, 2)


def test_real_lightgbm_adapter_intervention_and_reproducibility():
    recipe, _, _ = protocol()
    # Explicit synthetic-only recipe: 200 rows cannot meet production min-leaf 1000.
    recipe.update(min_data_in_leaf=2, rounds=5)
    rng = np.random.default_rng(8)
    x = rng.normal(size=(200, 12))
    t = rng.integers(0, 2, 200)
    y = (x[:, 0] + 3 * t > 1).astype(int)
    models = [
        lgb.train(
            parameters(recipe, 4),
            lgb.Dataset(design(x, t), label=y),
            num_boost_round=recipe["rounds"],
        )
        for _ in range(2)
    ]
    p0, p1 = predict(models[0], x, 0), predict(models[0], x, 1)
    np.testing.assert_array_equal(p1, predict(models[1], x, 1))
    assert (p1 - p0).mean() > 0
    assert x.shape[1] == 12


def test_extraction_matches_source_ids_and_excludes_holdout(source, tmp_path):
    from marketing_uplift import data_contract as dc
    from marketing_uplift.baselines import extract
    from marketing_uplift.ingestion import ingest
    from marketing_uplift.splits import get_member, split

    config = source[0]
    dc.validate(config, full=True)
    ingest(config)
    registry = split(config)
    holdout = get_member(registry["memberships"]["holdout"], registry["rows"])
    rows = np.asarray(source[1], dtype=float)
    for role in ("train", "validation"):
        member = registry["development_splits"][0][role]
        x, t, y, ids = extract(config, member, registry["rows"], tmp_path, role)
        assert np.intersect1d(ids, holdout).size == 0
        np.testing.assert_array_equal(x, rows[ids, :12])
        np.testing.assert_array_equal(t, rows[ids, 12])
        np.testing.assert_array_equal(y, rows[ids, 13])
