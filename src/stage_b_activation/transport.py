"""Scoped Git access. No credentials, automatic retries, live dispatch or settings edits."""

import re
import subprocess
from pathlib import Path

from execution_safeguards.protocol import Denied
from execution_safeguards.receipt import AmbiguousWrite, GitHubTransport

MAIN = "https://github.com/Sjaisw12/marketing-uplift-engine.git"
PRIVATE = "https://github.com/Sjaisw12/uplift-private-checkpoint-transfer.git"


class StrictReceiptTransport(GitHubTransport):
    """Identical racing claims must NOT both succeed on an up-to-date response."""

    def command(self, args, data=None):
        result = super().command(args, data)
        if args and args[0] == "push" and "\t[new tag]" not in result:
            raise AmbiguousWrite("Receipt not confirmed NEW; reconcile read-only, never retry")
        return result


class JournalRunner:
    def __init__(self, repository, receipt_ref, journal_prefix):
        self.root = Path(repository)
        self.receipt_ref, self.journal_prefix = receipt_ref, journal_prefix

    def __call__(self, argv, data=None):
        if not argv or argv[0] != "git":
            raise Denied("Git argv only")
        a = argv[1:]
        permitted = False
        if a and a[0] == "ls-remote":
            permitted = (
                len(a) == 4
                and a[1] == "--refs"
                and a[2] == MAIN
                and (
                    a[3] == self.receipt_ref
                    or a[3] == self.journal_prefix + "*"
                    or re.fullmatch(re.escape(self.journal_prefix) + r"\d{6}", a[3])
                )
            )
        if a and a[0] == "fetch":
            permitted = (
                len(a) == 4
                and a[:3] == ["fetch", "--no-tags", MAIN]
                and (
                    a[3] == self.receipt_ref
                    or re.fullmatch(re.escape(self.journal_prefix) + r"\d{6}", a[3])
                )
            )
        if a and a[0] == "cat-file":
            permitted = len(a) == 3 and a[1] == "tag" and bool(re.fullmatch(r"[0-9a-f]{40}", a[2]))
        if a == ["mktag"]:
            permitted = isinstance(data, bytes) and len(data) < 1048576
        if a and a[0] == "push" and len(a) == 5 and a[1] == "--porcelain" and a[3] == MAIN:
            oid, sep, ref = a[4].partition(":")
            permitted = (
                bool(sep and re.fullmatch(r"[0-9a-f]{40}", oid))
                and (
                    ref == self.receipt_ref
                    or bool(re.fullmatch(re.escape(self.journal_prefix) + r"\d{6}", ref))
                )
                and a[2] == f"--force-with-lease={ref}:"
            )
        if not permitted:
            raise Denied("Git command/ref outside frozen receipt/journal allowlist")
        try:
            r = subprocess.run(
                ["git", "-c", "core.hooksPath=/dev/null", *a],
                cwd=self.root,
                input=data,
                capture_output=True,
                timeout=120,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AmbiguousWrite(
                "Git operation response unknown; read-only reconciliation required"
            ) from exc
        if r.returncode:
            # Never print authentication diagnostics that may contain server-supplied URLs.
            raise Denied(f"Git {a[0]} failed (exit {r.returncode}); no retry; details suppressed")
        return r.stdout.decode("utf-8")


class PrivateRemote:
    def __init__(self, repository, branch):
        self.root, self.branch = Path(repository), branch
        if branch != "stage-b-checkpoint-v1":
            raise Denied("Only fixed production checkpoint branch permitted")

    def command(self, args, timeout=120):
        try:
            r = subprocess.run(
                ["git", "-c", "core.hooksPath=/dev/null", *args],
                cwd=self.root,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AmbiguousWrite("Private Git response ambiguous; never retry upload") from exc
        if r.returncode:
            raise Denied(f"Private Git command failed (exit {r.returncode}); no retry")
        return r.stdout.decode()

    def access(self):
        from .preflight import ref_sha

        return ref_sha(self.command(["ls-remote", PRIVATE, "refs/heads/main"]), "refs/heads/main")

    def commit(self):
        from .preflight import ref_sha

        return ref_sha(
            self.command(["ls-remote", PRIVATE, "refs/heads/" + self.branch]),
            "refs/heads/" + self.branch,
            absent=True,
        )

    def publish(self, directory, transfer):
        """Single create-only push; fixed allowlist, no plaintext or implicit git add."""
        import shutil

        from execution_safeguards.checkpoints import checked_path
        from execution_safeguards.protocol import digest, file_hash, strict_json

        directory = Path(directory)
        if self.commit() is not None:
            raise Denied("Existing fixed checkpoint branch; verify/recover, never publish again")
        metadata = strict_json((directory / "transfer.json").read_bytes())
        if metadata != transfer:
            raise Denied("Transfer manifest changed before publication")
        names = ["transfer.json", "catalog.json", *[p["path"] for p in transfer["parts"]]]
        for part in transfer["parts"]:
            path = checked_path(directory, part["path"])
            if (
                not re.fullmatch(r"encrypted/part-\d{6}\.bin", part["path"])
                or path.stat().st_size != part["bytes"]
                or file_hash(path) != part["sha256"]
                or not 0 < part["bytes"] <= 33554432
            ):
                raise Denied("Unsealed encrypted publish files")
        if (
            digest(strict_json((directory / "catalog.json").read_bytes()))
            != transfer["catalog_sha256"]
        ):
            raise Denied("Export catalog changed")
        checkout = directory / "git-workspace"
        if checkout.exists():
            raise Denied("Interrupted publish workspace; read-only reconciliation required")
        self.command(
            [
                "clone",
                "--depth",
                "1",
                "--single-branch",
                "--branch",
                "main",
                PRIVATE,
                str(checkout),
            ],
            timeout=120,
        )
        entries = {p.name for p in checkout.iterdir()}
        if entries != {".git", "README.md"}:
            raise Denied("Private repository baseline changed; review before publishing")

        def git(args, timeout=120):
            try:
                r = subprocess.run(
                    ["git", "-c", "core.hooksPath=/dev/null", *args],
                    cwd=checkout,
                    capture_output=True,
                    timeout=timeout,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise AmbiguousWrite("Unknown private Git publication; no retry") from exc
            if r.returncode:
                raise Denied("Private Git publication failed; stop without retry")
            return r.stdout.decode()

        git(["switch", "--create", self.branch])
        for name in names:
            src = checked_path(directory, name)
            target = checkout / name
            target.parent.mkdir(exist_ok=True, parents=True)
            with target.open("xb") as out, src.open("rb") as inp:
                shutil.copyfileobj(inp, out, 1048576)
        git(["-c", "core.compression=0", "add", "--", *names])
        if sorted(git(["diff", "--cached", "--name-only"]).splitlines()) != sorted(names):
            raise Denied("Unexpected staged files")
        # Non-secret author identity is fixed; never use a signing key for this commit.
        git(
            [
                "-c",
                "user.name=Checkpoint executor",
                "-c",
                "user.email=checkpoint@invalid",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-m",
                "Seal encrypted private checkpoint",
            ]
        )
        commit = git(["rev-parse", "HEAD"]).strip()
        result = git(
            [
                "-c",
                "pack.compression=0",
                "-c",
                "pack.threads=2",
                "push",
                "--porcelain",
                f"--force-with-lease=refs/heads/{self.branch}:",
                "origin",
                f"HEAD:refs/heads/{self.branch}",
            ],
            timeout=300,
        )
        if "\t[new branch]" not in result or self.commit() != commit:
            raise AmbiguousWrite("Private checkpoint push/readback ambiguous; never repeat")
        return commit
