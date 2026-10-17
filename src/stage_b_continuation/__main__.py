"""Metadata-only entry point; never claims, resumes, scores, uploads or evaluates."""

import argparse
import json
from pathlib import Path

from stage_b_activation.authorization import draft

from .approval import START_DOMAIN
from .lock import verify

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("command", choices=["verify-lock", "unsigned-draft"])
args = p.parse_args()
plan = verify(Path.cwd())
if args.command == "verify-lock":
    print(plan["lock_sha"])
else:
    print(
        json.dumps(
            {
                "signable": False,
                "signature": None,
                "signature_domain_utf8": START_DOMAIN.decode(),
                "payload": draft(plan),
            },
            indent=2,
        )
    )
