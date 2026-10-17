"""No live Git, real keys or real holdout inputs; subprocesses are synthetic mocks."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from execution_safeguards.protocol import Denied, digest, file_hash
from execution_safeguards.receipt import AmbiguousWrite
from stage_b_activation.backup import encrypt
from stage_b_activation.transport import MAIN, JournalRunner, PrivateRemote


def test_verified_binary_and_exact_age_recipient(tmp_path, monkeypatch):
    binary = tmp_path / "age"
    binary.write_bytes(b"synthetic executable fixture only")
    archive = tmp_path / "synthetic.tar"
    archive.write_bytes(b"invented checkpoint")
    cipher = tmp_path / "synthetic.age"
    config = {
        "age_tool": {"binary_sha256": file_hash(binary)},
        "age_recipient": "synthetic-recipient",
    }
    commands = []

    def run(args, **kwargs):
        commands.append(args)
        Path(args[args.index("--output") + 1]).write_bytes(
            b"age-encryption.org/v1\n-> X25519 fake\n"
        )
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("stage_b_activation.backup.subprocess.run", run)
    encrypt(binary, config, archive, cipher)
    assert commands == [
        [
            str(binary),
            "--encrypt",
            "--recipient",
            "synthetic-recipient",
            "--output",
            str(cipher),
            str(archive),
        ]
    ]
    with pytest.raises(Denied):
        encrypt(binary, config, archive, cipher)
    config["age_tool"]["binary_sha256"] = "0" * 64
    with pytest.raises(Denied):
        encrypt(binary, config, archive, tmp_path / "new.age")
    assert len(commands) == 1


@pytest.mark.parametrize("failure", ["exit", "timeout", "bad-header"])
def test_encryption_failure_is_not_retried(tmp_path, monkeypatch, failure):
    binary = tmp_path / "fixture"
    binary.write_bytes(b"invented executable")
    config = {"age_tool": {"binary_sha256": file_hash(binary)}, "age_recipient": "synthetic"}
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        if failure == "timeout":
            from subprocess import TimeoutExpired

            raise TimeoutExpired(args, 1)
        Path(args[args.index("--output") + 1]).write_bytes(b"wrong header")
        return SimpleNamespace(returncode=1 if failure == "exit" else 0)

    monkeypatch.setattr("stage_b_activation.backup.subprocess.run", run)
    with pytest.raises(Denied):
        encrypt(binary, config, tmp_path / "archive", tmp_path / "cipher")
    assert len(calls) == 1


@pytest.mark.parametrize(
    "command",
    [
        ["push", "origin", "HEAD:refs/heads/main"],
        ["push", "--porcelain", "--force", MAIN, "HEAD:refs/tags/other"],
        [
            "push",
            "--porcelain",
            "--force-with-lease=refs/tags/other:",
            MAIN,
            "a" * 40 + ":refs/tags/other",
        ],
        ["config", "credential.helper", "untrusted"],
        ["fetch", "--all"],
    ],
)
def test_main_and_unrelated_git_writes_denied_before_subprocess(tmp_path, monkeypatch, command):
    def forbidden(*args, **kwargs):
        pytest.fail("Unauthorized subprocess")

    monkeypatch.setattr("stage_b_activation.transport.subprocess.run", forbidden)
    runner = JournalRunner(
        tmp_path,
        "refs/tags/stage-b-receipts/" + "1" * 64 + "/" + "2" * 64,
        "refs/tags/stage-b-journal/" + "1" * 64 + "/" + "2" * 64 + "/",
    )
    with pytest.raises(Denied):
        runner(["git", *command])


def test_scoped_create_only_git_argv_and_timeout(tmp_path, monkeypatch):
    ref = "refs/tags/stage-b-receipts/" + "1" * 64 + "/" + "2" * 64
    runner = JournalRunner(tmp_path, ref, ref.replace("receipts", "journal") + "/")
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=0, stdout=b"synthetic-new-tag")

    monkeypatch.setattr("stage_b_activation.transport.subprocess.run", run)
    args = ["git", "push", "--porcelain", f"--force-with-lease={ref}:", MAIN, "a" * 40 + ":" + ref]
    assert runner(args) == "synthetic-new-tag"
    assert calls[0][-3:] == [f"--force-with-lease={ref}:", MAIN, "a" * 40 + ":" + ref]

    def lost(*args, **kwargs):
        from subprocess import TimeoutExpired

        raise TimeoutExpired("synthetic git", 1)

    monkeypatch.setattr("stage_b_activation.transport.subprocess.run", lost)
    with pytest.raises(AmbiguousWrite):
        runner(args)


def test_private_publish_explicit_ciphertext_allowlist(tmp_path, monkeypatch):
    from execution_safeguards.bundle import atomic_json

    publish = tmp_path / "publish"
    (publish / "encrypted").mkdir(parents=True)
    data = b"only synthetic fake ciphertext"
    (publish / "encrypted/part-000000.bin").write_bytes(data)
    catalog = {"synthetic_only": True}
    atomic_json(publish / "catalog.json", catalog)
    transfer = {
        "catalog_sha256": digest(catalog),
        "parts": [
            {
                "path": "encrypted/part-000000.bin",
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        ],
    }
    atomic_json(publish / "transfer.json", transfer)
    # Plaintext is deliberately present beside publish. It must never be staged.
    (tmp_path / "private-checkpoint.tar").write_bytes(b"invented plaintext")
    remote = PrivateRemote(tmp_path, "stage-b-checkpoint-v1")
    calls, published = [], []

    def run(args, **kwargs):
        calls.append(args)
        text = ""
        if "ls-remote" in args:
            text = ("a" * 40 + "\trefs/heads/stage-b-checkpoint-v1\n") if published else ""
        elif "clone" in args:
            dest = Path(args[-1])
            dest.mkdir()
            (dest / ".git").mkdir()
            (dest / "README.md").write_text("private transfer")
        elif "diff" in args:
            text = "transfer.json\ncatalog.json\nencrypted/part-000000.bin\n"
        elif "rev-parse" in args:
            text = "a" * 40 + "\n"
        elif "push" in args:
            published.append(True)
            text = "*\tHEAD:refs/heads/stage-b-checkpoint-v1\t[new branch]\n"
        return SimpleNamespace(returncode=0, stdout=text.encode())

    monkeypatch.setattr("stage_b_activation.transport.subprocess.run", run)
    assert remote.publish(publish, transfer) == "a" * 40
    staged = next(a for a in calls if "add" in a)
    assert staged[staged.index("--") + 1 :] == [
        "transfer.json",
        "catalog.json",
        "encrypted/part-000000.bin",
    ]
    with pytest.raises(Denied):
        remote.publish(publish, transfer)
    assert sum("push" in a for a in calls) == 1


def test_portable_lock_and_draft_is_non_signable(tmp_path):
    from stage_b_activation.authorization import draft
    from stage_b_activation.lock import LOCK, build, verify

    root = Path(__file__).resolve().parents[2]
    plan = verify(root)
    payload = build(root)
    for name in payload["files"]:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((root / name).read_bytes())
    lock = tmp_path / LOCK
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_bytes((root / LOCK).read_bytes())
    assert verify(tmp_path) == plan
    assert (
        draft(plan)["not_before"]
        is draft(plan)["expires_at"]
        is draft(plan)["reviewed_commit"]
        is None
    )
    config = tmp_path / "activation/config.json"
    changed = json.loads(config.read_text())
    changed["execution_approved"] = True
    config.write_text(json.dumps(changed))
    with pytest.raises(Denied):
        verify(tmp_path)


def test_forged_real_owner_grant_cannot_construct_source(monkeypatch):
    from stage_b_activation.authorization import draft
    from stage_b_activation.coordinator import production
    from stage_b_activation.lock import verify

    root = Path(__file__).resolve().parents[2]
    plan = verify(root)

    # No real source, model or membership is opened: only public repository metadata.
    def no_source(*args, **kwargs):
        pytest.fail("Real source constructed for forged approval")

    monkeypatch.setattr("stage_b_activation.coordinator.FrozenSource", no_source)
    monkeypatch.setattr("stage_b_activation.authorization.validate", lambda *a, **k: "0" * 64)
    payload = {
        **draft(plan),
        "reviewed_commit": "a" * 40,
        "preflight_sha256": "0" * 64,
        "not_before": "2026-10-17T00:00:00+00:00",
        "expires_at": "2026-10-18T00:00:00+00:00",
    }
    # Real checkout commit is deliberately mismatched as an additional independent binding check.
    envelope = {
        "payload": payload,
        "signature": __import__("base64").b64encode(b"\0" * 64).decode(),
    }
    with pytest.raises(Denied):
        production(root, "/never-created", "worker", envelope, {})


def test_unbound_real_adapters_deny_before_record_io(monkeypatch):
    from stage_b_activation.source import FrozenSource

    source = FrozenSource.__new__(FrozenSource)
    source._guard = None
    source._outcomes_opened = False

    def forbidden(*args, **kwargs):
        pytest.fail("Ungated record I/O")

    monkeypatch.setattr("stage_b_activation.source._batches", forbidden)
    with pytest.raises(Denied):
        source.models()
    with pytest.raises(Denied):
        source.features()
    with pytest.raises(Denied):
        source.outcomes()


def test_identical_receipt_race_requires_confirmed_new_tag():
    from execution_safeguards.protocol import cohort_ref
    from stage_b_activation.transport import StrictReceiptTransport

    receipt = {"dataset_sha256": "1" * 64, "holdout_sha256": "2" * 64}
    replies = iter(["*\tobject:ref\t[new tag]\n", "=\tobject:ref\t[up to date]\n"])

    def runner(args, data=None):
        if args[1] == "mktag":
            return "b" * 40 + "\n"
        if args[1] == "push":
            return next(replies)
        raise AssertionError("Unexpected synthetic command")

    first = StrictReceiptTransport("a" * 40, runner)
    second = StrictReceiptTransport("a" * 40, runner)
    ref = cohort_ref("1" * 64, "2" * 64)
    first.create(ref, receipt)
    with pytest.raises(AmbiguousWrite, match="not confirmed NEW"):
        second.create(ref, receipt)
