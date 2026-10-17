"""Metadata-only production plan. Historical source, policy and locks stay unchanged."""

import base64
import hashlib
import json
import tomllib
from pathlib import Path

from execution_safeguards.journal import GitJournalTransport
from execution_safeguards.lock import verify as verify_parent
from execution_safeguards.protocol import Denied, digest, file_hash, verify_authorization
from execution_safeguards.receipt import GitHubTransport, ReceiptStore

LOCK = "reports/phase9/production/execution_lock.json"
KEY_SHA = "9c885530f96b2a4cc50afa8a2baaa1f1300a97720552e590dff824bdcc593800"


def build(root):
    root = Path(root)
    parent = verify_parent(root)
    config = json.loads((root / "production/config.json").read_text())
    key = base64.b64decode(config["public_key_base64"], validate=True)
    if (
        len(key) != 32
        or hashlib.sha256(key).hexdigest() != KEY_SHA
        or config["public_key_sha256"] != KEY_SHA
        or config["stage_b_enabled"]
        or config["real_executor_available"]
        or config["bulk_private_transfer_verified"]
    ):
        raise Denied("Key fingerprint or disabled production configuration mismatch")
    old = json.loads((root / "reports/phase9/policy_lock.json").read_text())
    model = json.loads((root / "reports/phase9/model_manifest.json").read_text())
    registry = json.loads((root / "artifacts/splits.json").read_text())
    stage = json.loads((root / "reports/phase9/stage_a.json").read_text())
    historical = json.loads(
        (root / "reports/phase9/coordinator/implementation_lock.json").read_text()
    )
    receipt_ref = historical["payload"]["receipt_ref"]
    prefix = receipt_ref.replace("stage-b-receipts/", "stage-b-journal/") + "/"
    observed = json.loads((root / "production/rulesets.json").read_text())["rulesets"]
    for rule_id, pattern in [
        (config["receipt_ruleset_id"], receipt_ref),
        (config["journal_ruleset_id"], prefix + "*"),
    ]:
        match = [r for r in observed if r["id"] == rule_id]
        if (
            len(match) != 1
            or match[0]["enforcement"] != "active"
            or match[0]["target"] != "tag"
            or match[0]["bypass_actors"]
            or match[0]["conditions"]["ref_name"] != {"include": [pattern], "exclude": []}
            or {r["type"] for r in match[0]["rules"]} != {"deletion", "update"}
        ):
            raise Denied("Unverified ruleset coverage/protection")
    paths = [
        *root.glob("src/production_adapter/*.py"),
        *root.glob("tests/production/*.py"),
        root / "production/config.json",
        root / "production/rulesets.json",
        root / "docs/PRODUCTION_ADAPTER.md",
        root / ".github/workflows/production-adapter.yml",
        root / "reports/phase9/coordinator/implementation_lock.json",
        root / "reports/phase9/stage_a.json",
    ]
    files = dict(historical["payload"]["files"])
    files.update({p.relative_to(root).as_posix(): file_hash(p) for p in paths})
    return {
        "schema": 1,
        "parent_lock_sha256": parent,
        "config": config,
        "stage_a_lock_sha256": old["lock_sha256"],
        "model_manifest_sha256": model["model_manifest_sha256"],
        "models": {
            m["job"]["name"]: {"sha256": m["model_sha256"], "features": m["job"]["features"]}
            for m in model["payload"]["models"]
        },
        "parquet": {
            "path": "data/processed/criteo-v2.1.parquet",
            **stage["protected_before"]["data/processed/criteo-v2.1.parquet"],
        },
        "model_root": stage["artifact_root"],
        "dataset_sha256": historical["payload"]["dataset_sha256"],
        "holdout": registry["memberships"]["holdout"],
        "receipt_ref": historical["payload"]["receipt_ref"],
        "journal_prefix": historical["payload"]["receipt_ref"].replace(
            "stage-b-receipts/", "stage-b-journal/"
        )
        + "/",
        "policies": {
            "primary": old["payload"]["primary"],
            "secondary": old["payload"]["secondary"],
        },
        "settings": tomllib.loads((root / "configs/phase9.toml").read_text()),
        "files": dict(sorted(files.items())),
    }


def verify(root):
    payload = build(root)
    stored = json.loads((Path(root) / LOCK).read_text())
    if stored != {"execution_lock_sha256": digest(payload), "payload": payload}:
        raise Denied("Production lock stale/tampered; new review required")
    return stored["execution_lock_sha256"]


def deny_execution():
    raise Denied(
        "Stage B disabled: separate exact-lock, authorization and bulk-backup approval required"
    )


class PreparedExecutor:
    def __init__(self, root):
        self.root = Path(root)
        self.lock_sha = verify(root)
        self.payload = build(root)

    def expected_authorization(self, not_before, expires_at):
        p, c = self.payload, self.payload["config"]
        # Owner-selected validity is explicit; identity/recipe bindings never come from envelope.
        return {
            "schema": 1,
            "purpose": "one-final-holdout-evaluation",
            "execution_lock_sha256": self.lock_sha,
            "model_manifest_sha256": p["model_manifest_sha256"],
            "dataset_sha256": p["dataset_sha256"],
            "holdout_sha256": p["holdout"]["sha256"],
            "parameters_sha256": digest(
                {"policies": p["policies"], "settings": p["settings"], "config": c}
            ),
            "owner": c["owner"],
            "execution_id": c["execution_id"],
            "public_key_sha256": c["public_key_sha256"],
            "not_before": not_before,
            "expires_at": expires_at,
        }

    def verify_authorization(self, envelope, not_before, expires_at, now=None):
        if verify(self.root) != self.lock_sha or build(self.root) != self.payload:
            raise Denied("Changed prepared execution identity")
        return verify_authorization(
            envelope,
            self.expected_authorization(not_before, expires_at),
            self.payload["config"]["public_key_base64"],
            now,
        )

    def inert_transports(self, reviewed_commit):
        p = self.payload
        return (
            ReceiptStore(GitHubTransport(reviewed_commit)),
            GitJournalTransport(reviewed_commit, p["dataset_sha256"], p["holdout"]["sha256"]),
        )

    def start(self, *args, **kwargs):
        deny_execution()

    score = seal = evaluate = recover = start
