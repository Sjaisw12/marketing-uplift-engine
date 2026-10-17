"""Fresh owner-reviewed API observations plus independent, read-only Git probes."""

import re
from datetime import UTC, datetime

from execution_safeguards.protocol import Denied, digest


def window(start, end, now, limit):
    try:
        a, b = datetime.fromisoformat(start), datetime.fromisoformat(end)
        if (
            a.utcoffset() is None
            or b.utcoffset() is None
            or now.utcoffset() is None
            or not a <= now < b
            or not 0 < (b - a).total_seconds() <= limit
        ):
            raise Denied("Expired/not-yet-valid/oversized authorization window")
    except (TypeError, ValueError) as exc:
        raise Denied("Exact timezone-aware validity window required") from exc


def validate(report, plan, commit, now=None):
    """API provenance is owner-attested, not inferred from an unauthenticated JSON file."""
    now = now or datetime.now(UTC)
    if (
        set(report)
        != {
            "schema",
            "execution_lock_sha256",
            "reviewed_commit",
            "observed_at",
            "expires_at",
            "private_repository",
            "rulesets",
        }
        or report["schema"] != 1
    ):
        raise Denied("Preflight report schema")
    if report["execution_lock_sha256"] != plan["lock_sha"] or report["reviewed_commit"] != commit:
        raise Denied("Preflight for different reviewed execution")
    window(
        report["observed_at"],
        report["expires_at"],
        now,
        plan["config"]["preflight_maximum_seconds"],
    )
    repo = report["private_repository"]
    if (
        repo.get("full_name") != plan["config"]["backup_repository"]
        or repo.get("private") is not True
    ):
        raise Denied("Backup repository not confirmed private")
    for rid, pattern in [
        (plan["parent"]["config"]["receipt_ruleset_id"], plan["parent"]["receipt_ref"]),
        (plan["parent"]["config"]["journal_ruleset_id"], plan["parent"]["journal_prefix"] + "*"),
    ]:
        found = [r for r in report["rulesets"] if r.get("id") == rid]
        if len(found) != 1:
            raise Denied("Missing/duplicate production protection")
        r = found[0]
        if (
            r.get("enforcement") != "active"
            or r.get("target") != "tag"
            or r.get("bypass_actors") != []
            or r.get("conditions", {}).get("ref_name") != {"include": [pattern], "exclude": []}
            or {v["type"] for v in r.get("rules", [])} != {"update", "deletion"}
        ):
            raise Denied("Changed GitHub ruleset protection/coverage")
    return digest(report)


def ref_sha(output, ref, absent=False):
    if not output.strip() and absent:
        return None
    fields = output.split()
    if len(fields) != 2 or fields[1] != ref or not re.fullmatch(r"[0-9a-f]{40}", fields[0]):
        raise Denied("Missing or ambiguous remote ref; no retry")
    return fields[0]
