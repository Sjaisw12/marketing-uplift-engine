# Disabled production adapter preparation — completion evidence

Base main: `dbcd64a2fc454e8483b3031a76fa4a4d65eaf7c6`.
Preparation lock:
`2922e67d6aa7d891f87c8f90abe79aa16b9545c1c2f64d345fd42ede533d37e4`.

## Delivered

- Additive owner-key configuration, verified decoded 32-byte key fingerprint.
- Metadata-only lock/authorization preparation and inert fixed-cohort transports.
- Narrow feature/outcome Parquet query kernels, strict source-row alignment,
  preserved nine-model loader, batched memory-mapped predictions and policy seals.
- Pre-outcome receipt/journal/seal/independently attested backup proof verifier.
- Streamed 64 MiB private checkpoint export parts and bounded safe restore CLI.
- Synthetic tests, development-only model reproduction, read-only CI workflow,
  operations guide, README, phase checklist and interview explanation.

Stage B is disabled. Public real-data executor and holdout methods raise before
access; no activation CLI or workflow is provided. This is preparation, not a
claim that the live coordinator is operational. A later reviewed activation must
connect verified proofs, durable outcome transition and real adapters. Existing
historical locks, source modules and model manifest are preserved rather than resealed.

## Actual verification

`OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 make check`:
**268 passed, 20 full-data tests deselected**, 15.61 seconds for pytest; lint and
formatting passed. Twenty new synthetic cases cover projection/schema violations,
record anomalies, authorization rejection, disabled APIs before I/O, portable lock
and key/ruleset tampering, receipt/journal/backup ordering, seal integrity/cohort/layout,
private export corruption and disk preflight.

`pytest tests/production/test_development_full.py tests/test_final_stage_a_full.py -q`:
**3 passed**, 14.60 seconds. A pytest reporting warning concerned `record_property`
with xunit2 output, not test assertions. These permitted tests verified:

- All nine existing models against original file hashes, features and tree counts.
- Exact predictions and nuisance averages on 2,048 original development probes.
  These are correctness probes, not new out-of-sample performance estimates.
- 276 protected historical files against Stage A evidence, original Stage A lock
  and model manifest, and the unchanged 765-comparison numerical reference.
- Local export/restore of a 268,408,192-byte invented file using <=64 MiB parts.
  This demonstrates bounded local processing, not off-workspace transfer.

The separate /tmp filesystem has less than the 8 GiB production reserve. Tiny
synthetic/development output fixtures explicitly waive that reserve in tests only;
production source guards remain unchanged. No model recipe or dataset was reduced.

Historical coordinator lock still verifies as
`4789505034ccaf4ef1ab3f81b880b4a0d8e36909d3ab6ea013e859c434772b28`.
Original Stage A lock remains
`fbd0ec32f8d97bbc1ffe03dd4a16a7937390d4ac570becef83b109cbc3d32b93`.
Original model-manifest payload digest remains
`2e91bdae68cad12604c6aff3a9337b62e40df383f1ce6b2d3d4c1c58e08b8c9e`.
Machine-readable evidence is in `verification.json`.

No real holdout record/outcome was read, scored, summarized or evaluated. No model
was fitted or changed. No production authorization, receipt, journal or live write
test was created. Only PR branch publication uses GitHub writes in this task.

## Operations and remaining blockers

Read-only API snapshots verify the configured coverage/protection of rulesets
25285405 and 25285424. Production write enforcement was not tested and must not be
inferred from these snapshots. The completed synthetic receipt test was not repeated.

The owner reports the earlier small synthetic archive restored on their Mac. A
full-size private channel remains unavailable/unverified. Before real scoring or
outcome access, the owner must approve an existing private transfer route and
independently restore full-size invented files through it. No new services,
credentials, public artifacts or large chat transfer are used here. Follow
`docs/PRODUCTION_ADAPTER.md` for export/restore, byte bounds, disk requirements and
owner attestation. Local storage is not assumed durable across tasks.

Review this PR/lock, then separately review an activation release/lock, exact
unsigned authorization/validity, backup procedure and one-time execution. Do not
sign this disabled preparation lock for execution. Private signing stays on the
Mac. Stage B remains unapproved and disabled; Phase 10 is out of scope.

All later statistics remain conditional on unverified assignment and identification
assumptions. The primary abstention identity does not prove ineffectiveness or
optimality; diagnostics cannot replace it after seeing holdout results. IPW/DR and
multiplier intervals do not remove released-sample selection, dependence or unknown
experiment propensities, and do not substantiate financial profitability.
