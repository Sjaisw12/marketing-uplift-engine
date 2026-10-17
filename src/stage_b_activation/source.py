"""Narrow production source; only the integrated signed-grant coordinator calls it."""

import copy
import json
import tomllib
from pathlib import Path

from execution_safeguards.protocol import Denied, digest, file_hash
from marketing_uplift.data_contract import FEATURES
from marketing_uplift.splits import get_member
from production_adapter.parquet import _batches
from production_adapter.scoring import load_models


class FrozenSource:
    def __init__(self, root, parent):
        self.root, self.parent = Path(root), copy.deepcopy(parent)
        self._parent_sha = digest(self.parent)
        self.config = tomllib.loads((self.root / "configs/project.toml").read_text())
        self._config_sha = digest(self.config)
        self.path = self.root / parent["parquet"]["path"]
        self._ids = None
        self._guard = None
        self._outcomes_opened = False

    def check(self):
        # Raw hashes/metadata only. No Parquet columns or records are opened here.
        if digest(self.parent) != self._parent_sha or digest(self.config) != self._config_sha:
            raise Denied("In-memory source/model/resource configuration changed")
        if file_hash(self.path) != self.parent["parquet"]["sha256"]:
            raise Denied("Frozen dataset byte identity changed")
        for name, model in self.parent["models"].items():
            path = self.root / self.parent["model_root"] / f"{name}.txt"
            if file_hash(path) != model["sha256"]:
                raise Denied("Frozen model bytes changed")
        registry = json.loads((self.root / "artifacts/splits.json").read_text())
        if registry["memberships"]["holdout"] != self.parent["holdout"]:
            raise Denied("Sealed membership metadata changed")
        # IDs are loaded only inside future signed execution, never during preparation.
        spec = {**self.parent["holdout"], "path": str(self.root / self.parent["holdout"]["path"])}
        self._ids = get_member(spec, registry["rows"])

    @property
    def ids(self):
        if self._ids is None:
            raise Denied("Source identities not checked")
        return self._ids

    def models(self):
        if self._guard is None:
            raise Denied("Models require authorized scoring capability")
        self._guard("feature_scoring_started")
        return load_models(self.root, self.parent)

    def features(self):
        if self._guard is None:
            raise Denied("Feature access requires signed coordinator capability")
        self._guard("feature_scoring_started")
        return _batches(self.path, self.ids, ["row_id", *FEATURES], self.config)

    def outcomes(self):
        if self._guard is None or self._outcomes_opened:
            raise Denied("Outcome access requires unused durable coordinator capability")
        self._guard("outcome_access_started")
        self._outcomes_opened = True
        return _batches(self.path, self.ids, ["row_id", "treatment", "visit"], self.config)
