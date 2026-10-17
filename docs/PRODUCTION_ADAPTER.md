# Production execution adapter — prepared, disabled

This preparation release does not authorize or execute Stage B. Every public real
holdout entry point (`PreparedExecutor.start/score/seal/evaluate/recover` and
`ParquetAdapter.holdout_features/holdout_outcomes`) raises before data access.
There is no final-evaluation CLI or workflow dispatch. Internal array/query kernels
are preparation components, not a security sandbox against someone editing Python.
The operator must continue to respect the separate approval gate.

## Reviewed identities and preservation

The owner supplied this Ed25519 public key, independently checked on their Mac:

- Base64: `rJcbMwtTLCZZs3VdcZ08xjQX3fOx+torHv5UcAcpGuY=`
- SHA-256 of the 32 decoded bytes:
  `9c885530f96b2a4cc50afa8a2baaa1f1300a97720552e590dff824bdcc593800`.

Only public material is in `production/config.json`. Never send the private key
or passphrase to Codex, GitHub, CI, or logs. No production authorization is signed
or requested here. Expected authorization bindings are constructed from the
reviewed lock, source/cohort identity, model manifest, policy/settings digest,
owner, execution identity and explicit validity window, rather than an envelope's
claimed values. The historical configuration with an unset key remains historical.

`reports/phase9/production/execution_lock.json` binds this additive package,
configuration, workflow, tests and document, and the previous coordinator lock.
Verification recursively verifies the original Stage A policy, model manifest and
historical source. None is resealed or replaced. Nine existing model files are
checked against original SHA-256 values, feature order and 200-tree recipes before
loading. No retraining, winner selection, model substitution or new policy occurs.

The primary policy remains no targeting, zero assignments/spending and zero gain
relative to itself by identity. This does not establish that advertising has no
effect or abstention is optimal. Diagnostics remain random, response, S and T at
10/20/30/40/50%, plus none/all. All eight hypothetical economic scenarios, five
assumed propensities, 2,000 multiplier draws and 765-comparison family remain as
originally locked. The existing evaluation kernel is imported without edits.

## Prepared data and sealing boundaries

The Parquet query kernel selects either `row_id, f0, ..., f11` or
`row_id, treatment, visit`, never `SELECT *`. Feature processing does not request
outcomes. Source-row IDs must be sorted unique uint64 values, feature types must
be float64 and outcome types uint8. Missing, duplicate, null, nonfinite, nonbinary,
misaligned or incorrectly typed records cause failure; no deletion or coercion.
The permitted development adapter checks membership before opening Parquet and
verifies the Parquet byte hash. Real holdout methods are unconditionally disabled.

Prediction processing uses batches and memory-mapped arrays. The S intervention
indicator is supplied separately; all user predictors are exactly f0–f11. Six
nuisance predictions are combined by the historical formula. Frozen random seed,
ranking, tie-breaking and ceil reach rules are reused. The seal covers IDs,
scores, orders, bins, policy masks and nuisance predictions, file hashes, shapes
and execution bindings. Reading a seal recomputes ranking and memberships before
acceptance. The synthetic outcome kernel verifies the seal before consuming even
one outcome batch and invokes the historical IPW/DR and uncertainty implementation.

`verify_boundary` additionally requires the original verified receipt, owned and
complete durable journal ending at `predictions_sealed`, matching execution
bindings, the exact checkpoint digest, and an independently restored backup with
owner-signed attestation whose digest equals the journal evidence. It performs no
outcome access. A later approved activation must connect this proof to the existing
coordinator's durable `outcome_access_started` transition **before** opening the
outcome source. This release deliberately does not provide that live connection.
Recovery must use the existing separately signed approval and same journal/receipt;
there is no new campaign or automatic takeover.

## GitHub integration status

`production/rulesets.json` preserves read-only API observations of active tag
rulesets 25285405 (fixed receipt) and 25285424 (journal prefix). Both restrict
updates/deletions, permit initial creation and have no bypass actors. The lock
checks exact namespace coverage. The prepared transports use those exact existing
namespaces and have no subprocess runner attached; calling them cannot write.
No production ref is created or queried as an execution claim in this preparation.
The previously retained live synthetic receipt test is complete and was not repeated.

These snapshots verify configuration, not live production enforcement. GitHub
administrator changes, credential permissions, network ambiguity and concurrent
writers remain operational risks. Tag protection is not administrator-proof WORM.
A future read-only preflight must recheck rulesets and exact ref state; ambiguous
write results must stop for read-only reconciliation, never automatic retry.

## Private checkpoint export and independent restore

Codex local disk is not durable across tasks. The owner reports the small synthetic
archive restored successfully on their Mac. Direct private Cloud download is
unavailable; this is **not** evidence that full-size transfer works.

`production_adapter.export.export_chunks` verifies an existing checkpoint manifest,
streams an uncompressed tar and emits at most 64 MiB per numbered part plus
`catalog.json`. It records each part's bytes/SHA-256, whole archive bytes/SHA-256,
manifest and canonical catalog digest. No network transport, public upload,
credentials or compression of private data is implemented. At the frozen cohort
size, the six array payloads require 128 bytes per record (268,408,192 bytes), plus
NumPy/tar/manifest overhead. Memory is bounded by one 64 MiB export chunk; the
query is bounded by the existing DuckDB limits. Ranking still needs O(n) arrays
and O(n log n) sorting. Preflight checks reserve 8 GiB beyond estimated staging;
this is a guard, not a measured full-cohort runtime or RAM guarantee.

During export the checkpoint, temporary tar and output parts coexist: allow about
three times checkpoint size plus the reserve. Restore also needs room for parts,
assembled tar and restored files. Keep the original checkpoint until independent
restore and owner attestation succeed. Interrupted export directories are incomplete
and must not be accepted without the final valid catalog.

Future operational procedure, **not authorized for real predictions now**:

1. After the feature-only stage and exact seal, export into a new private directory.
   Record the canonical catalog digest and byte bound in the durable checkpoint
   evidence before transfer. Transfer all parts and catalog using an owner-approved
   existing private channel (for example, existing private SFTP or short-lived
   authenticated private object storage); do not use public GitHub, Actions
   artifacts, email/prompt credentials, or bulk Base64 in chat.
2. First verify that channel using full-size invented synthetic files and an
   independent Mac restore. No channel has been configured or tested here. If none
   exists, stop: real outcome access remains blocked. No paid service or new
   infrastructure is required by this code, but channel availability is unresolved.
3. On the Mac, check out the exact reviewed commit, install the pinned environment
   with `uv sync --locked`, and run from the repository directory:

   ```sh
   uv run --locked python -m production_adapter verify-lock
   uv run --locked python -m production_adapter restore-chunks \
     --directory "$HOME/PrivateBackup/parts" \
     --destination "$HOME/PrivateBackup/restored-new" \
     --catalog-sha256 REVIEWED_CANONICAL_CATALOG_DIGEST \
     --max-bytes REVIEWED_ARCHIVE_BYTE_BOUND
   ```

   Replace the two uppercase placeholders with the separately reviewed digest and
   bound; destination must not exist. The command verifies every part, whole tar,
   safe extraction and all restored file hashes. The catalog digest uses canonical
   JSON, **not** `shasum catalog.json`. The archive digest itself is ordinary
   SHA-256. Neither successful restore nor the printed lock grants execution.
4. Return only the lock/catalog/manifest/archive digests, byte counts and restore
   status. Preserve all private files locally. A later reviewed signing procedure
   must bind the independent-backup attestation to that exact manifest/execution;
   the private signing key stays on the Mac. Restore again into an independent
   executor directory for byte verification and match the signed backup to the
   durable journal. A second local directory alone does not prove off-workspace
   durability: owner attestation and the actual independently verified transfer
   are required. Hashes establish integrity, not confidentiality or availability.

## Required review before activation

Review this preparation PR and its new lock first. Then approve a separately
reviewed activation release/lock, exact unsigned authorization payload and validity
window, final transfer/restore procedure, backup attestation and one-time execution.
The disabled flags cannot be flipped under this lock: verification rejects them.
Only after that separate release and approval may the owner sign locally and an
executor claim the fixed receipt. Do not sign this preparation lock for execution.
No authorization, production receipt, journal event or holdout access is performed
here. No Phase 10 work is included.

IPW/DR results, if later authorized, remain assumption-dependent on unverified
propensities, identification, released-sample selection and dependence assumptions.
Multiplier intervals are nominal conditional working-model intervals. Simultaneous
and pointwise intervals remain distinct; none establishes actual ROI or revenue.
