"""Portable public-only locks. No private datasets or model weights needed."""

import json
import shutil
from pathlib import Path

import pytest

from execution_safeguards.lock import LOCK, build, verify
from execution_safeguards.protocol import Denied, digest

ROOT = Path(__file__).resolve().parents[2]


def relocated(root, destination):
    payload = build(root)
    for name in payload["files"]:
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, path)
    return payload


def test_portability_and_tampered_source(tmp_path):
    payload = relocated(ROOT, tmp_path)
    assert build(tmp_path) == payload
    target = tmp_path / LOCK
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"execution_lock_sha256": digest(payload), "payload": payload}))
    assert verify(tmp_path) == digest(payload)
    (tmp_path / "src/execution_safeguards/state.py").write_text("# changed execution code\n")
    with pytest.raises(Denied, match="stale or tampered"):
        verify(tmp_path)


def test_historical_lock_and_settings_tampering(tmp_path):
    relocated(ROOT, tmp_path)
    path = tmp_path / "reports/phase9/policy_lock.json"
    old = json.loads(path.read_text())
    old["payload"]["primary"]["reach"] = 0.1
    old["lock_sha256"] = digest(old["payload"])
    path.write_text(json.dumps(old))
    with pytest.raises(Denied, match="Stage A lock changed"):
        build(tmp_path)
    shutil.copyfile(ROOT / "reports/phase9/policy_lock.json", path)
    settings = tmp_path / "safeguards/settings.json"
    values = json.loads(settings.read_text())
    values["stage_b_enabled"] = True
    settings.write_text(json.dumps(values))
    with pytest.raises(Denied, match="disabled"):
        build(tmp_path)


def test_frozen_source_tampering_detected(tmp_path):
    relocated(ROOT, tmp_path)
    (tmp_path / "src/marketing_uplift/final_metrics.py").write_text("# tamper\n")
    with pytest.raises(Denied, match="Historical Stage A dependency changed"):
        build(tmp_path)
