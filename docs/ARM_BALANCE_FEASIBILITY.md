# Development arm-balance diagnostic — feasibility only

**Feasible with saved development predictions; not executed.** No arm means,
imbalance values, decomposition results or new outcomes were calculated. No final
holdout row-level features, predictions or outcomes were opened.

## Inputs and population

Use each of the five original **outer validation** memberships, optionally retaining
separate original selection/assessment roles. These are development records whose
models/nuisances were trained only on the corresponding outer training split.
Never substitute final development-refit models or final-holdout predictions.

The read-only inventory verified all five `dr-m0.npy` and `dr-m1.npy` arrays and
fit manifests against Phase 7 hashes; it also verified the Phase 8 role files and
validation membership hashes. S-nuisance arrays are available for a separately
labeled sensitivity, not a favorable evaluator selected afterward.

Required inputs: sorted development row IDs, aligned treatment T, shared m0/m1,
original role labels, sample size and fixed e scenarios. **Y is not needed for the
augmentation identity.** Treatment labels are not separately cached as verified
outer-validation arrays. A future approved diagnostic should obtain only
`row_id,treatment` from Parquet with an explicit join to validated development IDs;
it should not reuse `source_outcomes()`, which unnecessarily requests visit too.
Feature vectors and model loading/scoring are also unnecessary.

Before any future query, verify registry/ID/model/prediction hashes and exact
positional alignment. Process batches of 65,536, retain both assignment arms and
fail on missing/misaligned IDs, absent arms or invalid probabilities. Do not modify
memberships, records, saved arrays or the existing query/evaluation implementations.

## Proposed descriptive summaries and exact algebra

For a fixed development population, p=mean(T), and a in {0,1}:

```
mu[a,1] = sum(T*m_a)/sum(T)
mu[a,0] = sum((1-T)*m_a)/sum(1-T)
d[a] = mu[a,1] - mu[a,0]
bar_m[a] = p*mu[a,1] + (1-p)*mu[a,0]
```

Report both m0 arm means (predicted untreated/baseline risk), both m1 arm means
(predicted treated risk), d0/d1, counts and prediction provenance. Differences are
model-predicted risk differences, not observed individual effects or proof of
causal imbalance. Do not assume p equals the reference e=.85 in each role.

The all-targeting augmentation for the same population satisfies:

```
D(e) = mean[(e-T)*(m1/e + m0/(1-e))]
     = (e-p)*(bar_m1/e + bar_m0/(1-e))
       - p*(1-p)*(d1/e + d0/(1-e))
```

The first component is the overall assignment-share mismatch term; the second is
the empirical assignment/predicted-risk association term (covariance using divisor N).
This is an algebraic decomposition, not a causal decomposition. Check its numerical
identity against the direct prediction/T expression and the original saved
all-targeting DR-minus-IPW development aggregates for exactly the same role. No
new outcome access is needed for that consistency check. Any optional partial-policy
version must keep pi inside the expression and cannot reuse this whole-population
arm-mean formula without deriving the selection-weighted terms.

Start with descriptive tables and residual identity error only, under a separately
approved diagnostic protocol. No new confidence interval is promised by this plan.
If requested later, uncertainty needs its own fixed-model/dependence assumptions
and multiplicity definition. The overlapping outer splits are not independent
replications, and repeated vectors are not verified customer clusters.

## What is and is not identifiable

Existing factual calibration bins do not supply the missing cross-arm means for
both nuisance functions; saved DR/IPW totals do not identify their unique arm-wise
decomposition. New development-only aggregation is required, even though scoring
and training are unnecessary. The available arrays make this practical in bounded
memory, but byte-identity verification alone does not validate model correctness.

A future nonzero d0/d1 could reflect finite samples, pooled experiments, release
selection, model representation or misspecification. This diagnostic cannot identify
which mechanism caused it, establish hidden experiment effects, prove shared DR
causally correct, determine the causal bias direction of the descriptive rate gap,
or validate transport to another advertiser. No such conclusion is reported here.

Any approved output must be marked **post-hoc development diagnostic**, separate
from the original frozen result and never used to change the final recommendation.
