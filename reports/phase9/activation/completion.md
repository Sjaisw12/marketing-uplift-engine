# Stage B activation integration preparation

Prepared for review only. No production authorization exists and Stage B was not
executed. The metadata CLI cannot run evaluation or upload checkpoints.

## Reviewed identity

- Base main: `4dd2c71988a4f6e6296fe9fa5afb48fd2d771758`.
- New execution lock:
  `bd08dd6f38c672adcd3367c3134c0d3f7ad424dada60dabb47c3f2c0a216d103`.
- Unchanged Stage A model-manifest digest:
  `2e91bdae68cad12604c6aff3a9337b62e40df383f1ce6b2d3d4c1c58e08b8c9e`.
- Historical locks and dependency lockfile are preserved. The additive lock
  recursively verifies its historical parents.

## Implemented boundaries

The signed coordinator binds reviewed code, data, models and policy identities to
one fixed-cohort receipt and ordered durable journal. Feature and outcome sources
are separate guarded interfaces. Prediction and membership sealing precedes
encrypted checkpoint export. The checkpoint must be transferred to the private
repository, independently restored on the owner's Mac and covered by a separately
signed backup attestation before outcome access. The `outcome_access_started`
event must be durably verified before opening outcomes.

The strict transport requires an explicit new-tag acknowledgement: an identical
competing claim receiving Git's up-to-date response cannot become a second owner.
Ambiguous writes stop execution. Recovery keeps the original receipt and requires
an intact journal, checkpoint evidence and separately signed approval. Outcome
replay and automatic post-outcome recovery remain forbidden.

Existing estimators, five assumed propensity scenarios, 2,000 multiplier draws,
765-comparison family, nine models and primary abstention policy are unchanged.
Synthetic evaluation tests exercise these formulas; no real holdout was queried.

## Actual verification

`OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 make check` passed:

- 343 tests, including 75 new activation tests; 20 full-data tests deselected.
- Ruff lint passed; formatting passed for 93 files.
- All nine model files and twelve frozen membership files match historical raw
  byte hashes, without interpreting any holdout records.
- Portable lock verification passed. The unsigned draft has null signature,
  reviewed commit, preflight digest and UTC validity window, and is non-signable.

Coverage includes missing/forged/expired grants, identity tampering, concurrent
claims, interrupted and ambiguous writes, checkpoint corruption, missing backup,
unauthorized recovery and premature outcome access. Encryption/Git tests use
synthetic fixtures and mock transports. Actual full-size synthetic transfer and
Mac restore evidence is preserved separately as owner-reported historical evidence;
it is not a production checkpoint attestation.

## Remaining owner actions and limitations

Review this PR and exact lock. After approval, select the final reviewed commit
and a UTC window of at most 24 hours; obtain a fresh ruleset/private-repository
preflight snapshot and sign the exact authorization locally. No private key is
needed in Codex. During any separately approved execution, independently restore
the actual encrypted prediction checkpoint on the Mac and sign its exact backup
bindings before outcome access. See `docs/STAGE_B_ACTIVATION.md` for the procedure.

The API snapshot is owner-attested and signature-bound, rather than independently
authenticated by the standalone executor. Git ref checks are independent. Mac
restore is an owner assertion bound to hashes, not hardware attestation. GitHub
rulesets are not administrator-proof WORM storage. Expired authorization/preflight
windows, lost private state and post-outcome interruptions require review; this
implementation does not silently renew grants or replay analysis. There has been
no production receipt, journal, transfer, holdout scoring or final evaluation.
