# Phase 7 completion evidence

Phase 7 adds a fixed T-learner and shared, training-only doubly robust policy
evaluator. No final model/reach was selected, no holdout outcomes were analyzed,
and no abstention engine, dashboard or later-phase implementation was added.
Completion approval remains pending review.

## Protocol and preservation

Branch: codex/phase-7-robust-uplift, based on merged main
`2d0df11faeb45521960e6f993ce2e97f466e7f7a`.
The frozen specification, model/nuisance code and synthetic gates were committed
in `a2496af` before new real-data performance was examined. Protocol SHA-256:
`f3201b0fad04191b48607f269d1d1e1a3d25ef0203f6df06c7f1578881eee83e`.

All twelve frozen memberships, source archive, Parquet, earlier reports, Phase 6
models/predictions/protocol/MLflow runs and dependency lockfile remain unchanged.
The before/after protection record has 71 file/tree entries, including five complete
Phase 6 MLflow run-tree fingerprints. The original 25 protected input files are
included. Phase 6 approval was recorded in docs/PHASES.md; Phase 7 has a separate
approved scope and completion checklist.

Phase 6's three read-only integration checks reproduced its point estimates before
new model execution. The new evaluator also checks every historical baseline
fixed-reach IPW point estimate. No Phase 6 model was retrained.

## Actual execution

All five existing development splits were used, with 9,506,122 training and
2,376,531 validation records each. Every validation partition has 2,020,052 treated
records/98,060 visits and 356,479 controls/13,618 visits.

The T-learner reuses the corresponding Phase 6 treated-response model (8,080,205
training records) and fits a control model on 1,425,917 records/54,471 visits.
Every new arm model uses exactly f0–f11, 200 rounds and the frozen Phase 6 recipe.
Treatment is only a routing variable; no exposure, outcome or identifier is a predictor.

Three auxiliary nuisance folds are derived only from each frozen outer-training
partition. All five fold-label files were hashed before fitting. Six arm regressions
per split produce factual OOF diagnostics and averaged outer-validation predictions
for a common DR evaluator. Minimum positive-event support among nuisance fits was
36,080 controls and 260,868 treated visits. All thirty-five new models completed.
Model/prediction fit manifests were recorded before evaluation. Saved S-learner
outcome predictions provide a separate nuisance sensitivity; no evaluator was selected
by validation performance.

Split 104729 completed first. Three integration gates passed before continuing
unchanged through the other four splits. No recipe changes, data reduction,
calibration fitting, early stopping or silent estimator substitutions occurred.

## Measured findings

Five-split descriptive mean gain over no targeting, per 1,000 eligible validation
records, under reference assumed e=.85:

| Reach | IPW S | IPW T | Shared DR S | Shared DR T |
|---|---:|---:|---:|---:|
| 10% | 9.3593 | 8.9952 | 5.9693 | 5.7731 |
| 20% | 10.0543 | 9.8294 | 6.8630 | 6.6526 |
| 30% | 10.1279 | 10.0332 | 7.0812 | 6.8848 |
| 40% | 10.1999 | 10.1081 | 7.1798 | 6.9691 |
| 50% | 10.2604 | 10.1683 | 7.2751 | 7.0298 |

Random and response comparisons, anchors, all per-split results and all scenario
values appear in phase_7_comparison.md and phase_7_metrics.json. IPW full-prefix
AUUC/Qini definitions remain unchanged; DR ranking areas were not introduced.

At 10% reach, mean T-minus-S is -0.3641 per1,000 with IPW and -0.1962 with shared
DR. For first split 104729, the simultaneous ten-comparison bands are
[-0.8330, 0.0152] for IPW and [-0.5566, 0.1019] for DR. The corresponding
pointwise intervals are [-0.7517, -0.0982] and [-0.4831, 0.0119].
Across fifty within-split simultaneous bands, none lie wholly above zero, four
lie below zero and forty-six include zero. These are descriptive counts over
overlapping splits, not independent confirmations or a pooled inference.
No T-learner superiority or final choice is established.

At 10% reach, varying assumed e from .80 to .90 changes mean T-minus-S from
-0.0698 to -0.9074 with IPW and -0.1396 to -0.3180 with primary DR. Using the
saved S nuisance instead gives -0.2332 to -0.1172; at reference e=.85 its contrast
is -0.1936. All five propensity values and nuisance sensitivities are separate;
this range is not a verified bound on propensities or selection bias.
At reference 40%/50% reach, mean response-versus-S ordering changes between IPW
and DR. No favorable metric or evaluator is chosen.

No disjoint reach band triggered the <30 control-visit warning; the minimum was
123. Mean factual control-model AUC was 0.94754 and Brier score 0.025356.
Fixed calibration-bin counts and observed/predicted rates, arm-specific and OOF
metrics are included. These diagnostics do not establish individual-effect accuracy.
Validation rows with exact feature-vector matches in training range from 15.5092%
to 15.5841%. No deduplication, grouping changes or customer-identity claims were made.

## Uncertainty and limitations

Two thousand correlated Gaussian-multiplier replicates use the joint covariance
of centered fixed-policy contributions. Continuous cell moments reproduce the
sample covariance divided by n. The independent 511-row numerical reference,
covering 220 value coordinates and three batch sizes, had maximum absolute mean
error 1.9984e-15 and covariance error 1.7694e-16. Direct row-level contribution and
Gaussian-multiplier tests, zero-variance and singular cases passed. Tiny negative
roundoff eigenvalues are recorded and zeroed only within the frozen tolerance;
no substantive PSD failure occurred.

Intervals are nominal IID working-model intervals conditional on fitted models,
nuisance predictions and original targeting memberships, not an exact ordinary
row bootstrap. Pointwise quantiles and simultaneous bands over the ten T-minus-S
reference comparisons are distinguished. No across-split or across-sensitivity
coverage is claimed. Refitting, threshold estimation, dependence and stratified
sampling uncertainty are not included.

Double robustness requires causal identification and either correct propensity or
both correct outcome regressions with suitable estimation conditions. It does not
undo non-uniform privacy selection, identify hidden experiment probabilities,
verify exchangeability or eliminate dependence. Outcome calibration and numerical
precision do not establish these assumptions. These reused development splits are
not a fresh confirmatory sample. No causal superiority, advertiser-wide lift,
individual-effect accuracy or economic impact is claimed.

## Resources and tracking

The environment has 8 GiB RAM and two CPUs. Fits were sequential with two LightGBM
threads, one DuckDB thread, 2 GB DuckDB query memory, bounded spill and batched
prediction. Split workload elapsed seconds were 280.92, 289.31, 281.90, 281.03 and
288.15 (sum 1,421.32; final publication and verification overhead excluded).
Maximum model-process RSS was 3.736 GiB. No OOM, OOM kill, failed allocation or
method substitution occurred. The environment-wide memory high-water mark reached
its 8 GiB cap and recorded 18 cap/reclamation events; this includes file cache and
other checks and is distinct from model-process RSS. All requested runs completed.

New private Phase 7 artifacts occupy approximately 1.4 GiB; total local MLflow
including Phase 6/7 is approximately 1.7 GiB. Disk remained available. Only newly
created extraction caches were removed after successful execution. Five new MLflow
runs contain provenance, recipes, seeds, fit manifests, models, predictions, OOF
records, diagnostics, policy metrics, resource evidence and aggregate reports.
Old Phase 6 runs remain read-only.

Cloud-local data/models/MLflow are not guaranteed across new tasks. Git retains
code and aggregate evidence, not source records, fitted models or memberships.
Restore missing artifacts deliberately and verify them; do not overwrite existing
matching assets or silently replace mismatches.

## Actual verification and review package

- Fast checks: 125 tests passed; lint and formatting passed.
- Phase 6 preflight: three read-only checks passed before new execution.
- First Phase 7 split gate: three checks passed before remaining fits.
- Final Phase 6/7 full-data checks: six passed, including model reloads, row alignment,
  nuisance exclusion, primary/private/MLflow hashes, independent formulas and
  standard errors, baseline point reproduction and full-prefix integration.
- Resume performed no retraining and produced byte-identical aggregate JSON.
- Git diff whitespace checks passed; no raw data or serialized model/record files
  are tracked. All existing protected inputs and Phase 6 fingerprints match.
- GitHub Actions includes Python 3.11/3.12 synthetic checks and optional manual
  run_advanced=true prerequisites/first-split/all-five verification. Local full-data
  evidence is not represented as independent remote verification.

Created: configs/phase7.toml, docs/PHASE7_PROTOCOL.md, advanced.py,
robust_metrics.py, advanced_reports.py, statistical/unit/full-data tests,
verify_phase7_numerics.py and Phase 7 aggregate reports/evidence.
Updated: CLI, Makefile, GitHub Actions, README, INTERVIEW and phase checklist.
Dependency lockfile and frozen Phase 6 protocol/source/results remain unchanged.

Review is required before merge or any Phase 8 work.
