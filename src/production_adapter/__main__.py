"""Metadata verification and private restore only; no production execution command."""

import argparse
from pathlib import Path

from .export import restore_chunks
from .plan import verify

parser = argparse.ArgumentParser(description=__doc__)
sub = parser.add_subparsers(dest="command", required=True)
sub.add_parser("verify-lock")
restore = sub.add_parser("restore-chunks")
restore.add_argument("--directory", required=True)
restore.add_argument("--destination", required=True)
restore.add_argument("--catalog-sha256", required=True)
restore.add_argument("--max-bytes", type=int, required=True)
args = parser.parse_args()
sha = verify(Path.cwd())
if args.command == "verify-lock":
    print(sha)
else:
    restore_chunks(args.directory, args.destination, args.catalog_sha256, args.max_bytes)
    print("Chunk bytes restored/verified; no execution or independent-backup approval granted")
