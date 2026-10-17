"""Portable additive execution seal. Metadata only; never opens a dataset or model."""

import json
import tomllib
from pathlib import Path

from .protocol import Denied, cohort_ref, digest, file_hash

LOCK = "reports/phase9/safeguards/execution_lock.json"
STAGE_A_LOCK = "fbd0ec32f8d97bbc1ffe03dd4a16a7937390d4ac570becef83b109cbc3d32b93"
MODEL_MANIFEST = "2e91bdae68cad12604c6aff3a9337b62e40df383f1ce6b2d3d4c1c58e08b8c9e"


def build(root):
    root = Path(root)
    settings = json.loads((root / "safeguards/settings.json").read_text())
    if (
        settings["stage_b_enabled"]
        or settings["production_public_key"] is not None
        or settings["live_github_tested"]
        or settings["private_backup_verified"]
    ):
        raise Denied("Preparation release must remain disabled and unconfigured")
    old = json.loads((root / "reports/phase9/policy_lock.json").read_text())
    models = json.loads((root / "reports/phase9/model_manifest.json").read_text())
    if digest(old["payload"]) != old["lock_sha256"] or old["lock_sha256"] != STAGE_A_LOCK:
        raise Denied("Stage A lock changed")
    if (
        digest(models["payload"]) != models["model_manifest_sha256"]
        or models["model_manifest_sha256"] != MODEL_MANIFEST
        or old["payload"]["model_manifest_sha256"] != MODEL_MANIFEST
    ):
        raise Denied("Stage A model manifest changed")
    registry = json.loads((root / "artifacts/splits.json").read_text())
    config = tomllib.loads((root / "configs/project.toml").read_text())
    # Include every historical Stage A source hash. New code lives outside those globs.
    files = dict(old["payload"]["provenance"]["files"])
    for relative, expected in files.items():
        if file_hash(root / relative) != expected:
            raise Denied(f"Historical Stage A dependency changed: {relative}")
    paths = [
        *root.glob("src/execution_safeguards/*.py"),
        *root.glob("tests/safeguards/*.py"),
        root / "safeguards/settings.json",
        root / "docs/STAGE_B_SAFEGUARDS.md",
        root / ".github/workflows/safeguards.yml",
        root / "reports/phase9/policy_lock.json",
        root / "reports/phase9/model_manifest.json",
    ]
    files.update({p.relative_to(root).as_posix(): file_hash(p) for p in paths})
    return {
        "schema": 1,
        "stage_b_enabled": False,
        "stage_a_lock_sha256": old["lock_sha256"],
        "model_manifest_sha256": models["model_manifest_sha256"],
        "models": {m["job"]["name"]: m["model_sha256"] for m in models["payload"]["models"]},
        "dataset_sha256": config["data"]["sha256"],
        "holdout": registry["memberships"]["holdout"],
        "receipt_ref": cohort_ref(
            config["data"]["sha256"], registry["memberships"]["holdout"]["sha256"]
        ),
        "parameters_sha256": digest({"settings": settings, "stage_a_policy": old["payload"]}),
        "files": dict(sorted(files.items())),
        "excluded_from_self_hash": [LOCK, "completion reports and review prose"],
        "readiness": "synthetic-only; signer, GitHub protections and backup unverified",
    }


def verify(root):
    envelope = json.loads((Path(root) / LOCK).read_text())
    payload = build(root)
    if envelope != {"execution_lock_sha256": digest(payload), "payload": payload}:
        raise Denied("Execution lock stale or tampered; regenerate and obtain new review")
    return envelope["execution_lock_sha256"]
