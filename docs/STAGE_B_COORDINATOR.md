# Stage B coordinator implementation — synthetic only

Production public key is unset, Stage B is disabled, and real holdout interfaces
unconditionally deny access. The completed live synthetic receipt test is historical
evidence and must never be repeated. No live journal writes are authorized here.

This implementation connects authorization, receipt, fixed-sequence journal,
checkpoint/backup verification, and signed recovery using tiny declared synthetic
artifacts. The original Stage A models, policies, economics, statistical kernels,
2,000 draws and 765-family remain unchanged. Real model loading/data access and
owner public-key pinning require a later reviewed execution lock.

## Reviewed bindings and execution path

`Coordinator` accepts ONLY a tiny independently hashed `reviewed-fixture.json`
marked synthetic_only (2–4,096 rows), separate feature/outcome JSON files and nine
explicitly synthetic fixture predictors. It verifies the repository implementation
lock and fixture source/model byte hashes before each action. Expected signature
bindings are built from that trusted fixture manifest and frozen settings, never
copied from the submitted authorization. Fixtures use generated test keys; no
production key or credential is generated, requested or installed.

Production construction and the pre-existing real access entry points always deny
before I/O. No production Parquet reader, real LightGBM loading/coordinator route,
activation flag, or live command runner is shipped. Future activation must review
those data/model adapters and pin the owner public key under a NEW lock; this
release is a complete synthetic coordinator, not an executable final analysis.

The synthetic path is:

1. Verify lock, nine fixture model identities, dataset identity, exact authorization
   signature and validity; atomically claim the single fixed-cohort receipt.
2. Verify/read back the receipt; durably append receipt_verified with authorization
   and receipt hashes. No existing claim is treated as permission for a fresh start.
3. Append feature_scoring_started before reading features. Accept only source IDs
   plus exactly f0–f11. IDs are alignment metadata, never user predictors. S uses
   the existing separate intervention design. No label/exposure projection is allowed.
4. Use unchanged prediction/ranking helpers, PCG64 seed, descending score/priority
   and ascending ID tie rules; preserve ceil-rounded reaches. Persist ordered IDs,
   scores, rank orders, bins, all twenty policy memberships and shared nuisance
   predictions with a receipt/lock binding. Explicit none/all anchors and economics
   remain those of the frozen Stage A protocol; no new price/reach selection.
5. Hash/fsync checkpoint bytes and manifest; append features_scored. Export and
   independently restore the private bundle. Verify local and restored byte hashes
   plus owner backup signature; append predictions_sealed with both evidence hashes.
6. Recheck exact durable manifest, local/restored bytes, identity, sealed ranking and
   membership alignment BEFORE appending outcome_access_started. Only then may the
   synthetic outcome interface read aligned treatment/visit. It calls the unchanged
   final_metrics IPW/shared-DR/final-S-DR kernel: five assumed propensities, 2,000
   draws, IID and stratified sensitivities and 765 simultaneous diagnostic contrasts.
   The kernel reconstructs ranks from the same sealed scores and asserts identical
   memberships; it cannot choose a different policy from outcomes.
7. Save/fsync synthetic result arrays and a result manifest; append completed.
   Repeated evaluation is denied. Result backup can use the same bundle utilities;
   missing results after an interrupted outcome action do NOT authorize recomputation.

Statistical limitations remain unchanged: scenarios are assumptions rather than
verified propensities; DR does not remove release selection or unknown experiment
assignment issues; intervals are conditional working-model intervals. No real
holdout statistics, revenue, causal superiority or profitability is established.

## Durable journal and race handling

Git journal key:

    refs/tags/stage-b-journal/<dataset-sha256>/<holdout-sha256>/<six-digit-sequence>

Each tag is an annotated metadata object targeting the reviewed code commit. It
binds receipt SHA, implementation lock, owner, execution ID, instance ID, fixed
sequence, prior-event hash, stage and required evidence. Every recovery event
retains its actual signed recovery envelope, so fresh readers can verify it.
No private row data, source features, predictions, checkpoints or keys enter Git.

There is no mutable journal-head branch. List/verify the contiguous sequence and
compare against the caller's last durable tip digest. Append uses an absent-ref
compare-and-swap at the one next sequence key. Duplicate/out-of-order attempts fail;
two clients cannot reserve alternate keys for the same sequence. Remote readback is
mandatory. A push reporting an up-to-date no-op is NOT proof of a new claim: the
adapter requires a confirmed new tag. Unknown write results stop for read-only
reconciliation, with no automatic retry or acceptance of ownership.

The default Git journal adapter is inert without an explicitly supplied runner.
Tests use local files and a LOCAL bare Git server only. Live journal namespace
protection has NOT been tested/configured. The prior synthetic receipt integration
is complete; it is preserved in docs/STAGE_B_SYNTHETIC_INTEGRATION.md and is never
repeated. GitHub tags are not administrator-proof WORM. Loss/tampering by repository
administrators may defeat protections; retain the latest journal tip off-workspace.

## Private export, transfer and restore

The coordinator returns a prediction manifest, bound to its receipt and lock.
`export_bundle(private_root, manifest, archive_path)` creates a new, uncompressed
private tar bundle after verifying every file. It never overwrites an archive.
Transfer the archive AND expected manifest digest through an existing secure
owner-controlled method to your computer/private storage. The implementation
provides no external hosting, login or credentials. Verify the transfer path using
a synthetic archive first; the automated local-copy simulation is not a verified
Cloud-to-owner download capability or proof of storage independence.

On your computer, check out the exact reviewed implementation commit, install the
locked environment and run from the repository root:

    uv run --locked python -m execution_safeguards restore-bundle \
      --archive /private/path/checkpoint.tar \
      --destination /private/path/new-restored-directory \
      --manifest-sha256 <independently-recorded-manifest-digest> \
      --max-bytes <reviewed-upper-bound-for-restored-bytes>

The destination must be absent. Restore rejects links, traversal, duplicate names,
undeclared/missing files, wrong hashes and excessive sizes/member counts. It streams
file bytes and bounds disk use; partial failures never merge into existing files.
Keep bundles on private/encrypted owner storage, never Git or public CI artifacts.

Independently hash the restored copy. Retain original authorization, manifest,
archive digest, journal tip, exact commit and lock identity off-workspace. Sign the
backup attestation LOCALLY over the existing BACKUP_DOMAIN/canonical payload;
retain the private signing key outside Codex/GitHub. Its payload binds purpose,
manifest digest and receipt/lock. Supply only public key, envelope and signatures
when later authorized. An owner attestation authenticates the assertion; software
cannot infer physical independence merely from a second directory or signature.
If a restored copy must be returned to Cloud for byte verification, use the same
existing secure transfer method. If transfer/restore cannot be demonstrated, stop.
No new cloud service is required or assumed.

## Restricted recovery

After interruption, NEVER clear/recreate the original receipt or start a new
campaign. A fresh coordinator verifies original signed authorization (still within
its validity window), exact receipt, journal against an independently retained tip,
models/source/code, prediction manifest and restored-backup attestation.

Recovery is permitted ONLY at features_scored or predictions_sealed boundaries.
The owner must confirm the previous worker has terminated, then sign a separate,
short-lived RECOVERY_DOMAIN envelope binding the exact journal digest, receipt,
lock, execution, replacement instance and explicit termination acknowledgement.
The coordinator constructs these bindings independently; only the signed validity
window is owner-selected. The approval is appended create-only before takeover.
Old instances cannot continue using an advanced journal tip. There is no timer,
lease expiry, new random seed, changed model or automatic ownership transfer.

An interrupted feature_scoring_started or outcome_access_started phase is ambiguous
and cannot be repeated by this release, even with a generic recovery request.
Stop for review. Completed runs cannot restart. Any proposed arithmetic replay
needs separately reviewed immutable evidence, not a fresh evaluation.

## Manual gates after this PR

- Review implementation and new lock; production signing public key remains null.
- Later provide ONLY an owner public key and independently confirm its fingerprint.
  Pinning it and providing real data/model adapters require a new reviewed lock.
- Manually configure Active tag rulesets for the exact production receipt and journal
  cohort pattern, with no bypass actors, update/deletion restrictions ON, creation
  restrictions OFF. Do not change the completed synthetic tag/ruleset. This PR does
  not perform any settings changes or live receipt/journal writes.
- Demonstrate synthetic bundle transfer/restore to actual owner-controlled storage;
  retain a private backup and external journal tip. No production credentials requested.
- Verify future ruleset/identity configuration separately; local tests do not prove
  live journal enforcement. Any new live setup/write testing requires approval.
- Obtain separate approval of the exact later execution lock and model manifest
  before any production receipt, feature scoring or holdout outcome access.

Synthetic tests cover authorization failures, changed identities/seeds, create races,
no-op detection, journal truncation/tampering, signatures on recovery history, missing
or corrupt checkpoints, archive transfer/restore, missing backup attestation, ordered
sealing, interrupted actions, stale writers, recovery and unconditional real-access
denial. CI runs these without datasets, model weights, credentials or write rights.
