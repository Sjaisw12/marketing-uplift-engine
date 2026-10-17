"""Local Git persistence plus hostile synthetic archive fixtures; no live writes."""

import io
import subprocess
import tarfile
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from execution_safeguards.bundle import export_bundle, restore_bundle
from execution_safeguards.checkpoints import snapshot
from execution_safeguards.journal import GitJournalTransport, Journal
from execution_safeguards.protocol import Denied, digest
from execution_safeguards.receipt import AmbiguousWrite


def test_git_journal_two_client_race_persistence_and_noop_detection(tmp_path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    seed = tmp_path / "seed"
    subprocess.run(["git", "init", str(seed)], check=True, capture_output=True)
    tree = (
        subprocess.run(["git", "mktree"], cwd=seed, input=b"", check=True, capture_output=True)
        .stdout.decode()
        .strip()
    )
    commit = (
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Synthetic",
                "-c",
                "user.email=test@invalid",
                "commit-tree",
                tree,
                "-m",
                "fixture",
            ],
            cwd=seed,
            check=True,
            capture_output=True,
        )
        .stdout.decode()
        .strip()
    )
    subprocess.run(
        ["git", "push", str(remote), f"{commit}:refs/heads/fixture"],
        cwd=seed,
        check=True,
        capture_output=True,
    )
    barrier = threading.Barrier(2)
    clients = []
    for i in range(2):
        client = tmp_path / f"client{i}"
        subprocess.run(["git", "init", str(client)], check=True, capture_output=True)
        subprocess.run(
            ["git", "fetch", str(remote), commit], cwd=client, check=True, capture_output=True
        )

        def runner(argv, data=None, client=client):
            assert not any(a.startswith(("https:", "http:", "ssh:")) for a in argv)
            if argv[1] == "push" and barrier is not None:
                barrier.wait(timeout=10)
            p = subprocess.run(argv, input=data, cwd=client, capture_output=True)
            if p.returncode:
                raise OSError("local Git rejection")
            return p.stdout.decode()

        adapter = GitJournalTransport(commit, "1" * 64, "2" * 64, runner)
        adapter.remote = str(remote)
        clients.append(adapter)
    binding = {
        "receipt_sha256": "a" * 64,
        "execution_lock_sha256": "b" * 64,
        "execution_id": "synthetic",
        "owner": "fixture",
    }
    evidence = {"authorization_sha256": "c" * 64, "receipt_sha256": "a" * 64}

    def append(i):
        try:
            return Journal(clients[i], binding).append(
                "receipt_verified", evidence, f"writer-{i}", digest([])
            )
        except Denied:
            return None

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(append, [0, 1]))
    assert sum(bool(v) for v in results) == 1
    barrier = None
    events = Journal(clients[0], binding).read()
    assert len(events) == 1
    assert Journal(clients[1], binding).read() == events
    # Same object push is a Git no-op: must NOT be accepted as a fresh event claim.
    with pytest.raises(AmbiguousWrite, match="NEW journal tag"):
        clients[0].create(clients[0].prefix + "000000", events[0])
    assert Journal(clients[0], binding).read() == events


def test_default_journal_transport_never_accesses_github():
    transport = GitJournalTransport("a" * 40, "1" * 64, "2" * 64)
    with pytest.raises(Denied, match="disabled"):
        transport.list()
    with pytest.raises(Denied):
        transport.check_ref("refs/tags/something-else/000000")


def test_bundle_transfer_restore_missing_corrupted_and_bounded(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "predictions.bin").write_bytes(b"synthetic-only-predictions")
    manifest = snapshot(source, ["predictions.bin"], {"execution": "synthetic"})
    bundle = tmp_path / "checkpoint.tar"
    export_bundle(source, manifest, bundle)
    restored = tmp_path / "owner-restored"
    assert restore_bundle(bundle, restored, digest(manifest), 4096) == manifest
    assert (restored / "predictions.bin").read_bytes() == (source / "predictions.bin").read_bytes()
    with pytest.raises(Denied):
        restore_bundle(bundle, restored, digest(manifest), 4096)
    with pytest.raises(Denied):
        restore_bundle(bundle, tmp_path / "too-big", digest(manifest), 1)
    with pytest.raises(Denied):
        restore_bundle(bundle, tmp_path / "wrong", "0" * 64, 4096)
    (source / "predictions.bin").write_bytes(b"corrupt")
    with pytest.raises(Denied):
        export_bundle(source, manifest, tmp_path / "bad.tar")
    with pytest.raises(FileNotFoundError):
        restore_bundle(tmp_path / "missing.tar", tmp_path / "absent", digest(manifest), 4096)


@pytest.mark.parametrize(
    "name,kind",
    [
        ("../escape", "file"),
        ("/absolute", "file"),
        ("files/link", "symlink"),
        ("files/x", "duplicate"),
    ],
)
def test_unsafe_archives_never_escape_destination(tmp_path, name, kind):
    archive = tmp_path / "hostile.tar"
    with tarfile.open(archive, "w") as out:
        info = tarfile.TarInfo(name)
        if kind == "symlink":
            info.type = tarfile.SYMTYPE
            info.linkname = "../../escape"
            out.addfile(info)
        else:
            info.size = 1
            out.addfile(info, io.BytesIO(b"x"))
            if kind == "duplicate":
                out.addfile(info, io.BytesIO(b"x"))
    with pytest.raises(Denied):
        restore_bundle(archive, tmp_path / "restored", "0" * 64, 4096)
    assert not (tmp_path / "escape").exists() and not (tmp_path / "restored").exists()
