# Stage B activation integration — review and approval required

This is preparation, not final execution. No real holdout feature/outcome is read,
scored or evaluated; no production receipt/journal/backup branch is written. The
production CLI only verifies metadata or prints an unsigned draft. Existing real
interfaces in historical packages remain disabled. The new factory fails closed
without a separate, valid owner signature over the exact reviewed identity.
The configuration's `execution_approved=false` records this preparation status;
it is not an activation toggle. Changing it invalidates the lock and is rejected.
No workflow input, environment variable, local approval boolean or PR merge grants
execution. This is an application protocol, not a sandbox against an administrator
who edits Python, GitHub settings or local files.

## Preserved policy and statistical scope

The additive lock verifies the prior production adapter lock and recursively all
historical Stage A/coordinator/safeguards locks. None is resealed. The original model
manifest, nine fitted models, memberships, source/Parquet identity, seeds, dependency
lockfile, economics and previous results are unchanged. Models are checked by raw
SHA-256, feature order and 200-tree recipe. Only f0–f11 are user predictors; S receives
its intervention separately. Existing ranking/tie/ceil reach rules and statistical
kernels are imported without changes. The primary policy is always no targeting,
zero assignments/spending and zero gain relative to itself by identity. This does
not prove advertising ineffective or abstention optimal. Secondary diagnostics
cannot replace it after seeing holdout performance.

IPW, shared-nuisance DR and final-S nuisance sensitivity use the same five assumed
propensities, 2,000 paired Gaussian draws, 765 contrasts, separate pointwise and
simultaneous intervals and stratified sensitivity. These remain nominal working
models conditional on fixed fitted policies. Unknown experiment propensities,
privacy selection, dependence and causal identification remain limitations.
Hypothetical economics are not observed revenue or verified profitability.

## Trusted authorization and preflight

`activation/config.json` pins the distinct age recipient and the verified official
age Linux binary fingerprint. The owner Ed25519 public key is inherited from the
unchanged parent configuration. Neither private key nor passphrase enters Codex.

The unsigned draft leaves `not_before`, `expires_at`, `reviewed_commit` and
`preflight_sha256` null. It is non-signable as an execution grant. After PR review,
choose the exact reviewed checkout commit, a UTC interval no longer than 24 hours,
and fresh preflight observations. Review that completed payload before any signing.
No code/config/lock change is needed just to fill those approved runtime fields.
Any code/config/dependency/model change requires another lock and review.

Expected immutable bindings are rebuilt from the reviewed files, not copied from
an incoming envelope. The checkout's actual Git commit must equal the signed commit.
Canonical JSON is UTF-8, sorted keys, compact comma/colon separators, no NaN.
Activation signature bytes are:

`b"marketing-uplift/stage-b-activation-integration/v1\x00" + canonical(payload)`.

The domain differs from historical preparation protocols intentionally; an old
signature cannot activate the new integration. Only the owner signs locally after
separate explicit execution approval. The Mac's age identity decrypts backups; it
is never used to sign execution, and the Ed25519 key is never used for encryption.

Preflight report schema is defined in `preflight.validate`. It binds this lock,
reviewed commit, observation/expiry times, private repository identity and both
rulesets' API observations. Validity is at most one hour. Require active exact
receipt/journal coverage, update/deletion restrictions, creation allowed and no
bypass actors. The activation signature authenticates the report's digest. The
backup signature authenticates another fresh report before outcome access.

**Trust limitation:** Git alone cannot prove repository privacy or ruleset settings.
The existing connected GitHub API was used read-only during preparation; standalone
`gh` API access previously returned 403. Therefore the operator must obtain fresh
API observations through the authenticated connection (or on the Mac), and the
owner must inspect them before signing. The executor verifies the owner's binding
and freshness, not an independent API-origin signature. Do not substitute arbitrary
unsigned JSON or claim autonomous online API enforcement. Git read access and exact
remote refs/commit are checked independently at runtime. Settings may still change
after observation; this is not administrator-proof WORM or continuous monitoring.
The owner can reject this trust model at PR review; then execution stays blocked.

## Ordered execution and private persistence

The integrated kernel connects `FrozenSource`, nine models, strict receipt transport,
existing `Journal`, prediction sealing, encrypted export and unchanged evaluation.
The production factory has no caller-supplied clock, source, key or arbitrary runner.
Only synthetic tests inject fixture components into the internal kernel.

1. Verify exact code lock, actual reviewed commit, signed authorization and fresh
   preflight. Verify dataset/model bytes and frozen membership before scoring.
   No Parquet outcome columns are queried for these identity checks.
2. Check private Git access, no existing fixed backup branch and no existing journal.
   Claim the SAME fixed-cohort receipt as before. Require explicit Git **new tag**
   confirmation plus readback; an identical racing claim returning **up to date**
   is rejected. Never create a per-run receipt or replace an existing claim.
3. Append/read back `receipt_verified`, then `feature_scoring_started`. The feature
   source separately checks this durable stage before projecting `row_id,f0–f11`.
   Source IDs/types/alignment/nonfinite failures stop without dropping/coercing rows.
4. Save memory-mapped prediction, nuisance, ranking and membership arrays. Verify
   all hashes and recomputed ranks/masks, append/read back `features_scored`.
   Keep original signed approval/report and journal tip on the owner's Mac too.
5. Export the exact checkpoint using the unchanged format. Verify official age
   binary bytes, encrypt the COMPLETE tar with the pinned recipient, then split
   ciphertext into <=32 MiB parts. Re-read parts and compare byte-for-byte to the
   ciphertext. Record source seal/catalog/archive/ciphertext/part hashes. Partial
   outputs stop; no overwrite, silent retry, fresh encryption or automatic cleanup.
6. Publish ONLY encrypted parts, `transfer.json` and `catalog.json` to the fixed
   private `stage-b-checkpoint-v1` branch. The branch must be absent; creation uses
   an empty lease and requires new-branch confirmation/readback. Main and historical
   synthetic branches are untouched. No LFS, public artifacts or plaintext upload.
   A changed/ambiguous response latches execution shut for read-only reconciliation.
7. STOP for the owner to download the exact private commit on the Mac, check part
   and combined SHA-256, decrypt locally, verify tar/catalog/manifest, and run the
   existing `execution_safeguards restore-bundle` with the exact manifest digest and
   explicit archive byte bound. Verify every restored file's size and SHA-256.
   The successful synthetic test never substitutes for THIS production backup.
8. Owner signs `backup.backup_payload`: same receipt/lock/execution, exact prediction
   manifest, transfer/catalog/archive/ciphertext hashes and sizes, encryption
   recipient, private repository/branch/commit, fresh preflight digest and explicit
   successful independent Mac restore. Domain is
   `b"marketing-uplift/encrypted-mac-backup/v1\x00"`. It is a trusted owner attestation,
   not a cryptographic proof of physical storage or restore activity.
9. Verify local predictions/export parts, owner signature, freshness, Git access and
   exact private commit. Append/read back `predictions_sealed` with the exact proof
   digest. Reverify everything immediately before outcome access.
10. Append `outcome_access_started`, read back the COMPLETE journal at the expected
    tip, verify receipt/ownership/checkpoint again, THEN construct the narrow
    `row_id,treatment,visit` reader. This transition consumes the one-time outcome
    access even if the process crashes next. No other outcomes/features are read.
    The source's own capability guard repeats the durable-stage check and permits
    its outcome interface only once. Verify exact sealed predictions/masks before
    the unchanged evaluation kernel consumes labels. Save results, interval/draw
    evidence and manifest exclusively; append/read back `completed`. Never reselect.

No commands above have been executed on real holdout data in preparation. Future
operators use the reviewed Python API `production(...)` and explicit methods;
there is intentionally no automatic execute/recover/upload workflow or shell launcher.
Retain the original signed authorization, preflight, receipt identity, every journal
tip, checkpoint manifest, transfer metadata, private commit and signatures off-workspace.

## Resources, failures and recovery

Arrays use 128 bytes per cohort record plus format overhead (about 268 MB total).
Queries use the unchanged bounded DuckDB settings and batching; prediction arrays
are memory-mapped. Ranking still requires O(n) scratch and sorting. Encryption and
hashing stream; chunks are at most 32 MiB. Export requires an 8 GiB reserve plus
8x checkpoint bytes for tar/parts/ciphertext/Git staging. Actual full holdout runtime
and peak RAM are not measured here. Stop on insufficient capacity or failed checks;
never change recipes, reduce data, rerun training or alter fixed seeds.

Recovery requires the same exact code/commit/models/data, original receipt and
signed grant/report, complete durable journal at the reviewed expected tip, exact
local checkpoint/export, verified private commit, owner backup proof and a NEW
owner-signed recovery approval naming a NEW worker and asserting the old worker
was terminated. It never claims again. Existing journal recovery domain/schema is
preserved. Recovery is supported only at `features_scored` or `predictions_sealed`
with completed independently verified backup evidence. A feature-scoring interruption,
partial export or unpublished backup can require manual review rather than automatic
recovery. Post-outcome-start and completed states allow audit only, no second read.

The public factory still requires a current original authorization/preflight at
construction. Backup proof and its report must also remain current; a sealed proof
cannot be silently replaced by a newly favorable or extended one. Outside these
windows, stop for review rather than stretching an approval. There is no automatic
cross-task key transfer or restoration: age's private key stays on the Mac. If Cloud
loses local files, recovery remains blocked until exact artifacts are restored by
an approved private process. The Mac copy protects bytes, not automatic Cloud resume.
Git history, credentials and rule settings remain owner-administered and mutable.

## Required approval before execution

- [ ] Review/approve this PR and portable lock; no merge performed by Codex.
- [ ] Confirm the owner-attested API preflight trust/limitations above.
- [ ] Choose the exact reviewed commit and UTC window <=24h; collect fresh API report.
- [ ] Review the completed unsigned payload, exact lock/model identities and backup procedure.
- [ ] Separately explicitly approve ONE Stage B execution; owner signs locally.
- [ ] Verify runtime Git permissions/protections and artifact/disk identities.
- [ ] Score features once, transfer the actual encrypted checkpoint, restore on Mac.
- [ ] Owner supplies exact signed production backup attestation; verify durable seal.
- [ ] Only then consume outcome access once; stop for review after results.

PR approval/merge, the full-size synthetic restore and a boolean are NOT execution
approval. No production authorization/receipt/journal/backup exists yet. Phase 10
and any later policy selection or dashboard remain out of scope.
