"""Shared tiny synthetic dataset, isolated from the production archive."""

import copy
import csv
import gzip
import hashlib
import tomllib
from pathlib import Path

import pytest

from marketing_uplift import data_contract as dc

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def source(tmp_path, monkeypatch):
    config = tomllib.loads((ROOT / "configs/project.toml").read_text())
    monkeypatch.chdir(tmp_path)
    config["resources"]["min_free_disk_bytes"] = 0
    config["contract"]["treatment_rate_bounds"] = [0, 1]
    config["contract"]["visit_rate_bounds"] = [0, 1]
    # Repeated feature vectors deliberately survive. All four strata have ample members.
    rows = [
        [str(i % 3 + j / 4) for j in range(12)] + [str((i // 2) % 2), str(i % 2), "0", "0"]
        for i in range(80)
    ]

    def write(records=None, header=None):
        records = copy.deepcopy(rows if records is None else records)
        path = dc.source_path(config)
        path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(path, "wt", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(dc.COLUMNS if header is None else header)
            writer.writerows(records)
        config["data"]["rows"] = len(records)
        config["data"]["size_bytes"] = path.stat().st_size
        config["data"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        return config

    write()
    return config, rows, write
