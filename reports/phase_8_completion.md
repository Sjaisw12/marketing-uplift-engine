# Phase 8 completion evidence

Phase 8 implements the separately approved development-only abstention and budget
simulator. It preserves Phase 6/7 and does not train models, select or lock a final
deployment policy, access final holdout outcomes, implement Streamlit or start Phase 9.
Completion remains subject to user review; do not merge without approval.

## Frozen execution and preservation

Created codex/phase-8-decision-engine from merged main
1b71979f5e77b580c34bda664f881fec52e9570d. Commit 4bd79aa froze the economic scenarios,
role algorithm, successive-tranche objective, uncertainty protocol and synthetic
gates before new real-data evaluation. Statistical protocol SHA-256:
`b85ec9422576797929a8d3ee731cb1f1c2bb6cec329a60bca98c66a5beecbf81`.

Six existing Phase 6/7 read-only full-data tests passed in 89.79 seconds after the
branch switch, reproducing original estimates and checking model reloads/alignment,
artifacts and MLflow. All 201 protected file/tree entries match before/after Phase 8:
source/archive/Parquet, all 12 memberships/registry, prior reports/configuration,
protocol source, old models/predictions/MLflow trees and uv.lock. No protected
artifacts were recreated, replaced or deleted. Phase 7 approval is now recorded in
docs/PHASES.md and Phase 8 has its own scoped checklist.

Every existing validation partition has 2,376,531 rows. All five auxiliary role files
were frozen and hashed before Phase 8 outcome queries: 1,188,265 selection and
1,188,266 assessment records per split. The source development pool remains
11,882,653 rows; roles across overlapping splits must not be summed as unique users.
Selection decisions, selected-ID hashes and outcome-blind assessment applications
persist before assessment outcomes are queried. Assessment support is diagnostic;
it cannot revise a recommendation. The sealed 2,096,939-row holdout is unchanged.

## Actual findings

All 40 economic-scenario/split combinations recommend zero assignments and zero
hypothetical spending, leaving the entire available budget unspent:

- Zero visit value: no economic objective for spending.
- Below-first-reach budget: no feasible positive policy on the declared 10% grid.
- Remaining scenarios: sensitivity across the declared assumptions prevents a
  positive conservative first tranche. In the low-value scenario some rankings
  additionally have insufficient point-estimated net benefit under every scenario.

The rule was not relaxed, economics were not retuned, and no favorable evaluator
was chosen after observing universal abstention. This result does not establish
that all real-world campaigns or unexamined smaller reaches are unprofitable.

For first-split selection S at 10%, point gains range from −1.2511 to +16.0286 visits
per 1,000 eligible records across the 15 assumptions; the worst simultaneous lower
bound is −2.7875. Across five splits, S's worst lower bound ranges from −3.5703 to
−2.7875 per 1,000. Even free assignments cannot turn those negative lower visit gains
into positive robust net value.

By comparison, under reference assumed e=.85 on the first assessment role, S 10%
has IPW gain 9.0374/1,000 (pointwise 95% interval [8.3450,9.7518]), primary DR 5.8806
[5.3218,6.4231] and saved-S DR 5.8128[5.2512,6.3608]. Those positive conditional
reference results do not justify ignoring negative stress scenarios. The full
fixed-reach and all/none comparisons, all five splits and all 15 assumptions are in
phase_8_metrics.json and phase_8_economics.json; readable tables are in
phase_8_decisions.md and phase_8_sensitivity.md. Matched-spending comparators are
necessarily also no targeting when the engine spends zero. Same-cap fixed policies
remain separately reported, with their actual different spending.

No selection or assessment tranche violated the support gate: minimum control
visits were 54 in selection and 61 in assessment. Original calibration and vector
overlap evidence is preserved; exact matching vectors are not customer identifiers.

## Statistical verification

- make check:143 fast tests passed;17 full-data tests deselected; lint and formatting pass.
- Six preserved Phase 6/7 read-only full-data checks passed (89.79s).
- First real split independently passed the explicit receipt gate before remaining
  execution. Direct mean error<=1.7348e-17; variance error<=4.7646e-22.
- Two new read-only full-data tests passed across all five splits (48.88s), checking
  roles, immutable recommendations, budget compliance, selected-ID alignment,
  source-row formulas, paired covariance, all 300-coordinate critical values, private
  artifact hashes and MLflow copies. Maximum direct mean error 3.1226e-17 and variance
  error 6.8822e-22 across 360 coordinates per role.
- Synthetic independent 511-row reference: maximum mean error 1.6654e-16, covariance
  error 1.1276e-17 and Gaussian row-multiplier covariance error 1.4746e-17 across three
  batch sizes. Tests cover ordinary ties, budget rounding, negative/zero benefit,
  zero cost, partial spending, stopping the first failed tranche, singular/zero
  variance and assessment-outcome mutation without changing selection decisions.
- Byte-identical aggregate report resume is recorded in phase_8_reproducibility.json;
  matching artifacts are verified rather than rerun or overwritten.
- JUnit metadata export emitted one pytest record_property/xunit 2 schema warning;
  it affected neither test success nor numerical/evaluation results. No data,
  model, resource or statistical execution warning was suppressed.

The simultaneous lower family contains 300 marginal coordinates within each role
and split, with 2000 shared Gaussian draws. Selection critical values range 2.9331–
3.0675; assessment 3.0144–3.0428. Pointwise intervals remain separate. They are
nominal IID working-model intervals conditional on fitted models/policies, not
ordinary row-bootstrap or exact randomization inference. No across-split coverage
or independent-replication confidence interval is claimed.

## Resources and tracking

No fitting was required. Existing 8GiB/two-CPU resources were retained; bounded
DuckDB, batch 65536, shared-cell moments and sequential evaluation avoided an
N-by 2000 array. Split evaluation times were 7.91,7.27,7.48,7.15,8.45 seconds
(total 38.27, excluding protection/gate/report overhead). Maximum process RSS was
0.583GiB. Minimum recorded free disk was 25.278GiB. The environment's historical
memory high-water mark remains 8GiB with 18 cap/reclamation events from previous
work; all Phase 8 before/after snapshots show no additional cap events, OOM or kills.

Private Phase 8 artifacts occupy approximately 76MiB, including role labels,
uncertainty matrices, sealed decisions/applications, verification receipts and
per-split results. Five new local MLflow evaluation runs contain settings, dataset/
split/role/model provenance, actual decisions and copied private evidence. Separate
publication runs preserve aggregate report versions; unchanged publication resumes
reuse matching hashes. Old Phase 6/7 runs remain read-only. No raw records,
predictions, memberships, model files or MLflow stores are committed or uploaded.

Cloud-local datasets, models and MLflow are not guaranteed across new tasks. This
workspace was intact and required no reacquisition, reconstruction or retraining.
Fresh independent CI uses separately authorized prerequisites in its own runner;
that is not a reason to recreate matching local artifacts.

## Limitations and review

Unknown pooled-experiment propensities, non-uniform privacy sampling, missing
customer/experiment IDs, possible dependence, outcome stratification and prior
development inspection remain unresolved. DR's double robustness requires causal
identification and appropriate nuisance correctness; it does not establish those
assumptions. Stress scenarios are not a probability distribution or verified bounds
on bias. Hypothetical costs/values do not support real revenue, ROI or savings.
No policy is recommended for final deployment by this phase.

New files: configs/phase8.toml; docs/PHASE8_PROTOCOL.md; decision_engine.py,
decision_metrics.py, decisions.py, decision_verification.py, decision_reports.py;
five decision test modules; aggregate Phase 8 reports, numerical/reproducibility/
verification evidence and this completion report. Updated: CLI, Makefile,
.github/workflows/ci.yml, README.md, INTERVIEW.md and docs/PHASES.md.

GitHub Actions now includes the statistical/leakage/budget fixtures in cheap Python
3.11/3.12 checks, plus optional manual run_decisions=true prerequisites, first-split
receipt, remaining-four and full verification. Only aggregate evidence is uploaded.
Local full-data results are not represented as independent remote verification.

Review the PR before merge. No final policy locking, holdout analysis, dashboard or
Phase 9 work is authorized by this completion report.
