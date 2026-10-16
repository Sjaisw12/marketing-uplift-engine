"""Phase-gated command surface. Unimplemented stages fail without side effects."""

import argparse
import json
import sys
import tomllib
from pathlib import Path

from marketing_uplift.acquisition import AcquisitionError, acquire
from marketing_uplift.data_audit import audit
from marketing_uplift.data_contract import ContractError, validate
from marketing_uplift.ingestion import ingest
from marketing_uplift.splits import split

STAGES = {
    "acquire": (2, "Download the pinned archive and verify SHA-256"),
    "validate": (3, "Validate the raw data contract; --full includes expensive checks"),
    "ingest": (3, "Convert the verified archive to audited typed Parquet"),
    "split": (3, "Seal holdout once and freeze development memberships"),
    "audit": (4, "Audit development data only"),
    "ate": (5, "Estimate development assignment effect and confidence interval"),
    "baselines": (6, "Train and log development baselines in local MLflow"),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/project.toml"))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="Show declared protocol and implementation status")
    for name, (_, help_text) in STAGES.items():
        command = commands.add_parser(name, help=help_text)
        if name == "split":
            modes = command.add_mutually_exclusive_group()
            modes.add_argument("--holdout-only", action="store_true")
            modes.add_argument("--verify", action="store_true")
            modes.add_argument("--reconstruct", action="store_true")
        if name == "validate":
            command.add_argument("--full", action="store_true")
    args = parser.parse_args(argv)
    if args.command in STAGES and args.command not in {
        "acquire",
        "validate",
        "ingest",
        "split",
        "audit",
    }:
        phase, _ = STAGES[args.command]
        parser.exit(2, f"{args.command}: not implemented; reserved for approved Phase {phase}.\n")
    try:
        with args.config.open("rb") as stream:
            config = tomllib.load(stream)
        if args.command == "acquire":
            print(json.dumps(acquire(config), indent=2))
            return 0
        if args.command == "validate":
            print(json.dumps(validate(config, full=args.full), indent=2))
            return 0
        if args.command == "ingest":
            print(json.dumps(ingest(config), indent=2))
            return 0
        if args.command == "split":
            result = split(
                config,
                holdout_only=args.holdout_only,
                verify_only=args.verify,
                reconstruct_missing=args.reconstruct,
            )
            print(json.dumps(result, indent=2))
            return 0
        if args.command == "audit":
            result = audit(config, progress=lambda message: print(message, file=sys.stderr))
            print(
                json.dumps(
                    {
                        "status": result["status"],
                        "development_rows": result["development_rows"],
                        "reports": ["reports/data_audit.json", "reports/data_audit.md"],
                    },
                    indent=2,
                )
            )
            return 0
        summary = {
            "implementation": "Phase 4 commands available; status does not verify local artifacts",
            "dataset": config["data"]["filename"],
            "revision": config["data"]["revision"],
            "outcome": config["experiment"]["outcome"],
            "holdout_fraction": config["experiment"]["holdout_fraction"],
            "development_seeds": config["experiment"]["development_seeds"],
            "tracking_uri": Path(config["tracking"]["directory"]).resolve().as_uri(),
            "reserved_stages": [stage for stage in STAGES if stage in {"ate", "baselines"}],
        }
    except (AcquisitionError, ContractError) as error:
        parser.exit(1, f"Pipeline stopped: {error}\n")
    except (OSError, tomllib.TOMLDecodeError, KeyError, TypeError) as error:
        parser.exit(2, f"Configuration or filesystem error: {error}\n")
    print(json.dumps(summary, indent=2))
    return 0
