# Durable Stage B publication pause and continuation

Preparation and synthetic testing only. No real execution is authorized. This child
protocol preserves the historical activation lock, all nine fitted models, frozen
memberships, dependency lockfile, policies and statistical formulas unchanged.
Existing production signatures do not authorize it: both code identity and start
signature domain change. A new reviewed child lock and separately signed start
approval are required. The metadata CLI cannot execute the coordinator.

## Durable boundary

The operator uses the unchanged scoring, export, encryption and evaluation kernels.
The fixed cohort receipt and fixed Git journal namespace remain the same. No per-run
receipt or replacement campaign is introduced. Local OS file locking excludes two
workers using the same state directory; Git's atomic create-only sequence slots
exclude conflicting journal writers. The owner must independently ensure an old
worker on another machine is terminated. This is not a distributed worker lease.

After verified private backup publication, a new `backup_published` event binds the
prediction manifest, transfer manifest and private Git commit. `pause.json` is
exclusively written and fsynced in the private directory, binding those identities,
the original signed approval/report, receipt, complete journal tip and old worker.
The operator then closes and cannot score, seal or evaluate again. Its process may
exit. No live Python object is needed while the owner restores the backup.

The new process verifies the original signature, code/data/model/policy identities
and original preflight as historical evidence at the original grant's start time.
It does NOT treat that expired grant as current permission. It requires a NEW owner
continuation signature with a fresh preflight (at most one hour), a new validity
window (at most 24 hours), new worker ID, exact pause digest and expected journal
tip, and an explicit old-worker-terminated assertion. The owner-signed independent
backup restore proof is also required before continuation is admitted. No unsigned
or implicit takeover is supported. The original receipt is verified, never claimed.

The resumed operator verifies every checkpoint, rank and membership, remote backup
commit, original approval and complete journal. It appends/readbacks a single
`continuation_approved` event with the signed grant, preflight and pause metadata.
This does not access outcomes. `seal(...)` durably records the exact backup proof.
Only a subsequent explicit `evaluate()` can append/readback `outcome_access_started`
and call the unchanged outcome interface. The primary recommendation remains zero
targeting. No model or reach reselection is allowed.

## Signature definitions

Canonical JSON and the pinned owner Ed25519 public key are unchanged. New starts sign:

`b"marketing-uplift/resumable-stage-b-start/v1\x00" + canonical(payload)`

The start payload is `authorization.draft(child_plan)` with the reviewed child
commit, fresh preflight digest and explicit validity window completed. Historical
activation grants, including the previously uploaded production signature, cannot
be reused against this code. The child plan binds the unchanged parent settings
and an additional continuation rule through the parameter digest.

Continuations sign:

`b"marketing-uplift/resumable-stage-b-continue/v1\x00" + canonical(payload)`

Construct exact fields using `approval.continuation_payload(...)`. The payload binds
the child lock/commit, model manifest, dataset/holdout, owner/campaign, original
authorization digest, whole pause digest, journal tip, fresh report digest, new
instance, old-worker-terminated assertion, allowed seal/evaluate actions and window.
Do not sign a continuation until independently restoring the actual private backup.
Only the separate backup attestation uses the unchanged encrypted-backup domain.
The owner keeps every private signing/encryption key on the Mac.

## Exact future operator procedure

These are reviewed API steps, NOT authorization or commands to execute now.

1. Check out the approved child commit; run
   `python -m stage_b_continuation verify-lock`. Recheck private Git access, absent
   fixed receipt/journal/backup branch, exact protected artifacts and resources.
2. Obtain a fresh preflight for the CHILD lock and commit. Obtain separate owner
   approval and signature over the new start payload. Preserve both original files
   unchanged. Choose an existing private parent directory on a volume with capacity.
3. In process A, call
   `c = production(root, private, "worker-a", signed_start, start_preflight)`;
   `c.start(signed_start, start_preflight)`; `c.score_features()`;
   `transfer = c.export(pinned_age_binary)`; `pause = c.publish(transfer)`.
   STOP. `publish` closes the operator. Exit process A, and confirm it is terminated.
   Do not call `seal`, `evaluate` or legacy `recover` in process A.
4. Retain the ENTIRE private directory, including `original-approval.json`,
   `pause.json`, prediction arrays/seal, plaintext local export, encrypted export,
   transfer/catalog metadata and local Git publication workspace. Keep the latest
   journal tip, pause digest and original signed grant/report off-workspace too.
   Do not assume Cloud storage survives a new task. This protocol resumes across
   process death only when exact files are available. Losing them requires an
   independently approved private restoration procedure; never regenerate them.
5. On the Mac, fetch the EXACT private backup commit, verify part/ciphertext/archive
   and catalog hashes, decrypt with the distinct age identity and run the existing
   `execution_safeguards restore-bundle` with the exact prediction-manifest digest
   and explicit byte bound. Verify every restored file. The synthetic test is not
   evidence that this production backup has been restored.
6. Obtain a NEW fresh preflight for the SAME child lock and reviewed commit. Construct
   the unchanged `backup.backup_payload(...)`, review and sign locally only after
   successful restore. Construct the continuation payload using the exact pause,
   new instance `worker-b`, fresh preflight and new window. Ensure its not_before is
   within that preflight's validity window. Obtain separate explicit approval and
   sign locally; give Codex only public metadata and signed envelopes.
7. In genuinely new process B, load original signed start, `pause.json`, fresh
   preflight, signed continuation and signed restore proof, then call:

       c = production(root, private, "worker-b", signed_start, fresh_preflight,
                      continuation=signed_continuation, signed_backup=signed_restore)

   The factory validates the original grant historically, validates current fresh
   continuation permission and reconstructs the verified state without rescoring,
   re-encrypting, re-uploading or claiming any receipt.
8. ONLY with separately explicit holdout-outcome approval call
   `c.seal(pause["transfer"], signed_restore, fresh_preflight)`, then `c.evaluate()`
   once. Close the worker. Stop for results review; no subsequent phase or merge.

All real factory construction still requires authentic signatures. No production
grant was generated here. Preflight API privacy/ruleset observations remain
owner-attested and signature-bound, not independent API signatures. Git readbacks
remain independent. GitHub rulesets are not administrator-proof immutable storage.

## Fail-closed interruptions and limits

Only the exact `backup_published` pause can resume. A missing/corrupt pause,
checkpoint, original approval or journal, changed private commit, expired fresh
permission, unverified restore or competing worker stops before outcomes. A new
continuation never changes seeds, recipes, predictions, policies or original receipt.
The canonical pause is tamper-evident through signed owner approval plus durable
journal/hash verification; it is not a secret credential or a serialized Python object.

Ambiguous receipt, publication or journal writes stop without retry. If a
continuation event was remotely created but its acknowledgement was lost, the old
pause tip no longer matches; automated resumption is disabled pending read-only
reconciliation. Interruptions during scoring, between publication and pause fsync,
after continuation admission, or after sealing require review. This narrow fix
does not claim arbitrary crash recovery at every instruction.

After `outcome_access_started`, even a crash before the first outcome batch consumes
outcome access. No automatic replay, fresh campaign, updated snapshot or second
receipt is allowed. A completed evaluation is audit-only. Continued preflight and
backup proof freshness is required before outcome access; expiration cannot be
silently renewed. All statistical limitations of the parent protocol still apply.

Synthetic tests kill process A with SIGKILL after publication, independently restore
invented checkpoints, and start process B after the original grant AND preflight
have expired. They use synthetic Ed25519 keys, local file-backed fake Git receipts
and journals, simulated encryption and 80 invented records. They demonstrate process
restart and no rescoring, NOT production Git enforcement, real transfer, or arbitrary
Cloud persistence. No further live GitHub integration test is performed here.
