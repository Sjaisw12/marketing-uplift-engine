# Stage B safeguard preparation — no execution approval

This extension implements owner-authorized safeguards for an offline portfolio
project. Stage A completion was approved and merged at
e5ae9774513c12f168288524255457631286452c. Implementation preparation is authorized;
live GitHub write testing, repository settings changes, production authorization,
holdout feature access, outcomes and final evaluation are NOT authorized.

## Preserved evidence and additive execution identity

The original policy lock, nine-model manifest, models, recipes, economic scenarios,
evaluation formulas, 2,000 Gaussian draws and 765-comparison family remain unchanged.
Primary recommendation remains no targeting, zero spending, and zero incremental
gain relative to itself by identity, not evidence of no advertising effect or
optimality. Secondary diagnostics cannot replace that primary after seeing results.

New code is isolated in src/execution_safeguards. Original locked package modules,
configurations and protocols are untouched. The new execution lock includes their
historical file hashes, the Stage A lock, model manifest and all nine model hashes,
source/holdout identities, new code, tests, settings, this document and the new
synthetic-only workflow. Canonical JSON is UTF-8, sorted keys, compact separators,
no NaN/Infinity; file hashes cover raw bytes. No absolute workspace paths enter
the new payload. The lock excludes itself and completion/review prose. The reviewed
Git commit containing the lock must also be pinned at eventual integration.

Verify without opening private data or model files:

    uv run --locked python -m execution_safeguards verify-lock
    uv run --locked uplift final-prepare --verify-public-lock

No automatic lock replacement command exists. Any implementation edit requires a
new generated lock and review. Existing Stage A evidence is never resealed/refitted.

## Owner authorization

Use Ed25519 through cryptography, already present in uv.lock (no dependency changes).
Only verification ships in production code. Test keys are generated inside temporary
synthetic fixtures. Never send a private signing key to Codex, GitHub, or logs.

The owner signs canonical payload bytes prefixed with the exact domain bytes
`marketing-uplift/stage-b-authorization/v1` followed by a single NUL byte.
The envelope contains exactly payload and a base64 64-byte signature. The trusted
public key is base64 raw 32-byte Ed25519, pinned in separately reviewed settings;
it is never accepted from the envelope. Current production key is null.

Authorization payload fields are schema=1, purpose=one-final-holdout-evaluation,
execution_lock_sha256, model_manifest_sha256, dataset_sha256, holdout_sha256,
parameters_sha256, owner, execution_id, public_key_sha256, not_before, expires_at.
Times require offsets and validity is start-inclusive/end-exclusive. The executor
constructs expected bindings from reviewed artifacts, not untrusted submitted data.
Duplicate JSON fields/nonfinite numbers are rejected. Signatures bind execution
identity and expiration; they do not establish that the operator is independent.
Revocation/compromised-key handling requires stopping for review; no automatic key
rotation or alternate-key fallback. A signature does not itself enable Stage B.

## Fixed receipt and Git command adapter

One cohort key, invariant to model, run, owner and execution lock:

    refs/tags/stage-b-receipts/<archive-sha256>/<holdout-membership-sha256>

The literal production key is recorded in execution_lock.json. Never create it in
preparation or integration tests. Receipt metadata binds authorization, execution
lock, model manifest, source/membership, parameters, owner and execution_id. No
records, predictions, private keys or credentials enter Git. An annotated tag
targets the exact reviewed code commit. Its canonical receipt message is read back
and checked, including cohort and commit identity.

GitHubTransport prepares argv-only Git commands: mktag, and push with an EMPTY
force-with-lease expectation requiring the ref to be absent. This is a create-only
compare-and-swap, not permission to update an existing tag. The default transport
has no runner and denies all operations. No live runner/CLI is provided. Tests inject
mock/local-only runners. The adapter does NOT verify GitHub rulesets by itself.
No live production readiness or authorization may be inferred from adapter tests.

Duplicate claims fail even when the submitted receipt is identical. Different owners
or locks cannot claim the same cohort again. A timeout or failed write has an unknown
result: stop; never automatically retry or allocate a different ref. Recovery reads
the exact existing receipt and requires separate review. Hashes alone do not make
mutable refs immutable. GitHub repository owners can change rulesets/delete the
repository; this is explicitly weaker than independent administrator-proof WORM.

## Ordered stages and private checkpoint seal

The synthetic state machine orders authorization_verified → receipt_created →
features_scored → predictions_sealed → outcome_access_started → completed.
Every event binds a receipt, sequence, previous-event digest and required evidence.
The state functions validate evidence structure/hash continuity; they do not by
themselves prove a supplied digest represents a real authorization or durable write.
A future reviewed coordinator must call the verifiers and persist each transition
before proceeding. No real coordinator or holdout reader ships in this release.

The future feature interface must project only row_id/f0–f11 and preserve frozen
alignment/tie/reach conventions. Outcome access must consume the same sealed
predictions/memberships, never recalculate ranking. Current real scoring and outcome
interfaces unconditionally deny before I/O, including boolean/env claims of approval.

Checkpoint manifests include relative paths, byte sizes, SHA-256 and execution/receipt
binding. Files are private and ignored; no row-level content is interpreted by these
utilities. Rehash local and independent-backup copies before any future outcome
access. The owner additionally signs an attestation binding manifest and execution
using domain `marketing-uplift/private-backup/v1` followed by NUL, with purpose
independent-private-backup. Different local directories do not prove independence:
the owner must verify that the backup is outside this disposable Cloud environment.
Tests use local copies and prove hashing/signatures ONLY, not off-cloud durability.

After any crash, preserve the original claim. Verify the exact receipt, lock,
untruncated journal digest against its externally saved seal, and private checkpoints.
Never infer exclusivity from a local lock/expired timer. Recovery requires separate
owner approval and confirmation the previous worker is terminated. The recovery
helper verifies integrity only; resume_authorized is always false. Missing evidence,
ambiguous ownership or lost backups stops execution. Do not start an independent
evaluation. Arithmetic replay from immutable saved evidence must be labeled replay.

## Exact manual setup and live-test proposal — STOP pending approval

No settings have been changed and no GitHub write tests have been run.

1. Owner: retain an Ed25519 private signing key locally. Provide ONLY its public key
   after deciding to configure signing. Pin it in a newly reviewed execution lock.
2. GitHub Settings → Rules → Rulesets → New tag ruleset. Enforcement: Active.
   Bypass list: empty. Select the exact receipt tag name (omit refs/tags/).
   Enable Restrict updates and Restrict deletions. Leave Restrict creations OFF.
   Configure the disposable tag first; production protection needs separate review.
3. Proposed disposable namespace: refs/tags/stage-b-synthetic/receipt-integration-v1.
   Use fake archive identity 64 ones and fake holdout identity 64 twos. The proposed
   full tag is that namespace followed by /<64 ones>/<64 twos>. It contains no real
   cohort identifiers. The adapter's separate synthetic namespace mode permits only
   this exact fake cohort; the default mode remains production and rejects it.
   A separately approved runner must target only this exact disposable tag.
4. After separate write-test approval, test initial creation, two competing clients,
   duplicate creation, changed target/message, update and deletion attempts under
   the intended execution identity. Exactly one creation must succeed; update/delete
   must be rejected by GitHub. Keep the synthetic receipt as audit evidence; do not
   bypass protections to clean it up. Verify persistence from a fresh client.
5. Verify supported credential-injected Git write transport without exposing tokens.
   Current read connectivity is not proof of write access. No new long-lived secrets.
6. Choose and verify a private backup on an existing owner-controlled independent
   device/service; record a restore/hash check. Do not upload private checkpoints
   to this public repository or public Actions artifacts. No paid service required.
7. Review live-test evidence, production ruleset, owner public key, backup procedure,
   coordinator/access implementation and the NEW execution lock before separately
   approving any final evaluation. This preparation release is not executable Stage B.

Owner signing replaces the previously proposed required-reviewer environment gate
by explicit user-approved scope. No independent reviewer is claimed. GitHub protected
environments remain an optional later alternative; self-review prevention requires
another eligible participant. That alternative is not silently enabled here.

## Verification and limitations

Synthetic tests cover RFC8032 Ed25519 reference, forged/wrong-key/domain signatures,
identity mismatches, validity windows, duplicate/competing claims, ambiguity after
write, wrong tag targets, tampering, checkpoint paths/hashes, stage order, crashes,
restricted recovery, and denial of real access before I/O. A real LOCAL bare Git
race verifies server-side absent-ref claims and remote persistence; it does not
demonstrate GitHub rulesets. CI has read-only permissions and no data downloads,
live credentials, dispatch activation or real holdout commands.

Statistical identification/uncertainty limitations are unchanged: assumed propensity
scenarios, release subsampling, unknown experiments/dependence, and nominal intervals
conditional on fixed policies/models. Safeguards do not establish causal validity.
The current preparation remains fail-closed until blockers are separately resolved.
