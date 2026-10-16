"""Membership tests never calculate holdout outcome statistics or treatment effects."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from marketing_uplift import data_contract as dc
from marketing_uplift.ingestion import ingest
from marketing_uplift.splits import get_member, initial_members, member_spec, split


def prepared(source):
    config = source[0]
    dc.validate(config, full=True)
    ingest(config)
    return config


def test_holdout_is_sealed_before_development_and_never_replaced(source):
    config = prepared(source)
    sealed = split(config, holdout_only=True)
    assert sealed["state"] == "holdout_sealed"
    assert sealed["development_splits"] == []
    assert sealed["memberships"]["holdout"]["rows"] == 12
    path = Path(sealed["memberships"]["holdout"]["path"])
    original = path.read_bytes()
    registry = split(config)
    assert registry["state"] == "complete"
    assert len(registry["development_splits"]) == 5
    holdout = get_member(registry["memberships"]["holdout"], 80)
    dev = get_member(registry["memberships"]["development"], 80)
    assert len(dev) == 68
    for entry in registry["development_splits"]:
        train = get_member(entry["train"], 80)
        validation = get_member(entry["validation"], 80)
        assert len(train) == 54 and len(validation) == 14
        assert not set(train) & set(validation)
        assert not (set(train) | set(validation)) & set(holdout)
        assert set(train) | set(validation) == set(dev)
    frozen = Path(config["experiment"]["split_registry"]).read_bytes()
    split(config)
    assert path.read_bytes() == original
    assert Path(config["experiment"]["split_registry"]).read_bytes() == frozen


def test_every_membership_reconstructs_identically(source):
    config = prepared(source)
    registry = split(config)
    specs = list(registry["memberships"].values())
    for entry in registry["development_splits"]:
        specs.extend([entry["train"], entry["validation"]])
    original = {spec["path"]: Path(spec["path"]).read_bytes() for spec in specs}
    frozen_registry = Path(config["experiment"]["split_registry"]).read_bytes()
    for spec in specs:
        Path(spec["path"]).unlink()
    with pytest.raises(dc.ContractError, match="Missing frozen"):
        split(config, verify_only=True)
    split(config, reconstruct_missing=True)
    assert Path(config["experiment"]["split_registry"]).read_bytes() == frozen_registry
    for name, content in original.items():
        assert Path(name).read_bytes() == content


def test_changed_seed_or_membership_stops_without_replacement(source):
    config = prepared(source)
    registry = split(config)
    config["experiment"]["holdout_seed"] += 1
    with pytest.raises(dc.ContractError, match="refusing replacement"):
        split(config)
    config["experiment"]["holdout_seed"] -= 1
    path = Path(registry["memberships"]["holdout"]["path"])
    ids = np.load(path)
    ids[0] = 999
    np.save(path, ids)
    corrupt = path.read_bytes()
    with pytest.raises(dc.ContractError, match="corrupt"):
        split(config, reconstruct_missing=True)
    assert path.read_bytes() == corrupt


def test_reconstruction_checks_all_frozen_hashes_before_restoring(source):
    config = prepared(source)
    registry = split(config)
    first = Path(registry["memberships"]["holdout"]["path"])
    first.unlink()
    registry["development_splits"][-1]["validation"]["sha256"] = "0" * 64
    Path(config["experiment"]["split_registry"]).write_text(json.dumps(registry))
    with pytest.raises(dc.ContractError, match="corrupt"):
        split(config, reconstruct_missing=True)
    assert not first.exists()


def test_stratification_and_membership_hash_convention(source):
    config = source[0]
    labels = np.tile(np.arange(4, dtype=np.uint8), 20)
    dev, holdout = initial_members(labels, config)
    assert np.array_equal(np.bincount(labels[holdout]), [3, 3, 3, 3])
    assert len(dev) + len(holdout) == len(labels)
    assert (
        member_spec("test", holdout)["sha256"]
        == hashlib.sha256(np.asarray(holdout, dtype="<u8").tobytes()).hexdigest()
    )
