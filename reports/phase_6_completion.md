# Phase 6 completion evidence

Phase 6 implements the approved random, treated-response LightGBM and S-learner
baselines. No later-phase estimators, policy optimization or holdout evaluation
were implemented. Review and merge approval remain pending.

## Protocol and execution

- Started from merged Phase 5 main `b6ec130d0b2ac57c5c807142c6200a4744415ab3`,
  verified again against fetched origin/main; branch `codex/phase-6-baselines`.
- Recipes, ranking rules, full-prefix metric conventions and inference assumptions
  were committed in `1e89baf` before real performance was examined.
- Nine-page authoritative roadmap remained readable, SHA-256
  `e1b1a2d40ca6d91393beaf2bceb57b6d049dd667deab29d6bd5db7e87826c364`.
- Synthetic statistical/model gates passed before the first real split.
- Split 104729 completed first; three read-only integration checks passed before
  the other four began. Saved models reproduced predictions exactly; independent
  row-level aggregation and trapezoidal integration matched reported metrics.
- All five splits completed with the unchanged 200-round recipes, all 12 user
  predictors and no subsampling, tuning or early stopping. Training rows per split:
  response 8,080,205; S-learner 9,506,122. Each validation contains 2,376,531 rows:
  2,020,052 treatment (98,060 visits), 356,479 control (13,618 visits).
- All 11,882,653 development records and the sealed 2,096,939-row holdout remain
  intact. All 25 protected files, including all 12 memberships, raw source,
  Parquet, registry, manifests and earlier evidence, match the pre-branch snapshot.
- A second `make baselines` reused verified completed artifacts, performed no
  retraining and produced byte-identical aggregate JSON.

## Actual reference-scenario results

Mean gain relative to no targeting, per 1,000 eligible validation records, under
constant e=.85. These five-split means are descriptive, not independent-replication
estimates or proven causal gains.

| Reach | Random | Treated response | S-learner |
|---|---:|---:|---:|
| 10% | 1.0803 | 8.1106 | 9.3593 |
| 20% | 2.0938 | 9.6625 | 10.0543 |
| 30% | 3.1557 | 9.9850 | 10.1279 |
| 40% | 4.1446 | 10.1473 | 10.1999 |
| 50% | 5.2123 | 10.2005 | 10.2604 |

None/all value anchors are 38.2013/48.5433 per 1,000. At 10% reach, the mean
S-minus-response contrast is +1.2487 per 1,000. All five within-split nominal
simultaneous bands exclude zero positively; for split 104729 the band is
[0.6445, 1.7634], versus pointwise [0.7646, 1.6248]. At 20%, three of five
simultaneous bands exclude zero positively; none do at 30%, 40% or 50%.
This is not five independent confirmations or a pooled confidence interval.

The 10% contrast reverses to −2.0561 under e=.80 and becomes +7.1934 under e=.90.
This substantial assumption sensitivity prevents an unqualified causal superiority
claim. All five propensity scenarios, support counts and paired intervals are in
`phase_6_metrics.json`. Mean full-prefix IPW Qini areas at e=.85 are random
0.00004075, response 0.00441311, S-learner 0.00472830; conventions are unnormalized
areas above the random diagonal, with every validation prefix included.

The 2,000-replicate paired bootstrap uses 720–732 occupied compressed cells per
split. Synthetic checks establish equality with ordinary row-bootstrap calculations
for the same row multiplicities. Pointwise percentile and simultaneous standardized
maximum-deviation bands condition on fitted models and original policies. They
exclude refitting/reranking, unknown clusters and development-stratification effects.
The release's selection mechanism and unknown experiment propensities remain
unresolved; sensitivity scenarios do not validate assignment or identify causal gains.

## Resources and artifacts

The environment has 8 GiB RAM and a two-CPU quota. Disk preflight showed about
29 GiB free. Sequential extraction/training/prediction used two LightGBM threads,
one DuckDB thread, a 2 GB DuckDB limit and 65,536-row batches. Split elapsed
seconds were 190.12, 197.27, 187.25, 182.53 and 181.65 (sum 938.83 seconds;
verification/reporting overhead excluded). Peak training process RSS was 3.026 GiB;
the environment high-water mark including other checks was about 4.44 GiB.
No OOM events, estimator substitutions, data reductions or recipe changes occurred.

Private persisted Phase 6 models/predictions occupy about 370 MiB, with about
374 MiB in local MLflow including copies and metadata. Temporary extraction caches
created by Phase 6 were removed after successful use; no existing data were deleted.
All five MLflow runs record settings, versions, source/split/code hashes, models,
predictions, predictive metrics, policy values, areas and aggregate reports.
Raw data, memberships, model files, predictions and MLflow remain Git-ignored.

Cloud-local datasets and MLflow are not guaranteed to persist into a new task.
Git preserves recipes, the frozen registry and aggregate evidence, not fitted models
or records. If artifacts are missing, verify/reacquire the pinned archive, validate,
ingest and reconstruct only missing memberships against the existing registry.
Existing matching artifacts should be preserved. Cross-platform bitwise model
identity is not claimed; local prediction reload and resume identity were checked.

## Actual verification

- `make check`: **114 passed**, 12 full-data tests deselected; lint and formatting pass.
- First-split gate: **3 passed** before continuing unchanged recipes.
- Final read-only full-data checks: **11 passed, 1 deselected**, covering Phase 3–6.
  The pre-existing reconstruction test was intentionally excluded locally because
  it rewrites its report. Existing memberships were verified, not reconstructed.
- `git diff --check` passed; no tracked file exceeds 10 MB; all data/model directories
  were confirmed ignored. The source archive still has expected SHA-256
  `2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc`.
- GitHub Actions cheap checks now cover the new synthetic tests on Python 3.11/3.12.
  Optional manual `run_baselines=true` executes first-split verification, all five
  evaluations and read-only checks; uploads contain only small aggregate evidence.
  Local results are not claimed as independent remote full-data verification.

Reproduce verification in the intact workspace:

```sh
make check
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 make baselines
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 uv run --locked pytest \
  tests/test_baselines_full.py tests/test_full_data.py \
  tests/test_data_audit_full.py tests/test_development_ate_full.py \
  -m full_data -k 'not reconstruct'
```

Changes: fixed recipe/protocol, baseline training and policy-metric modules,
aggregate report renderer, CLI/Makefile, statistical/synthetic/full-data tests,
GitHub Actions, four Phase 6 evidence reports plus first-split evidence, README,
phase checklist and interview explanation/questions. Phase 5 approval is recorded;
Phase 6 completion approval remains unchecked until review.
