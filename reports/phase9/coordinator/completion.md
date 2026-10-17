# Coordinator preparation completion — Stage B disabled

Implementation-lock payload SHA-256: `4789505034ccaf4ef1ab3f81b880b4a0d8e36909d3ab6ea013e859c434772b28` (75 bound files).
Original Stage A lock, model manifest and prior safeguards implementation lock are
preserved byte-for-byte. Documentation commit 93ab406 and independently verified
synthetic integration evidence are included in this branch. No repeat live test.

## Implementation

- One synthetic-only coordinator constructs expected authorization from independently
  reviewed fixture metadata and the frozen implementation lock, verifies source/model
  identities, claims/verifies one receipt, and enforces the ordered journal stages.
- Fixed-cohort, fixed-sequence annotated Git journal adapter uses create-only CAS,
  checks new-tag output (no-op is not a claim), and replays bound/signature-verified
  history. Competing, truncated, tampered, out-of-order and ambiguous writes stop.
- Feature projection is IDs + f0–f11 only. Nine fixture predictors exercise arm/S
  routing; final real diagnostic models are never changed or used for holdout scoring.
- Prediction, nuisance, rank, alignment and twenty membership arrays are saved and
  hashed. Exact sealed decisions and independently attested backup are required before
  outcome-access transition. Existing statistical kernel is reused without edits.
- Bounded private archive export and safe restore reject traversal, links, duplicate
  files, missing/corrupt files, wrong digests and excess size. No external storage service.
- Recovery requires exact original receipt, journal tip, checkpoints, backup and a
  separate signed owner instruction acknowledging previous-worker termination. Actual
  recovery signatures remain verifiable in durable events. Only known prediction
  boundaries resume; ambiguous action-start and completed stages cannot restart.

## Actual verification

`make check`: 248 passed, 18 expensive tests deselected in 17.30s; lint and formatting
passed (73 Python files). This includes 83 safeguards tests, 36 added here.
End-to-end fixtures and recovered execution call unchanged IPW/DR kernel with all
five propensity assumptions, 2,000 draws per uncertainty method and 765 comparisons.
These are synthetic correctness results, NOT final policy performance.

Permitted Stage A development-only full gate: 1 passed in 12.24s; nine model reloads,
276 protected historical entries, all frozen memberships, Stage A caches/probes and
MLflow verify unchanged. No real holdout records queried/scored/evaluated.
New metadata lock and unchanged Stage A public lock verify. CI push/PR checks are
synthetic-only; no manual whole-source workflow is dispatched.

## Boundaries and unresolved manual steps

Production public key remains null. Production construction and real access APIs
unconditionally deny before I/O; no activation command, real Parquet reader, real
model-loading route or default live runner is shipped. Future adapters and key
pinning require a LATER reviewed execution lock and separate Stage B approval.

No production receipt, new live receipt/journal tests, rule changes, paid resources,
credentials, model refits, split changes, previous-results changes or Phase 10 work.
Only branch/PR publication and safe CI are authorized GitHub writes for this task.

Journal durability/concurrency are tested against LOCAL Git and file backends.
Actual future journal ruleset coverage and production identity remain unverified;
prior synthetic tag enforcement evidence is preserved, not generalized silently.
Private transfer/restore is simulated with local synthetic copies: the owner must
verify a real off-workspace destination/restore and retain the latest journal digest.
Signed attestations cannot prove physical storage independence or worker termination.
GitHub protection is not administrator-proof WORM. Exactly one physical read under
arbitrary crashes is not promised; one locked campaign with fail-closed recovery is.

See docs/STAGE_B_COORDINATOR.md for backup/restore procedure and manual gates.
Existing statistical identification and conditional uncertainty limitations remain.
