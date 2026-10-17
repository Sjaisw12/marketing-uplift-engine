# Stage B durable-continuation preparation

Prepared for review only. No production receipt/journal was created, no production
checkpoint uploaded, and no real holdout feature or outcome was accessed.

The earlier activation signature is not reused. This is an additive child of
activation lock `bd08dd6f38c672adcd3367c3134c0d3f7ad424dada60dabb47c3f2c0a216d103`.
Historical activation code, locks, model manifest, fitted models, memberships,
dependency lockfile, policy definitions and statistical kernels remain unchanged.

New child execution lock:

`b7dca1de6089f2f621c4972d078c906f126205d837e8485064633a326f9e212c`

## Implemented behavior

The original operator publishes the verified encrypted checkpoint, appends and
reads back `backup_published`, writes/fsyncs the exact private pause record, and
closes. Its process can terminate. A new operator reconstructs the campaign from
the original signed approval, exact checkpoint files, fixed receipt, durable
journal, private backup commit, independently restored backup proof and a new
signed continuation grant. It never claims again, rescores, retrains or republishes.

Original authorization and original preflight are verified historically. Current
permission requires a fresh signed continuation and fresh preflight; the original
grant is never silently extended. New start/continuation domains and the child
lock invalidate the previously uploaded signature for this implementation.

The new journal enforces the publication boundary and one continuation admission.
Local OS locks exclude competing workers sharing the private directory; create-only
Git sequence slots and expected-tip verification fence remote journal transitions.
Prediction and backup sealing precedes the unchanged durable outcome-access gate.
Any post-outcome-start attempt to resume or replay is rejected.

## Actual verification

`OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 make check`:

- **378 passed, 20 full-data tests deselected**, in 108.54 seconds.
- Includes **35 new tests**, with real subprocess startup, SIGKILL and a different
  process resuming after BOTH the original authorization and preflight expired.
- One synthetic receipt, one feature-scoring call and one outcome call; 765
  diagnostic comparisons through the unchanged synthetic evaluation kernel.
- Competing processes admit exactly one evaluation. Missing/corrupt checkpoints,
  missing restore proof, forged/expired approvals, tampered policies/models/dataset,
  journal gaps/truncation, changed backup commit, ambiguous journal acknowledgement,
  failed state persistence and premature outcome access all fail closed.
- Crashes before the first outcome batch and at the outcome reader boundary cannot
  trigger another evaluation.
- Ruff lint and formatting passed (101 Python files).
- Recursive locks verify. Raw-byte checks matched all 258 historical files,
  18 historical MLflow directory trees, nine final models and twelve memberships.

The subprocess fixtures use 80 invented records, synthetic Ed25519 keys,
file-backed simulated Git and explicitly simulated encryption. Independent local
restore of synthetic bundle files is verified. These tests do not claim new live
GitHub enforcement or production backup-transfer verification.

## Required review and limitations

See `docs/STAGE_B_CONTINUATION.md` for the exact two-process procedure. Review this
PR and child lock before creating any new authorization. The supplied draft has
null signature, reviewed commit, preflight digest and validity window. Real start
requires new explicit approval and owner-local signature. Actual Mac backup restore,
fresh preflight, a separately signed continuation and backup attestation are
required before continuation. Outcome access still requires separate approval.

Only the durable publication pause is resumable automatically. A crash before
pause fsync, an ambiguous write, lost private files, or interruption after continuation
admission/sealing requires review. After outcome access starts, replay is forbidden.
Cloud file persistence is not guaranteed: preserve the entire private directory and
retain exact metadata off-workspace. Lost files need an approved private restoration
procedure. Local locks are not distributed leases; owner termination confirmation
is required across machines. GitHub administration and owner-attested preflight/
Mac restore retain the previously documented trust limitations. No Phase 10 work.
