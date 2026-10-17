"""Subprocess harness: invented Parquet, synthetic keys, local fake Git, fake encryption ONLY."""

import json
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

from execution_safeguards.bundle import atomic_json
from execution_safeguards.interfaces import NAMES
from execution_safeguards.protocol import Denied, digest, file_hash, strict_json
from execution_safeguards.receipt import AmbiguousWrite, ReceiptStore
from production_adapter.parquet import _batches
from stage_b_activation import backup
from stage_b_continuation.operator import Lease, Operator


class Files:
    namespace = "stage-b-receipts"

    def __init__(self, path, prefix="", ambiguous=False):
        self.path, self.prefix, self.ambiguous = Path(path), prefix, ambiguous
        self.path.mkdir(exist_ok=True)

    def filename(self, ref):
        return self.path / (ref.rsplit("/", 1)[1] + ".json")

    def list(self):
        return [self.prefix + p.stem for p in sorted(self.path.glob("*.json"))]

    def read(self, ref):
        p = self.filename(ref)
        return strict_json(p.read_bytes()) if p.exists() else None

    def create(self, ref, payload):
        try:
            atomic_json(self.filename(ref), payload)
        except FileExistsError as exc:
            raise Denied("Duplicate synthetic atomic ref") from exc
        if self.ambiguous and payload.get("stage") == "continuation_approved":
            raise AmbiguousWrite("Synthetic write succeeded but acknowledgement lost")


class Remote:
    def __init__(self, root):
        self.path = root / "remote-commit.json"

    def access(self):
        return "b" * 40

    def commit(self):
        return strict_json(self.path.read_bytes())["commit"] if self.path.exists() else None

    def publish(self, directory, transfer):
        sha = digest(transfer)[:40]
        atomic_json(self.path, {"commit": sha})
        return sha


class Model:
    def __init__(self, name):
        self.name = name

    def predict(self, x, **kwargs):
        assert x.shape[1] == (13 if self.name == "s_learner" else 12)
        return 1 / (1 + np.exp(-x[:, 0] / 10))


def operator(root, phase, instance=None):
    fixture = strict_json((root / "fixture.json").read_bytes())
    plan = fixture["plan"]
    source_path = root / "invented.parquet"
    expected = fixture["source_sha256"]
    journal = Files(root / "journal", plan["parent"]["journal_prefix"], phase == "ambiguous")

    def count(name):
        with (root / (name + ".calls")).open("ab") as out:
            out.write(b"called\n")
            out.flush()
            os.fsync(out.fileno())

    class Source:
        ids = np.arange(80, dtype=np.uint64)

        def check(self):
            if file_hash(source_path) != expected:
                raise Denied("Changed synthetic dataset/model identity")

        def models(self):
            return {n: Model(n) for n in NAMES}

        def features(self):
            count("features")
            return _batches(
                source_path, self.ids, ["row_id", *[f"f{i}" for i in range(12)]], fixture["project"]
            )

        def outcomes(self):
            events = [journal.read(ref) for ref in journal.list()]
            assert events[-1]["stage"] == "outcome_access_started"
            count("outcomes")
            if phase == "outcome_reader_crash":
                os.kill(os.getpid(), signal.SIGKILL)
            return _batches(
                source_path, self.ids, ["row_id", "treatment", "visit"], fixture["project"]
            )

    def fake_encrypt(binary, cfg, archive, cipher):
        # Simulated encryption; only synthetic files and NEVER confidentiality evidence.
        Path(cipher).write_bytes(b"SYNTHETIC-FAKE-CIPHER\n" + Path(archive).read_bytes())

    actual_export = backup.export_checkpoint

    def export(*a, **kw):
        return actual_export(*a, **kw, encryptor=fake_encrypt)

    backup.export_checkpoint = export
    clock = datetime.fromisoformat(fixture["start"] if phase == "part1" else fixture["resume_time"])
    c = Operator(
        plan,
        fixture["commit"],
        Source(),
        ReceiptStore(Files(root / "receipts")),
        journal,
        Remote(root),
        root / "private",
        instance or ("worker-a" if phase == "part1" else "worker-b"),
        lambda: None,
        lambda: clock,
        lease=Lease(root / "private"),
    )
    return c, fixture


def main():
    root, phase = Path(sys.argv[1]), sys.argv[2]
    c, fixture = operator(root, phase)
    try:
        if phase == "part1":
            c.start(fixture["authorization"], fixture["original_report"])
            c.score_features()
            transfer = c.export("fake-synthetic-encryption-only")
            pause = c.publish(transfer)
            atomic_json(root / "part1-pid.json", {"pid": os.getpid(), "tip": pause["journal_tip"]})
            print("SYNTHETIC_PUBLICATION_DURABLE", flush=True)
            # Parent kills this genuine process before starting the continuation process.
            while True:
                time.sleep(1)
        elif phase == "hold":
            print("SYNTHETIC_LEASE_HELD", flush=True)
            while True:
                time.sleep(1)
        else:
            pause = strict_json((root / "private/pause.json").read_bytes())
            proof = strict_json((root / "continue.json").read_bytes())
            if phase == "state_write_failure":
                import stage_b_continuation.operator as module

                real_atomic = module.atomic_json

                def fail_checkpoint(path, value):
                    if path.name == "continuation-approval.json":
                        raise OSError("Synthetic disk write failure")
                    return real_atomic(path, value)

                module.atomic_json = fail_checkpoint
            c.resume(pause, proof["approval"], proof["backup"], proof["preflight"])
            if phase == "premature":
                c.evaluate()
                raise AssertionError("Unsealed evaluation succeeded")
            c.seal(pause["transfer"], proof["backup"], proof["preflight"])
            if phase == "outcome_crash":
                c._append("outcome_access_started", {"checkpoint_sha256": digest(c.manifest)})
                os.kill(os.getpid(), signal.SIGKILL)
            result = c.evaluate()
            print(
                json.dumps(
                    {
                        "pid": os.getpid(),
                        "family": len(result["family"]),
                        "stage": c.journal.read(c.tip)[-1]["stage"],
                    }
                ),
                flush=True,
            )
    finally:
        c.close()


if __name__ == "__main__":
    main()
