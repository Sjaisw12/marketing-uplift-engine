# Completed live synthetic GitHub receipt integration

**Complete and independently verified by the owner. Do not repeat this test.**
This is historical evidence, not authorization to run these commands again or
activate Stage B. No production receipt, signing key, holdout access, or evaluation
was involved.

The one-time test used merged main
`67f70bb0de4e6cafbf398e706db741676b2b1cbe` and execution lock
`2792d14576f1b3a84acad042c2f22f28693e875e52cba795ddb98385fb3e758a`.

## Retained remote evidence

Exact synthetic ref (retained permanently for audit):

`refs/tags/stage-b-synthetic/receipt-integration-v1/1111111111111111111111111111111111111111111111111111111111111111/2222222222222222222222222222222222222222222222222222222222222222`

- Annotated tag object: `5262253c71ffd4033c5165c7864e590838b0d7f6`.
- Target commit: `67f70bb0de4e6cafbf398e706db741676b2b1cbe`.
- Receipt payload SHA-256: `9d8aecb4557d5f3c067de7ac5a3b69e8b7ba68a5df72ab35cf3c21a1bb9bee9d`.
- Annotated-tag content SHA-256: `6cb4b060c075247179cb4e851347a7596ae969ba9309804562d38eec06bf3276`.
- Ruleset: 25283799, Stage B Synthetic Receipt Protection. Before/after reads
  confirmed active, exact tag scope, updates/deletions restricted, creations
  unrestricted, no bypass actors, unchanged settings.

## Actual results

| Check | Observed result |
|---|---|
| Authenticated Git preflight | Dry-run exit 0; subsequent successful creation confirms write access |
| Two independent competing clients | Exactly one creation exit 0; other exit 1, reference already exists |
| Duplicate logical claim | ReceiptStore denied before push |
| Changed-owner/receipt logical claim | ReceiptStore denied before push |
| Changed-object create-only push | Exit 1, stale info; original unchanged |
| Forced update of exact synthetic ref | Exit 1, GH013: Cannot update this protected ref |
| Deletion of exact synthetic ref | Exit 1, GH013: Cannot delete this tag |
| Fresh independent client | Same object, payload bytes, and target commit |

The helper conservatively paused when the race loser received a server-side
reference-already-exists error rather than stale-info wording. Read-only
reconciliation verified the winner; no competing creation was retried. An
identical-object raw Git push can be an up-to-date no-op, so duplicate logical
claims were tested through ReceiptStore rather than represented as server writes.

## Sanitized command evidence

[Original JSON command log](../reports/phase9/safeguards/live_synthetic/integration_evidence.json)
records actual argv commands, exit statuses, sanitized errors, synthetic payloads,
and before/after verification results. It is copied byte-for-byte from the
sanitized integration report. SHA-256:
`da9ff95963a1612a7694d6f2cba8098b6f3c1e3c0ad9cbaf45f0d7a53df60971`.
Temporary client paths in the log are provenance only, not recovery requirements.
The authorization digest in the receipt denotes a synthetic fixture, not an
owner-signed production authorization. No credentials or private data are included.

The original 276 protected historical entries, nine model files, memberships,
policy lock and model manifest verified unchanged before/after. No previous
results, dependency lockfile, repository settings or other remote ref was modified.

## Boundary of this evidence

This demonstrates enforcement for the exact synthetic tag and tested identity at
that time. It does not establish production tag protection, private-backup
durability, coordinator correctness, administrator-proof WORM, or Stage B approval.
Owner public-key pinning, durable coordinator/journal integration, independent
private restore verification, and a new reviewed execution identity remain gates.
No further live synthetic receipt test is planned or authorized.
