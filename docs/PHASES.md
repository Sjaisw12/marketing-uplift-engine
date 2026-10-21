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

## Phase 9 — policy lock and one-time final evaluation (completed)

Historical preparation protocols and locks remain immutable. Their preparation-only
statements describe the approval state at creation; the checklist below records the
subsequent separately approved execution. No previous lock is resealed.

### Stage A — preparation and policy lock
- [x] Owner approves separately scoped Stage A and its completion.
- [x] Freeze primary abstention, diagnostic policies, nine refit recipes and methodology.
- [x] Verify synthetic estimators, 765-family, stratified sensitivity and leakage boundaries.
- [x] Fit nine development-only final models; preserve all historical models/results.
- [x] Record reviewed policy, model, code, data and dependency identities.

### Stage B — safeguards and explicit execution gates
- [x] Review and merge safeguards, coordinator, adapters, activation and continuity (PRs #11–14).
- [x] Pin owner public key; private signing/encryption keys remain owner-controlled.
- [x] Verify synthetic live receipt protection; retain evidence without repeating the test.
- [x] Verify full-size encrypted synthetic transfer and independent Mac restore.
- [x] Verify production receipt/journal protections and reviewed child execution lock.
- [x] Obtain separate signed start approval; claim one fixed production receipt.
- [x] Score only frozen holdout features; preserve nine models and frozen policies.
- [x] Publish encrypted prediction backup and stop at the durable publication pause.
- [x] Owner independently restores and verifies the actual prediction checkpoint.
- [x] Obtain fresh signed backup proof, continuation approval and matching preflight.
- [x] Verify continuation, seal and durable outcome-access transition before outcome access.
- [x] Complete one locked evaluation and 765-contrast family; close worker without replay.
- [x] Owner reviews completion and approves Phase 10 portfolio finalization.

Stage B is completed and closed, not available for another execution. See the
Phase 10 aggregate provenance and completion report for final result identities.
Signed approvals, private checkpoints, row-level predictions and operational
receipts are not portfolio publication assets.

## Phase 10 — portfolio finalization (release preparation)
- [x] Owner approves coordinated documentation/figure/test scope without experiment reruns.
- [x] Create isolated local branch and preserve Phase 1–9 evidence and private state.
- [x] Reconcile aggregate-only snapshot with the completed evaluation and review disclosure.
- [x] Produce README, architecture/workflow diagram, case study and model card.
- [x] Produce descriptive, reach, uncertainty, sensitivity and paired-comparison figures.
- [x] Provide aggregate-only reproduction code and validation tests.
- [x] Provide interview pitch, walkthrough, technical discussion and challenging questions.
- [x] Complete final local checks and record actual verification evidence.
- [x] Owner independently reviews materials and conditionally approves release preparation.
- [x] Owner approves Phase 10 aggregate disclosure and PR #15; merged main is 7a038ffe.

No dashboard, deployment, new model, outcome access or Stage B execution is included.
The roadmap's dashboard/demo/recording remain unimplemented, not claimed as complete.

## Phase 11 — interactive aggregate dashboard and deployment readiness
- [x] Owner approves one coordinated implementation phase using public Phase 10 aggregates only.
- [x] Create isolated branch from merged main 7a038ffe; preserve existing ignored artifacts.
- [x] Implement overview, equal-reach policies, saved sensitivity and model explanations.
- [x] Implement hypothetical budget arithmetic with no automatic policy/reach selection.
- [x] Preserve no targeting, exact snapshot provenance and saved uncertainty semantics.
- [x] Pin the minimal Python 3.12 deployment environment; leave research locks unchanged.
- [x] Document launch, provider deployment checklist, licensing and live-link approval steps.
- [x] Complete local tests, minimal-environment headless smoke and responsive UI review.
- [ ] Owner reviews the finished dashboard and approves publication preparation.
- [ ] Owner explicitly authorizes any push, PR, merge or public deployment.

Phase 10's dashboard exclusion describes its historical scope. Phase 11 adds a
local aggregate presentation app, not a model-serving or live targeting system.
No new holdout analysis, experiment, private artifact access or public deployment
is authorized by this phase.
