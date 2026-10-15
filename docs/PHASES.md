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
- [ ] Download official archive at pinned revision.
- [ ] Verify exact basename, byte count and SHA-256 before ingestion.
- [ ] Persist provenance manifest without inventing unverified row counts.
- [ ] Report evidence; receive approval.

## Phase 3 — contract, ingestion, partitions
- [ ] Validate exact schema/rows, types, binary values, rates and nonfinite counts.
- [ ] Audit coercions; no silent row drops or deduplication.
- [ ] Produce typed Parquet; enforce leakage tests on every feature export.
- [ ] Seal 15% holdout before exploratory analysis; record membership hashes.
- [ ] Freeze five joint-stratified 80/20 dev re-splits and save seeds in artifacts/splits.json.
- [ ] Verify disjointness, coverage and reproducibility; activate real full-data CI.
- [ ] Report evidence; receive approval.

## Phase 4 — development audit
- [ ] Audit distributions, missingness, arm balance, repeated vectors and strata.
- [ ] Publish reports/data_audit.md with deviations and limitations.
- [ ] Report evidence; receive approval.

## Phase 5 — development ATE
- [ ] Report arm sizes, event counts, visit rates and difference with 95% CI.
- [ ] Express effects per 1,000 rows; state ITT and released-sample limitations.
- [ ] Report evidence; receive approval.

## Phase 6 — baselines
- [ ] Freeze random, visit-propensity and S-learner definitions and hyperparameters.
- [ ] Evaluate all five development re-splits at 10/20/30/40/50% reach.
- [ ] Include none/all anchors, metric conventions, IPW assumptions and event counts.
- [ ] Log provenance, models, predictions and metrics in local mlruns/.
- [ ] Publish development stability comparison; keep holdout sealed.
- [ ] Report evidence; receive approval.

Every completion updates INTERVIEW.md with an explanation and two tough questions.
T-learner, DR evaluation, final policy selection, dashboard and headline holdout
analysis require later scope and approval.
