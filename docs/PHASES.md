# Phase checklists

The attached final roadmap is authoritative. Each phase requires approval before
implementation and a completion report before approval of the next phase.
No calendar or effort schedule applies.

## Phase 1 — scaffold
- [x] Rename operating rules to AGENTS.md.
- [x] Establish package, directories, protocol configuration, and command interface.
- [x] Pin dependencies and provide a lockfile and setup/check commands.
- [x] Protect raw/processed data, predictions, models, and local MLflow files from Git.
- [x] Document provenance, data rights, and benchmark citation.
- [x] Verify installation, fast checks, imports, and command behavior.
- [x] User approves completion.

## Phase 2 — acquisition
- [x] Download official archive at pinned revision.
- [x] Verify exact basename, byte count and SHA-256 before ingestion.
- [x] Persist provenance manifest without inventing unverified row counts.
- [x] Report evidence; receive approval.

## Phase 3 — contract, ingestion, partitions
- [x] Validate exact schema/rows, types, binary values, rates and nonfinite counts.
- [x] Audit coercions; no silent row drops or deduplication.
- [x] Produce typed Parquet; enforce leakage tests on every feature export.
- [x] Seal 15% holdout before exploratory analysis; record membership hashes.
- [x] Freeze five joint-stratified 80/20 dev re-splits and save seeds in artifacts/splits.json.
- [x] Verify disjointness, coverage and reproducibility; activate real full-data CI.
- [x] Report evidence; receive approval.

## Phase 4 — development audit
- [x] Audit distributions, missingness, arm balance, repeated vectors and strata.
- [x] Publish reports/data_audit.md with deviations and limitations.
- [x] Report evidence; receive approval.

## Phase 5 — development ATE
- [x] Report arm sizes, event counts, visit rates and difference with 95% CI.
- [x] Express effects per 1,000 rows; state ITT and released-sample limitations.
- [x] Report evidence; receive approval.

## Phase 6 — baselines
- [x] Freeze random, visit-propensity and S-learner definitions and hyperparameters.
- [x] Evaluate all five development re-splits at 10/20/30/40/50% reach.
- [x] Include none/all anchors, metric conventions, IPW assumptions and event counts.
- [x] Log provenance, models, predictions and metrics in local mlruns/.
- [x] Publish development stability comparison; keep holdout sealed.
- [x] Report evidence; receive approval.

Every completion updates INTERVIEW.md with an explanation and two tough questions.
T-learner, DR evaluation, final policy selection, dashboard and headline holdout
analysis require later scope and approval.


## Phase 7 — advanced uplift modeling and robust evaluation
- [x] User approves separately scoped implementation plan and safeguards.
- [x] Freeze T-learner, three-fold training-only nuisance and multiplier protocol.
- [x] Verify preserved Phase 6 estimates, artifacts and frozen memberships.
- [x] Pass synthetic statistical, covariance, leakage and integration gates.
- [x] Complete and verify the first real split before the remaining four.
- [x] Report IPW/DR, propensity/nuisance sensitivity, support, calibration and vector overlap.
- [x] Verify all five evaluations, protected artifacts, reproducibility and CI.
- [x] Publish completion evidence and receive user approval.

No final model/reach selection, abstention engine, dashboard or holdout evaluation
is included in Phase 7. Later phases require separate scope and approval.

## Phase 8 — abstention-aware, budget-constrained development simulator
- [x] User approves separately scoped protocol and safeguards.
- [x] Freeze hypothetical economics, roles, decision and 300-coordinate uncertainty protocol.
- [x] Pass synthetic statistical, budget, abstention and leakage gates.
- [x] Verify first real split before continuing unchanged through the remaining four.
- [x] Publish five-split selection/assessment, sensitivity and matched-spending results.
- [x] Verify preserved artifacts, reproducibility and MLflow; extend GitHub Actions checks.
- [x] Publish completion evidence and receive user approval.

Phase 8 does not select/lock a final deployment policy, retrain models, evaluate the
sealed holdout, build Streamlit or authorize Phase 9.

## Phase 9 — final policy lock and separately gated holdout evaluation
### Stage A — authorized preparation only
- [x] User approves Stage A scope; Stage B remains unapproved.
- [x] Freeze primary abstention, diagnostics, nine refit recipes and evaluation protocol.
- [x] Pass synthetic estimators, 765-family, stratified covariance and leakage/gate tests.
- [x] Fit and verify nine development-only models; preserve prior artifacts.
- [x] Publish exact policy/code/model/data/dependency lock and Stage A review evidence.
- [x] User reviews Stage A completion and lock.

### Stage B — NOT authorized and disabled
- [ ] Integrate and verify protected reviewer approval and durable create-once receipt service.
- [ ] User separately approves exact final code lock AND model-manifest digests.
- [ ] Record durable execution receipt before any holdout outcome access.
- [ ] Execute the one-time locked analysis without policy re-selection.
- [ ] Review final results before merge or Phase 10.

Stage A approval/merge cannot authorize Stage B. No local boolean or approval file
can enable holdout scoring or outcome evaluation. No Phase 10/dashboard work.


### Stage B safeguard preparation — separately approved, execution still disabled
- [x] User approves owner-signed authorization and GitHub-backed receipt preparation.
- [x] Preserve Stage A lock, nine models, historical artifacts and frozen memberships.
- [x] Implement synthetic signature, create-only receipt, checkpoint and state protocols.
- [x] Add portable execution lock, synthetic CI and operational instructions.
- [ ] User reviews safeguards PR and exact execution identity.
- [x] User separately approves disposable GitHub write testing and manual ruleset setup.
- [x] Verify live GitHub creation/duplicate/update/deletion behavior and persistence (complete; do not repeat).
- [ ] Pin owner public key and verify independent private checkpoint backup.
- [ ] Complete reviewed real coordinator integration; obtain separate Stage B approval.

Preparation tests are not live enforcement evidence. No production receipt is created;
no holdout features/outcomes are accessed; no automatic recovery or Phase 10.


### Stage B coordinator and journal preparation — execution NOT authorized
- [x] Preserve documentation commit 93ab406 and independently verified live synthetic evidence.
- [x] Connect trusted bindings, authorization, receipt, journal, seals and signed recovery.
- [x] Implement synthetic feature/outcome interfaces using unchanged statistical kernels.
- [x] Add bounded private bundle export/restore and failure/end-to-end tests.
- [ ] Review coordinator implementation and new portable implementation lock.
- [ ] Pin owner public key and review later real data/model adapters under a NEW lock.
- [ ] Verify owner-controlled off-workspace transfer/restore and journal-tip retention.
- [ ] Configure/verify future production receipt and journal protections separately.
- [ ] Obtain separate final Stage B approval; no production receipt or holdout access yet.

### Production adapter preparation (separate review)

- [x] Pin owner public key and verify decoded-byte fingerprint.
- [x] Prepare disabled adapters and preserved-model/seal verification.
- [x] Preserve historical locks; add portable preparation lock and synthetic CI.
- [x] Record owner-reported small synthetic Mac restore.
- [x] Verify a full-size encrypted synthetic private transfer and independent Mac restore.
- [ ] Review activation release, new lock and exact unsigned authorization.
- [ ] Separately approve Stage B one-time execution (not authorized here).

See [operations](PRODUCTION_ADAPTER.md). Read-only production ruleset configuration
is recorded; no production receipt/journal or additional live write test is created.


### Stage B activation integration — preparation only, separate review

- [x] Owner confirms all 13 synthetic download checksums, decryption and Mac restore.
- [x] Integrate signed approval, fixed receipt, journal, nine models and strict adapters.
- [x] Require exact encrypted checkpoint/Mac-restore attestation before outcome access.
- [x] Verify durable outcome-access transition before constructing the outcome reader.
- [x] Add synthetic failure, concurrency, interruption and recovery verification.
- [x] Preserve historical locks; prepare additive lock and non-signable approval draft.
- [ ] Owner reviews activation integration PR, lock and preflight trust assumptions.
- [ ] Choose exact reviewed commit, fresh preflight and UTC window <=24h; review payload.
- [ ] Owner separately explicitly approves/signs ONE Stage B execution on the Mac.
- [ ] Transfer/restore the ACTUAL prediction checkpoint and obtain its signed proof.
- [ ] Perform one-time outcome evaluation only after all gates; review before later work.

The synthetic transport result is not a production checkpoint or execution approval.
See [activation protocol](STAGE_B_ACTIVATION.md). No Stage B execution or Phase 10.
