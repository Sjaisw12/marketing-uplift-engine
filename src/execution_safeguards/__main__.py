"""Public metadata verification only. No execution, signing, keygen or live-write command."""

import argparse
from pathlib import Path

from .bundle import restore_bundle
from .lock import verify

parser = argparse.ArgumentParser(description=__doc__)
commands = parser.add_subparsers(dest="command", required=True)
commands.add_parser("verify-lock")
restore = commands.add_parser("restore-bundle", help="Verify/restore private bytes; no evaluation")
restore.add_argument("--archive", required=True)
restore.add_argument("--destination", required=True)
restore.add_argument("--manifest-sha256", required=True)
restore.add_argument("--max-bytes", required=True, type=int)
args = parser.parse_args()
lock_sha = verify(Path.cwd())
if args.command == "verify-lock":
    print(lock_sha)
else:
    restore_bundle(args.archive, args.destination, args.manifest_sha256, args.max_bytes)
    print("Restored bytes and manifest verified; no execution or backup independence established")
