"""Transport mocks and real LOCAL bare Git tests; never writes to GitHub."""

import copy
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from execution_safeguards.protocol import Denied
from execution_safeguards.receipt import (
    AmbiguousWrite,
    GitHubTransport,
    ReceiptStore,
    receipt_for,
)


def sample():
    return receipt_for(
        {
            "execution_lock_sha256": "a" * 64,
            "model_manifest_sha256": "b" * 64,
            "dataset_sha256": "c" * 64,
            "holdout_sha256": "d" * 64,
            "parameters_sha256": "e" * 64,
            "owner": "owner",
            "execution_id": "id",
        },
        "f" * 64,
    )


class MemoryTransport:
    def __init__(self):
        self.values = {}
        self.lock = threading.Lock()

    def read(self, ref):
        return copy.deepcopy(self.values.get(ref))

    def create(self, ref, payload):
        with self.lock:
            if ref in self.values:
                raise Denied("Already exists")
            self.values[ref] = copy.deepcopy(payload)


def test_create_verify_duplicate_and_changed_owner():
    backend = MemoryTransport()
    store = ReceiptStore(backend)
    p = sample()
    assert store.claim(p) == store.verify(p)
    for changed in [p, dict(p, owner="other"), dict(p, execution_lock_sha256="0" * 64)]:
        with pytest.raises(Denied):
            ReceiptStore(backend).claim(changed)
    with pytest.raises(Denied):
        store.verify(dict(p, owner="other"))
    backend.values[store.ref(p)]["owner"] = "tampered"
    with pytest.raises(Denied):
        store.verify(p)


@pytest.mark.parametrize("after_write", [False, True])
def test_ambiguous_write_never_succeeds_or_automatically_retries(after_write):
    class Interrupted(MemoryTransport):
        def create(self, ref, payload):
            if after_write:
                super().create(ref, payload)
            raise TimeoutError("synthetic network timeout")

    backend = Interrupted()
    with pytest.raises(AmbiguousWrite):
        ReceiptStore(backend).claim(sample())
    assert bool(backend.values) == after_write


def test_wrong_readback_and_default_live_transport_fail_closed():
    class Tampered(MemoryTransport):
        def create(self, ref, payload):
            super().create(ref, dict(payload, owner="tampered"))

    with pytest.raises(Denied):
        ReceiptStore(Tampered()).claim(sample())
    with pytest.raises(Denied, match="disabled"):
        ReceiptStore(GitHubTransport("a" * 40)).claim(sample())


def test_local_git_create_race_persistence_and_wrong_target(tmp_path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    clients = []
    for i in range(2):
        folder = tmp_path / f"client{i}"
        folder.mkdir()
        subprocess.run(["git", "init", str(folder)], check=True, capture_output=True)
        # Identical synthetic commit object available in both clients and the bare server.
        tree = (
            subprocess.run(
                ["git", "mktree"], input=b"", cwd=folder, capture_output=True, check=True
            )
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
                    "user.email=fixture@invalid",
                    "commit-tree",
                    tree,
                    "-m",
                    "synthetic",
                ],
                cwd=folder,
                capture_output=True,
                check=True,
            )
            .stdout.decode()
            .strip()
        )
        subprocess.run(
            ["git", "push", str(remote), f"{commit}:refs/heads/fixture{i}"],
            cwd=folder,
            check=True,
            capture_output=True,
        )

        def runner(args, data=None, folder=folder):
            # LOCAL ONLY: rewrite pinned remote and assert network destinations never survive.
            args = [str(remote) if a.startswith("https://github.com/") else a for a in args]
            assert not any(a.startswith(("http:", "https:", "ssh:")) for a in args)
            result = subprocess.run(args, input=data, cwd=folder, capture_output=True)
            if result.returncode:
                raise OSError("Synthetic local Git command failed")
            return result.stdout.decode()

        clients.append(GitHubTransport(commit, runner))

    def claim(client):
        try:
            return ReceiptStore(client).claim(sample())
        except Denied:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(claim, clients))
    assert sum(r is not None for r in results) == 1
    winner = clients[0] if results[0] else clients[1]
    # New adapter instance reads receipt persisted outside either client worktree.
    fresh = GitHubTransport(winner.commit, winner.runner)
    assert ReceiptStore(fresh).verify(sample())
    wrong = GitHubTransport("0" * 40, winner.runner)
    with pytest.raises(Denied, match="wrong execution code"):
        ReceiptStore(wrong).verify(sample())


def test_ref_namespace_injection_denied():
    adapter = GitHubTransport("a" * 40)
    with pytest.raises(Denied):
        adapter.read("--upload-pack=bad")


def test_synthetic_namespace_cannot_claim_a_real_cohort():
    from execution_safeguards.protocol import cohort_ref

    ns = "stage-b-synthetic/receipt-integration-v1"
    adapter = GitHubTransport("a" * 40, namespace=ns)
    adapter.check_ref(cohort_ref("1" * 64, "2" * 64, ns))
    for ref in [cohort_ref("c" * 64, "d" * 64, ns), cohort_ref("1" * 64, "2" * 64)]:
        with pytest.raises(Denied):
            adapter.check_ref(ref)
