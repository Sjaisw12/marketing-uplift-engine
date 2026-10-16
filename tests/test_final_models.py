"""Synthetic fits verify exact feature boundaries and separately supplied S treatment."""

import lightgbm as lgb
import numpy as np

from marketing_uplift.baselines import predict
from marketing_uplift.data_contract import FEATURES
from marketing_uplift.final_fit_worker import fit_model
from marketing_uplift.final_stage_a import digest, primary_policy


def test_small_synthetic_arm_and_s_models_reload(tmp_path):
    rng = np.random.default_rng(55)
    x = rng.normal(size=(300, 12))
    t = np.arange(300) % 2
    y = rng.binomial(1, 0.2 + 0.3 * (x[:, 0] > 0))
    recipe = dict(
        rounds=3,
        learning_rate=0.05,
        num_leaves=7,
        min_data_in_leaf=5,
        max_bin=15,
        bin_construct_sample_cnt=200,
        num_threads=2,
    )
    for is_s in (False, True):
        mask = np.ones(300, dtype=bool) if is_s else t == 0
        m = fit_model(x, t, y, mask, recipe, 9, is_s)
        assert m.feature_name() == ([*FEATURES, "__intervention_treatment"] if is_s else FEATURES)
        path = tmp_path / f"model-{is_s}.txt"
        m.save_model(str(path))
        loaded = lgb.Booster(model_file=str(path))
        for intervention in (0, 1) if is_s else (None,):
            np.testing.assert_array_equal(
                predict(m, x, intervention), predict(loaded, x, intervention)
            )


def test_lock_digest_canonical_and_primary_is_identity():
    assert digest({"a": 1, "b": 2}) == digest({"b": 2, "a": 1})
    assert digest({"a": 1}) != digest({"a": 2})
    report = {
        "splits": [
            {
                "seed": 1,
                "decisions": {
                    "toy": dict(model=None, reach_index=0, reason_codes=["assumption_sensitive"])
                },
            }
        ]
    }
    policy = primary_policy([{"name": "toy"}], report)
    assert policy["model"] is None and policy["ranking"] is None
    assert policy["incremental_gain_relative_to_no_targeting"] == 0
    assert policy["identity_not_statistical_evidence"] and not policy["claim_of_optimality"]
