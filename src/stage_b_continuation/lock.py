"""Child of the unchanged activation lock; no historical files are resealed."""

from pathlib import Path

from execution_safeguards.protocol import Denied, digest, file_hash, strict_json
from stage_b_activation.lock import verify as activation

LOCK = "reports/phase9/continuation/execution_lock.json"


def build(root):
    root = Path(root)
    old = activation(root)
    files = dict(old["files"])
    paths = [
        *root.glob("src/stage_b_continuation/*.py"),
        *root.glob("tests/continuation/*.py"),
        root / "docs/STAGE_B_CONTINUATION.md",
        root / ".github/workflows/continuation.yml",
        root / "reports/phase9/activation/execution_lock.json",
    ]
    files.update({p.relative_to(root).as_posix(): file_hash(p) for p in paths})
    return {
        "schema": 1,
        "activation_lock_sha256": old["lock_sha"],
        "parent": old["parent"],
        "config": {
            **old["config"],
            "continuation": "fresh signed owner grant, new worker, exact durable publication pause",
            "outcome_replay": "forbidden",
        },
        "files": dict(sorted(files.items())),
    }


def verify(root):
    payload = build(root)
    if strict_json((Path(root) / LOCK).read_bytes()) != {
        "execution_lock_sha256": digest(payload),
        "payload": payload,
    }:
        raise Denied("Continuation child lock changed; new review required")
    return {**payload, "lock_sha": digest(payload)}
