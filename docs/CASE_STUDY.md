# When a targeting engine recommends no targeting

## The decision

Who should receive an advertising assignment when the budget is limited and the
incremental benefit is uncertain? Predicting who will visit is useful, but it can
prioritize people who would have visited without an advertisement. This project
separates that prediction task from an assignment-level policy decision.

The result is an offline, reproducible decision study on Criteo's corrected v2.1
benchmark. It includes data contracts, response/uplift models, a conservative
budget simulator and a one-time held-out evaluation. Its final recommendation is
**the no-targeting policy frozen before final outcomes**. The recommendation is
an evidence-governance decision under the declared development rule, not a claim
that advertising never works or that zero spending is causally optimal.

## A trustworthy foundation

The official archive contains 13,979,592 records and is pinned by repository
revision, exact byte size and SHA-256. Strict validation checks all 16 columns,
binary values, finite numeric features and the full row count. The pipeline does
not remove inconvenient rows, deduplicate repeated vectors or silently impute them.

DuckDB and Parquet support bounded-memory scans. Source-row ordinals preserve
CSV-to-Parquet alignment and later reconstruction. They are not customer IDs.
The development audit found no missing/nonfinite values and documented that
18.10% of development observations shared a full feature vector with another row.
Repeated vectors alone do not establish that the rows describe the same person.

A joint treatment × visit-stratified split sealed 15% before exploratory analysis.
The remaining 11,882,653 records supplied five frozen 80/20 development re-splits.
Those overlapping splits reveal stability, not independent replication. The
final 2,096,939 records were excluded from model fitting, tuning and policy selection.

## Models that answer different questions

| Strategy | Score | Why include it? |
|---|---|---|
| Random targeting | Frozen random priority | Equal-reach baseline without learned ranking |
| Treated response | Predicted visit probability among assigned records | Conventional predictive targeting |
| S-learner | One outcome model, evaluated with intervention 1 minus 0 | Simple heterogeneous-assignment contrast |
| T-learner | Separate treatment/control outcome predictions, subtracted | More flexible arm-specific response surfaces |

All predictive user inputs are exactly f0–f11. Exposure and outcomes are excluded;
treatment is supplied separately only as the S-learner intervention indicator.
Neither a row identifier nor a post-assignment exposure flag becomes a predictor.

LightGBM handles concentrated numeric features without a fitted scaling pipeline.
The frozen recipe uses 200 rounds, learning rate 0.05, 31 leaves and two threads.
These small deterministic tabular models fit the available Cloud resources; adding
complex estimators would not solve the benchmark's identification limitations.
MLflow records configurations and private model/provenance artifacts.

Separate training-only nuisance folds supply the shared DR evaluator for every
policy. The final diagnostic models were predetermined development-only refits,
not candidates chosen after holdout performance. Final-S nuisance predictions form
a separately declared sensitivity, not a favorable evaluator selected afterward.

## From a score to a spending decision

The Phase 8 simulator evaluates predeclared 10%, 20%, 30%, 40% and 50% reaches
under eight hypothetical economic scenarios. For visit value v, assignment cost c
and N eligible records, scenario net value is `v × N × estimated gain − c × targeted count`.
No actual costs, revenue or realized ROI are available in Criteo.

The rule can leave the budget unspent. It requires support and a sufficiently
positive conservative marginal net value across the predeclared evaluation
assumptions; it stops at the first failed tranche. All 40 development scenario/split
combinations recommended abstention. Reasons included sensitivity to assumptions,
negative estimated net benefit, zero visit value and a budget below the first reach.

That recommendation became the locked primary policy. Random, response, S and T
policies remained secondary diagnostic comparisons. Final evaluation could describe
those strategies but could not replace the primary policy with a better-looking result.

## What the one-time evaluation measured

![Observed rates](../reports/portfolio/figures/descriptive_rates.png)

The observed treatment visit rate was 4.8543%, versus 3.8202% in control: a
descriptive 1.0341 percentage-point difference. It is an assignment contrast in a
released sample, not a verified advertiser-wide causal effect or exposure effect.

![Reach diagnostics](../reports/portfolio/figures/policy_reach.png)

At reference **assumed** e=0.85, the shared-DR estimate for 10% S-learner targeting
was 6.002 estimated incremental visits per 1,000 eligible records; its nominal
simultaneous 95% interval was [5.279, 6.725]. At 50%, the four fixed rankings gave
random 3.805, response 7.241, S 7.104 and T 6.924. These are released-benchmark
scenario functionals under the stated evaluation model, not verified deployment gains.

The all-targeting DR anchor was 7.419 [6.376, 8.462] using simultaneous bounds.
All-targeting has a larger assignment budget than the fixed-reach policies.
No targeting has exactly zero incremental gain relative to itself; it does not
imply zero website visits without advertising.

![Paired comparisons](../reports/portfolio/figures/s_vs_t.png)

All ten simultaneous S-versus-T comparisons at e=0.85 (IPW/shared DR × five reaches)
included zero. This result comes from paired differences, not from comparing
overlapping model-level intervals. A positive policy-versus-none diagnostic and
an unresolved S-versus-T comparison can both be true.

## The uncertainty that matters

![Sensitivity](../reports/portfolio/figures/propensity_sensitivity.png)

Unknown original experiment-specific assignment probabilities are a central
limitation. Under assumed e from 0.80 to 0.90, the all-targeting IPW estimate changes
from +22.926 to −11.456 visits per 1,000 eligible. Shared DR stays between 7.382
and 7.486, with a separately reported final-S nuisance sensitivity. This relative
stability is useful evidence about these estimators, not proof that either nuisance
model is correct or that hidden selection bias has disappeared.

The completed analysis used 2,000 paired Gaussian-multiplier draws, preserving
correlation across all policies and propensity/evaluator scenarios. Its two-sided
simultaneous family contains 765 contrasts: 15 evaluator/propensity scenarios ×
(20 policy-versus-none gains + 30 equal-reach model differences + one all-targeting gain).
Pointwise intervals answer a different question and are reported separately.

The intervals are nominal IID working-model intervals conditional on fitted models,
nuisance predictions and fixed rankings. They omit training uncertainty and cannot
correct unknown dependence or the released sample's privacy selection. The
mandatory stratified sensitivity fixes observed treatment × visit composition; it
must not replace the primary method because it gives narrower intervals. No coverage
across both uncertainty methods is claimed.

## Engineering an honest final boundary

The final evaluation required signed owner approval bound to code, model, data and
policy identities. Feature-only scoring preceded outcome access. Predictions and
memberships were hashed, encrypted and independently restored by the owner before
signed continuation. A fixed receipt and append-only journal recorded the campaign;
`outcome_access_started` was durably read back before constructing the outcome reader.

This reduced accidental replay and created auditable evidence. It did not turn GitHub
into administrator-proof immutable storage or establish scientific identification.
The one final evaluation completed; no second outcome access is permitted. Phase 10
reads only its saved aggregate estimates and intervals.

## What this project demonstrates

The strongest deliverable is a connected, tested analytical workflow whose claims
match its evidence. The system preserves rows and provenance, compares simple
models fairly, treats assignment assumptions explicitly, and carries a no-action
option through final reporting instead of manufacturing a winner.

The final recommendation remains unchanged despite positive secondary diagnostics.
Testing that diagnostic family does not solve optimal-policy selection, validate
hypothetical prices or establish commercial value. A future deployment decision
would need known experimental assignment/sampling mechanisms, real economics,
dependence information and fresh prospective evaluation.

This finalization includes static portfolio materials and reproducible figures.
The roadmap's Streamlit dashboard, deployment and recorded walkthrough are **not
implemented or claimed** in the approved scope. The [model card](MODEL_CARD.md)
and [review checklist](PORTFOLIO_REVIEW.md) document appropriate reuse and publication gates.
