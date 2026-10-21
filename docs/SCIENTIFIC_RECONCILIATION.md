# Scientific narrative reconciliation — current local review

Status: **BLOCKED pending owner review**, then the separate deployment gates.
This correction explains existing evidence only. It does not change the frozen
analysis, select a policy, generate a replacement estimate or reopen outcomes.
Phase 10 PR #15 is merged at `7a038ffe4e0902b37aa287c125fd6ae87941cbf5`.
The local Streamlit and React apps exist; public website deployment is not claimed.

## Exact original development abstention

Source: [original Phase 8 metrics](../reports/phase_8_metrics.json),
[decision report](../reports/phase_8_decisions.md),
[sensitivity report](../reports/phase_8_sensitivity.md), and
[unchanged decision implementation](../src/marketing_uplift/decision_engine.py).

The five split seeds were 104729, 130363, 155921, 181081 and 206369. Each used
all eight original economic configurations. All 40 recommendations were no targeting.

| Original configuration | Across five splits | First blocking condition |
|---|---:|---|
| zero_value | 5 | Explicit zero-value gate |
| below_first_reach | 5 | No feasible initial reach |
| low_value | 5 | First tranche: random had negative net value across all scenarios; other rankings assumption-sensitive |
| illustrative_reference | 5 | First-tranche assumption sensitivity |
| higher_value | 5 | First-tranche assumption sensitivity |
| limited_budget | 5 | First-tranche assumption sensitivity |
| zero_cost | 5 | First-tranche assumption sensitivity |
| all_targeting_feasible | 5 | First-tranche assumption sensitivity |

The latter six configurations across five splits generated **120 candidate ranking
records** (30 × four rankings). Every accepted prefix was zero, every recorded stop
was at the first 10% tranche, and every binding scenario was **IPW, assumed e=.90**.
All corresponding IPW point gains were negative. The first tranches contained at
least 638 control visits, above the threshold of 30; event support did not bind.

The rule required each successive tranche to retain positive worst-scenario
simultaneous lower net value, within budget/support constraints. It stopped at
the first failure. The decision family was **300 one-sided marginal coordinates**,
not the final **765 two-sided diagnostic contrasts**. Increasing visit value does
not repair a negative gain bound, including in the zero-cost scenario.

The e=.90 scenario was binding and sufficient to block these candidates. This does
not show that removing it would produce targeting; no counterfactual engine or new
selection was run. The recommendation is the retained result of a prespecified
stress-test objective, not universal business guidance, advertising ineffectiveness
or proof of globally optimal abstention.

## IPW and DR use the same complete denominator

Source: [gain basis and weights](../src/marketing_uplift/decision_metrics.py),
[final moments and contrast construction](../src/marketing_uplift/final_metrics.py),
[independent row reference](../src/marketing_uplift/final_verification.py), and
[approved public snapshot](../reports/portfolio/aggregate_results.json).

For all targeting, mean denotes the average over **all 2,096,939 eligible final
holdout records**; T is assignment, Y is visits, and m0/m1 are frozen shared
nuisance predictions. Gains are relative to no targeting:

```
G_IPW = mean[TY/e − (1−T)Y/(1−e)]
G_DR  = mean[m1−m0 + T(Y−m1)/e − (1−T)(Y−m0)/(1−e)]
G_DR − G_IPW = mean[(e−T)(m1/e + m0/(1−e))]
```

At assumed e=.85, saved gains per 1,000 eligible are **10.341310853 IPW** and
**7.419188765 shared DR**. Their difference, **−2.922122088**, is the augmentation
term above (values displayed to nine decimal places). Neither arm normalization
nor a different evaluation population explains this difference. Equality is not
required in a realized sample; matching the overall assignment fraction to e does
not force assignment to be unassociated with predicted risk.

The six shared nuisance models fit development-only arm records outside each of
three deterministic nuisance folds. Each arm's three predictions are averaged;
every policy uses the same evaluator. Final-S nuisance sensitivity is separate.
Scoring stores m0,m1,s0,s1 in that order, and the sealed evaluator verifies IDs and
uses the same order. Existing independent synthetic tests check explicit formulas
and streaming moments. The audit found no demonstrated estimator/alignment bug;
this is not proof that every nuisance or identification assumption is correct.

Factual calibration cannot establish counterfactual outcome-model correctness.
The published evidence does not isolate model misspecification, release selection,
hidden assignment probabilities or finite-sample variation as the cause. No missing
row-level diagnostic is invented. DR's relative stability does not establish causal
identification or resolve non-uniform privacy subsampling and pooled experiments.

## What the propensity sweep means

For fixed policy membership π and observed records, let A=mean[πTY] and
B=mean[π(1−T)Y]. Both are nonnegative:

```
G_IPW(e) = A/e − B/(1−e)
dG_IPW/de = −A/e² − B/(1−e)² ≤ 0
```

Increasing assumed e mechanically decreases this unnormalized estimate, strictly
when A or B is positive. The five saved scenarios are assumptions, not a calibrated
probability distribution or observed variation in treatment effects.

A normalized/Hájek all-targeting contrast instead divides each weighted outcome
total by its weighted arm count:

```
(sum TY/e)/(sum T/e) − (sum (1−T)Y/(1−e))/(sum (1−T)/(1−e))
```

Constant e cancels within each arm. Partial-policy normalization needs its own
explicit denominator and estimand. Different scaling does not repair identification,
privacy selection or hidden experiment assignment. No normalized replacement
holdout estimate was generated or retrospectively substituted.

## Higher-reach insight — saved shared DR, assumed e=.85, primary IID model

Units: visits per 1,000 eligible. Bounds are the existing **765-family simultaneous**
intervals. Values below are rounded presentations of saved contrasts, not new estimates.

| Reach | Contrast | Estimate | Saved simultaneous interval |
|---|---|---:|---|
| 30% | Response minus S | 0.078378 | [−0.252683, 0.409440] |
| 30% | Response minus T | 0.277541 | [−0.201221, 0.756302] |
| 30% | S minus T | 0.199162 | [−0.251529, 0.649853] |
| 40% | Response minus S | 0.149547 | [−0.120209, 0.419302] |
| 40% | Response minus T | 0.313480 | [−0.153763, 0.780723] |
| 40% | S minus T | 0.163934 | [−0.284883, 0.612751] |
| 50% | Response minus S | 0.136665 | [−0.108547, 0.381876] |
| 50% | Response minus T | 0.317154 | [−0.137752, 0.772061] |
| 50% | S minus T | 0.180490 | [−0.259807, 0.620787] |

Response has the numerically larger points at these reaches, but all nine intervals
include zero. This establishes neither superiority nor equivalence and selects no
new preferred strategy. Nominal intervals condition on fitted models and fixed
policies; no exact randomization or unconditional causal coverage is claimed.

## Current status versus historical evidence

The case study now distinguishes implemented local dashboards from unperformed
public deployment. Historical Phase 10 review documents carry current-status
clarifications acknowledging PR #15; historical sealed reports, checkboxes inside
immutable evidence, aggregate `local-review-only` metadata and original locks are
unchanged. Local review/private transfer never authorizes public deployment.

The descriptive rates remain assignment-arm observations under pooled experiments,
unknown assignment probabilities and privacy subsampling. They are not verified
advertiser-wide causal ITT or actual-exposure effects. MIT software and Criteo-derived
CC BY-NC-SA 4.0 assets remain distinct. No financial or deployment claims are added.

## Before → after

- Generic “assumption sensitivity” → exact 5 + 5 + 30 breakdown, all 120 binding
  first-tranche records and the specific e=.90 IPW rule.
- IPW/DR stability comparison without reconciliation → same denominator,
  exact saved values, augmentation identity and unresolved identification limits.
- Propensity sensitivity without mechanical explanation → fixed-policy derivative
  and a conceptual Hájek distinction with no replacement analysis.
- Higher-reach points alone → nine saved paired simultaneous bounds, no superiority
  or equivalence claim.
- Phase 10's historical nonimplementation/permission language → merged PR #15,
  implemented local dashboards and a separate current owner-review/launch gate.
