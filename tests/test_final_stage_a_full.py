"""Read-only Stage A verification: development probes and hashes, never holdout rows."""

import json
import tomllib
from pathlib import Path

import pytest

from marketing_uplift.final_stage_a import verify_public_lock
from marketing_uplift.final_verification import verify

pytestmark = pytest.mark.full_data
ROOT = Path(__file__).resolve().parents[1]


def test_stage_a_development_fits_lock_and_disabled_holdout(monkeypatch, record_property):
    monkeypatch.chdir(ROOT)
    config = tomllib.loads(Path("configs/project.toml").read_text())
    report = json.loads(Path("reports/phase9/stage_a.json").read_text())
    public = verify_public_lock()
    assert public["lock_sha256"] == report["lock_sha256"]
    assert not public["stage_b_enabled"] and not public["datasets_opened"]
    evidence = verify(config, report)
    record_property("stage_a_verification", json.dumps(evidence))
    assert evidence["models"] == 9 and evidence["no_holdout_access"]
    assert evidence["numerical_reference"]["family_size"] == 765
    assert evidence["development_probe_rows"] == 2048
    assert report["no_holdout_rows_read"] and report["no_holdout_predictions"]
