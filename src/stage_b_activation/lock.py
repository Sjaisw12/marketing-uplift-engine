"""Additive portable lock. Never replaces/reseals any historical lock."""

import hashlib
import json
from pathlib import Path

from execution_safeguards.protocol import Denied, digest, file_hash
from production_adapter.plan import build as parent_plan
from production_adapter.plan import verify as verify_parent

LOCK = "reports/phase9/activation/execution_lock.json"


def build(root):
    root = Path(root)
    parent_sha = verify_parent(root)
    parent = parent_plan(root)
    config = json.loads((root / "activation/config.json").read_text())
    if config["execution_approved"] is not False:
        raise Denied("Preparation approval flag cannot enable execution")
    if (
        hashlib.sha256(config["age_recipient"].encode()).hexdigest()
        != config["age_recipient_sha256"]
    ):
        raise Denied("Encryption recipient fingerprint mismatch")
    files = dict(parent["files"])
    paths = [
        *root.glob("src/stage_b_activation/*.py"),
        *root.glob("tests/activation/*.py"),
        root / "activation/config.json",
        root / "docs/STAGE_B_ACTIVATION.md",
        root / ".github/workflows/activation.yml",
        root / "reports/phase9/production/execution_lock.json",
        root / "reports/phase9/activation/synthetic_transfer_evidence.json",
    ]
    files.update({p.relative_to(root).as_posix(): file_hash(p) for p in paths})
    return {
        "schema": 1,
        "parent_lock_sha256": parent_sha,
        "parent": parent,
        "config": config,
        "files": dict(sorted(files.items())),
    }


def verify(root):
    payload = build(root)
    stored = json.loads((Path(root) / LOCK).read_text())
    if stored != {"execution_lock_sha256": digest(payload), "payload": payload}:
        raise Denied("Activation integration lock stale/tampered")
    return {**payload, "lock_sha": digest(payload)}
