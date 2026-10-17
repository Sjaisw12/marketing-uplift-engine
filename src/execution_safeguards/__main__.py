"""Public metadata verification only. No execution, signing, keygen or live-write command."""

import argparse
from pathlib import Path

from .lock import verify

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("command", choices=["verify-lock"])
parser.parse_args()
print(verify(Path.cwd()))
