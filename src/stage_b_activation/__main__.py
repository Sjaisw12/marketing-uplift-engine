"""Review metadata only: no execution, signing, receipt, journal, scoring or upload CLI."""

import argparse
import json
from pathlib import Path

from .authorization import draft
from .lock import verify

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("command", choices=["verify-lock", "unsigned-draft"])
args = parser.parse_args()
plan = verify(Path.cwd())
if args.command == "verify-lock":
    print(plan["lock_sha"])
else:
    print(json.dumps({"signable": False, "signature": None, "payload": draft(plan)}, indent=2))
