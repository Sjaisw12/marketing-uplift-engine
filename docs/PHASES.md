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
- [ ] Freeze T-learner, three-fold training-only nuisance and multiplier protocol.
- [ ] Verify preserved Phase 6 estimates, artifacts and frozen memberships.
- [ ] Pass synthetic statistical, covariance, leakage and integration gates.
- [ ] Complete and verify the first real split before the remaining four.
- [ ] Report IPW/DR, propensity/nuisance sensitivity, support, calibration and vector overlap.
- [ ] Verify all five evaluations, protected artifacts, reproducibility and CI.
- [ ] Publish completion evidence and receive user approval.

No final model/reach selection, abstention engine, dashboard or holdout evaluation
is included in Phase 7. Later phases require separate scope and approval.
