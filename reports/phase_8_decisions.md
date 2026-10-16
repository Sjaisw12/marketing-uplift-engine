# Phase 8 — development-only budget and abstention simulation

All monetary inputs are hypothetical currency units, not observed Criteo costs,
revenue, ROI or savings. Values below are assumption-dependent released-development
benchmark estimates, not proven causal or financial improvements. Propensities are
assumptions; DR does not repair unknown experiment assignment, privacy selection or
unverified identification. Gaussian intervals are nominal IID working-model,
conditional on fitted models and fixed role-specific policies, excluding refitting,
unknown dependence and outcome-stratification uncertainty. Pointwise intervals differ
from the one-sided simultaneous 300-coordinate marginal decision bounds. Splits overlap;
mean/range and decision frequencies are descriptive, not independent replications.
Auxiliary assessment roles reduce direct selection reuse but are not fresh confirmatory
data: development outcomes informed prior phases. No deployment policy is selected or
locked, and the final holdout remains sealed.

## Frozen design

Protocol SHA-256: `b85ec9422576797929a8d3ee731cb1f1c2bb6cec329a60bca98c66a5beecbf81`.
Each outer validation has 1,188,265 selection and 1,188,266 assessment records.
Recommendations and assessment assignment hashes persisted before assessment outcome queries.
Eight predeclared economic configurations use exact budget density scaling B=b*N.
The objective sums worst-scenario simultaneous lower marginal net values, and stops at the first failed tranche.
Selection support requires both arms and 30 control visits per tranche; assessment support is diagnostic only.
No model retraining, recalibration, split regeneration, holdout outcome analysis or lockfile change.

## Hypothetical scenarios

| Scenario | Assignment cost | Visit value | Budget/eligible record | Max reach |
|---|---:|---:|---:|---:|
| zero_value | 0.01 | 0 | 0.005 | 0.5 |
| below_first_reach | 0.01 | 1 | 0.0005 | 0.5 |
| low_value | 0.01 | 0.25 | 0.005 | 0.5 |
| illustrative_reference | 0.01 | 1 | 0.005 | 0.5 |
| higher_value | 0.01 | 5 | 0.005 | 0.5 |
| limited_budget | 0.01 | 1 | 0.0025 | 0.5 |
| zero_cost | 0 | 1 | 0 | 0.5 |
| all_targeting_feasible | 0.01 | 1 | 0.01 | 1 |

## Provisional selection and assessment decisions

| Split | Scenario | Model | Selection reach | Assessment reach | Assignments | Spending | Unspent | Reasons |
|---|---|---|---:|---:|---:|---:|---:|---|
| 104729 | zero_value | none | 0.000000% | 0.000000% | 0 | 0.00 | 5941.330 | zero_value |
| 104729 | below_first_reach | none | 0.000000% | 0.000000% | 0 | 0.00 | 594.1330 | no_feasible_positive_reach |
| 104729 | low_value | none | 0.000000% | 0.000000% | 0 | 0.00 | 5941.330 | assumption_sensitive, negative_estimated_net_benefit |
| 104729 | illustrative_reference | none | 0.000000% | 0.000000% | 0 | 0.00 | 5941.330 | assumption_sensitive |
| 104729 | higher_value | none | 0.000000% | 0.000000% | 0 | 0.00 | 5941.330 | assumption_sensitive |
| 104729 | limited_budget | none | 0.000000% | 0.000000% | 0 | 0.00 | 2970.6650 | assumption_sensitive |
| 104729 | zero_cost | none | 0.000000% | 0.000000% | 0 | 0 | 0 | assumption_sensitive |
| 104729 | all_targeting_feasible | none | 0.000000% | 0.000000% | 0 | 0.00 | 11882.66 | assumption_sensitive |
| 130363 | zero_value | none | 0.000000% | 0.000000% | 0 | 0.00 | 5941.330 | zero_value |
| 130363 | below_first_reach | none | 0.000000% | 0.000000% | 0 | 0.00 | 594.1330 | no_feasible_positive_reach |
| 130363 | low_value | none | 0.000000% | 0.000000% | 0 | 0.00 | 5941.330 | assumption_sensitive, negative_estimated_net_benefit |
| 130363 | illustrative_reference | none | 0.000000% | 0.000000% | 0 | 0.00 | 5941.330 | assumption_sensitive |
| 130363 | higher_value | none | 0.000000% | 0.000000% | 0 | 0.00 | 5941.330 | assumption_sensitive |
| 130363 | limited_budget | none | 0.000000% | 0.000000% | 0 | 0.00 | 2970.6650 | assumption_sensitive |
| 130363 | zero_cost | none | 0.000000% | 0.000000% | 0 | 0 | 0 | assumption_sensitive |
| 130363 | all_targeting_feasible | none | 0.000000% | 0.000000% | 0 | 0.00 | 11882.66 | assumption_sensitive |
| 155921 | zero_value | none | 0.000000% | 0.000000% | 0 | 0.00 | 5941.330 | zero_value |
| 155921 | below_first_reach | none | 0.000000% | 0.000000% | 0 | 0.00 | 594.1330 | no_feasible_positive_reach |
| 155921 | low_value | none | 0.000000% | 0.000000% | 0 | 0.00 | 5941.330 | assumption_sensitive, negative_estimated_net_benefit |
| 155921 | illustrative_reference | none | 0.000000% | 0.000000% | 0 | 0.00 | 5941.330 | assumption_sensitive |
| 155921 | higher_value | none | 0.000000% | 0.000000% | 0 | 0.00 | 5941.330 | assumption_sensitive |
| 155921 | limited_budget | none | 0.000000% | 0.000000% | 0 | 0.00 | 2970.6650 | assumption_sensitive |
| 155921 | zero_cost | none | 0.000000% | 0.000000% | 0 | 0 | 0 | assumption_sensitive |
| 155921 | all_targeting_feasible | none | 0.000000% | 0.000000% | 0 | 0.00 | 11882.66 | assumption_sensitive |
| 181081 | zero_value | none | 0.000000% | 0.000000% | 0 | 0.00 | 5941.330 | zero_value |
| 181081 | below_first_reach | none | 0.000000% | 0.000000% | 0 | 0.00 | 594.1330 | no_feasible_positive_reach |
| 181081 | low_value | none | 0.000000% | 0.000000% | 0 | 0.00 | 5941.330 | assumption_sensitive, negative_estimated_net_benefit |
| 181081 | illustrative_reference | none | 0.000000% | 0.000000% | 0 | 0.00 | 5941.330 | assumption_sensitive |
| 181081 | higher_value | none | 0.000000% | 0.000000% | 0 | 0.00 | 5941.330 | assumption_sensitive |
| 181081 | limited_budget | none | 0.000000% | 0.000000% | 0 | 0.00 | 2970.6650 | assumption_sensitive |
| 181081 | zero_cost | none | 0.000000% | 0.000000% | 0 | 0 | 0 | assumption_sensitive |
| 181081 | all_targeting_feasible | none | 0.000000% | 0.000000% | 0 | 0.00 | 11882.66 | assumption_sensitive |
| 206369 | zero_value | none | 0.000000% | 0.000000% | 0 | 0.00 | 5941.330 | zero_value |
| 206369 | below_first_reach | none | 0.000000% | 0.000000% | 0 | 0.00 | 594.1330 | no_feasible_positive_reach |
| 206369 | low_value | none | 0.000000% | 0.000000% | 0 | 0.00 | 5941.330 | assumption_sensitive, negative_estimated_net_benefit |
| 206369 | illustrative_reference | none | 0.000000% | 0.000000% | 0 | 0.00 | 5941.330 | assumption_sensitive |
| 206369 | higher_value | none | 0.000000% | 0.000000% | 0 | 0.00 | 5941.330 | assumption_sensitive |
| 206369 | limited_budget | none | 0.000000% | 0.000000% | 0 | 0.00 | 2970.6650 | assumption_sensitive |
| 206369 | zero_cost | none | 0.000000% | 0.000000% | 0 | 0 | 0 | assumption_sensitive |
| 206369 | all_targeting_feasible | none | 0.000000% | 0.000000% | 0 | 0.00 | 11882.66 | assumption_sensitive |

## Assessment at reference assumed e=.85

Intervals below are paired-draw pointwise 95% working-model intervals, not the decision family bounds.

| Split | Scenario | Evaluator | Incremental visits/1,000 | 95% interval/1,000 | Hypothetical net value |
|---|---|---|---:|---|---:|
| 104729 | zero_value | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | zero_value | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | zero_value | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | below_first_reach | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | below_first_reach | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | below_first_reach | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | low_value | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | low_value | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | low_value | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | illustrative_reference | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | illustrative_reference | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | illustrative_reference | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | higher_value | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | higher_value | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | higher_value | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | limited_budget | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | limited_budget | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | limited_budget | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | zero_cost | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | zero_cost | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | zero_cost | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | all_targeting_feasible | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | all_targeting_feasible | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 104729 | all_targeting_feasible | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | zero_value | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | zero_value | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | zero_value | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | below_first_reach | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | below_first_reach | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | below_first_reach | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | low_value | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | low_value | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | low_value | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | illustrative_reference | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | illustrative_reference | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | illustrative_reference | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | higher_value | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | higher_value | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | higher_value | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | limited_budget | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | limited_budget | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | limited_budget | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | zero_cost | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | zero_cost | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | zero_cost | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | all_targeting_feasible | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | all_targeting_feasible | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 130363 | all_targeting_feasible | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | zero_value | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | zero_value | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | zero_value | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | below_first_reach | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | below_first_reach | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | below_first_reach | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | low_value | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | low_value | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | low_value | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | illustrative_reference | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | illustrative_reference | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | illustrative_reference | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | higher_value | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | higher_value | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | higher_value | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | limited_budget | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | limited_budget | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | limited_budget | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | zero_cost | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | zero_cost | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | zero_cost | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | all_targeting_feasible | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | all_targeting_feasible | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 155921 | all_targeting_feasible | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | zero_value | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | zero_value | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | zero_value | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | below_first_reach | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | below_first_reach | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | below_first_reach | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | low_value | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | low_value | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | low_value | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | illustrative_reference | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | illustrative_reference | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | illustrative_reference | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | higher_value | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | higher_value | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | higher_value | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | limited_budget | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | limited_budget | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | limited_budget | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | zero_cost | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | zero_cost | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | zero_cost | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | all_targeting_feasible | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | all_targeting_feasible | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 181081 | all_targeting_feasible | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | zero_value | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | zero_value | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | zero_value | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | below_first_reach | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | below_first_reach | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | below_first_reach | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | low_value | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | low_value | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | low_value | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | illustrative_reference | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | illustrative_reference | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | illustrative_reference | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | higher_value | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | higher_value | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | higher_value | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | limited_budget | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | limited_budget | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | limited_budget | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | zero_cost | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | zero_cost | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | zero_cost | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | all_targeting_feasible | ipw | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | all_targeting_feasible | dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |
| 206369 | all_targeting_feasible | s_dr | 0.0000 | [0.0000, 0.0000] | 0.0000 |

## Fixed-reach assessment comparisons

Descriptive five-split mean [range] gain per 1,000 eligible records at assumed e=.85.
Role-specific policies preserve ranking rules; historical Phase 6/7 results are unchanged.
All four rankings have equal actual assignment counts within each reach.
Economics JSON separately applies feasible caps and hypothetical spending.

| Reach | Evaluator | Random | Response | S | T |
|---|---|---:|---:|---:|---:|
| 10% | ipw | 1.0197 [0.9406, 1.0950] | 8.0733 [7.5368, 8.5503] | 9.3830 [9.0374, 9.7047] | 9.0123 [8.7820, 9.4430] |
| 10% | dr | 0.7479 [0.6427, 0.8190] | 5.1431 [4.7266, 5.4262] | 5.9179 [5.5855, 6.2690] | 5.7477 [5.4977, 5.9065] |
| 10% | s_dr | 0.7403 [0.6337, 0.8150] | 5.0753 [4.6749, 5.3514] | 5.8445 [5.5258, 6.1817] | 5.6750 [5.4275, 5.8189] |
| 20% | ipw | 1.9636 [1.4534, 2.1788] | 9.6076 [9.2856, 9.9565] | 10.1055 [9.8532, 10.6667] | 9.7651 [9.4199, 10.0760] |
| 20% | dr | 1.3933 [1.1318, 1.5367] | 6.6426 [6.4026, 6.9340] | 6.8765 [6.6964, 7.0852] | 6.5657 [6.2118, 6.7330] |
| 20% | s_dr | 1.3800 [1.1220, 1.5186] | 6.5628 [6.3351, 6.8440] | 6.7983 [6.6352, 6.9918] | 6.4956 [6.1545, 6.6623] |
| 30% | ipw | 3.0875 [2.7240, 3.3458] | 9.8608 [9.3529, 10.1898] | 10.0298 [9.6856, 10.5185] | 9.9489 [9.5892, 10.3053] |
| 30% | dr | 2.1932 [2.0259, 2.3936] | 6.9236 [6.5045, 7.2884] | 6.9705 [6.6755, 7.2106] | 6.7905 [6.4008, 6.9540] |
| 30% | s_dr | 2.1705 [2.0074, 2.3701] | 6.8433 [6.4355, 7.1950] | 6.8920 [6.6184, 7.1179] | 6.7232 [6.3478, 6.8649] |
| 40% | ipw | 4.0200 [3.5827, 4.4012] | 9.9935 [9.5803, 10.2852] | 10.0953 [9.6222, 10.4651] | 9.9927 [9.6153, 10.3199] |
| 40% | dr | 2.9059 [2.6785, 3.0989] | 7.0739 [6.7576, 7.4373] | 7.0441 [6.6745, 7.3317] | 6.8511 [6.4372, 7.1225] |
| 40% | s_dr | 2.8712 [2.6479, 3.0644] | 6.9938 [6.6902, 7.3431] | 6.9666 [6.6191, 7.2467] | 6.7841 [6.3849, 7.0345] |
| 50% | ipw | 5.1512 [4.7550, 5.5180] | 10.0442 [9.6539, 10.2902] | 10.1148 [9.7700, 10.5096] | 10.0390 [9.6707, 10.3492] |
| 50% | dr | 3.7276 [3.5711, 3.8671] | 7.1379 [6.8481, 7.5109] | 7.1140 [6.8574, 7.3529] | 6.8901 [6.5011, 7.1631] |
| 50% | s_dr | 3.6864 [3.5349, 3.8169] | 7.0582 [6.7809, 7.4174] | 7.0365 [6.8021, 7.2658] | 6.8232 [6.4486, 7.0741] |

## Stability and comparisons

- zero_value: abstention 5/5; assessment reach mean 0.000000%, range [0.000000%, 0.000000%]; provisional model counts {'none': 5}.
- below_first_reach: abstention 5/5; assessment reach mean 0.000000%, range [0.000000%, 0.000000%]; provisional model counts {'none': 5}.
- low_value: abstention 5/5; assessment reach mean 0.000000%, range [0.000000%, 0.000000%]; provisional model counts {'none': 5}.
- illustrative_reference: abstention 5/5; assessment reach mean 0.000000%, range [0.000000%, 0.000000%]; provisional model counts {'none': 5}.
- higher_value: abstention 5/5; assessment reach mean 0.000000%, range [0.000000%, 0.000000%]; provisional model counts {'none': 5}.
- limited_budget: abstention 5/5; assessment reach mean 0.000000%, range [0.000000%, 0.000000%]; provisional model counts {'none': 5}.
- zero_cost: abstention 5/5; assessment reach mean 0.000000%, range [0.000000%, 0.000000%]; provisional model counts {'none': 5}.
- all_targeting_feasible: abstention 5/5; assessment reach mean 0.000000%, range [0.000000%, 0.000000%]; provisional model counts {'none': 5}.

Same-cap policies can spend different amounts. All-targeting appears only when feasible; it is not reach-matched.
The JSON economics report contains all feasible fixed-reach gains, hypothetical net values and intervals for all 15 evaluator/propensity combinations.
Matched-spending contrasts use exactly the engine's actual count; zero-spending recommendations make all matched comparators no targeting.
No ranking AUUC/Qini definition changed; those historical areas are not a spending objective.

## Resources and preservation

All 201 protected file/tree entries match before/after.
Split evaluation elapsed seconds: [7.91, 7.27, 7.48, 7.15, 8.45]; total 38.27 (excludes protection/gate/publication overhead).
Maximum process RSS: 0.583 GiB.
Memory cgroup snapshots, disk availability and individual numerical diagnostics are in phase_8_metrics.json.
Cloud-local models/data/memberships/MLflow are not guaranteed to persist across new tasks. Preserve matching artifacts; deliberately restore and verify missing prerequisites.

Existing calibration and exact-vector overlap diagnostics remain in phase_7_comparison.md; vector matches are not customer identities or validated clusters.
