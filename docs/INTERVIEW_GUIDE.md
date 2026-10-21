# Interview guide

## 30-second pitch

“I built an offline marketing decision engine on 13.98 million Criteo advertising
records. I compared visit prediction with S- and T-learner uplift targeting,
using frozen development splits and a one-time holdout. The distinctive part is
the decision rule: it can recommend spending nothing when evidence is sensitive
to assumptions. I preserved that recommendation even though secondary holdout
diagnostics were positive, rather than selecting a winner after the test.”

## Two-minute walkthrough

“The business problem is deciding whom to assign advertising under a limited
budget. Predicting who visits does not identify who visits because of advertising:
high-propensity users may visit anyway.

I started with the corrected Criteo v2.1 release. I pinned and verified the archive,
validated all 13,979,592 rows, and converted it to Parquet with deterministic
source-row identifiers. I kept every observation, including repeated feature vectors.
I sealed 15% before exploratory work and used five frozen development re-splits.

I compared random targeting, a treated-response LightGBM model, an S-learner and
a T-learner. Exactly f0–f11 were predictive user features. Exposure was excluded,
and the S-learner received treatment separately. I tracked configurations and
artifacts in MLflow and evaluated equal reaches from 10% to 50%.

The important limitation is that the released data hides experiment-specific
assignment probabilities and uses non-uniform privacy subsampling. So I reported
IPW and DR under explicit propensity assumptions, not verified causal gains.
The development budget engine abstained in all 40 scenario/split combinations,
and I locked no targeting as the primary recommendation.

The one-time final evaluation used 2,096,939 records and a predeclared family of
765 comparisons. At assumed e=0.85, the DR all-targeting anchor was 7.419 estimated
incremental visits per 1,000 eligible, with simultaneous interval 6.376 to 8.462.
S versus T was unresolved within the simultaneous family. Those diagnostics did
not change the recommendation. The achievement is a reproducible decision analysis
that makes its uncertainty and limits visible, not a claim of advertising ROI.”

## Technical discussion

**Prediction versus uplift.** Response estimates a visit probability. An S-learner
contrasts the same model at intervention 1 and 0. A T-learner contrasts separate
arm response models. No one has both potential outcomes observed; a model score
is not an observed individual causal label. More flexible arm models can increase
variance, especially in the smaller control arm.

**Estimand and formulas.** For fixed policy π(X), target `V(π)=E[Y(π(X))]` and
gain `V(π)−V(0)`. Under assumed constant e:

```text
IPW H0 = (1−T)Y / (1−e)
IPW Z  = TY/e − (1−T)Y/(1−e)
DR  H0 = m0 + (1−T)(Y−m0)/(1−e)
DR  Z  = m1−m0 + T(Y−m1)/e − (1−T)(Y−m0)/(1−e)
value  = mean(H0 + πZ)
gain   = mean(πZ)
paired difference = mean((πA−πB)Z)
```

These observed-data functionals have a causal interpretation only under the
required identification assumptions. e=0.85 is a reference scenario, never an
individual assignment probability verified from the observed treatment fraction.
Shared three-fold training-only nuisances evaluate all policies fairly; the final-S
nuisance alternative is reported separately. Nothing is fitted on holdout outcomes.

**Uncertainty.** Streaming covariance recovers the joint contribution covariance
without storing a huge row-by-comparison matrix. Two thousand correlated Gaussian
draws preserve pairing across scenarios and policies. The simultaneous critical
value is the 95th percentile of the maximum absolute standardized draw over all
765 contrasts; pointwise intervals use separate marginal quantiles. This is not
an ordinary bootstrap or exact randomization inference. Training uncertainty,
unknown clustering and outcome-stratification limitations remain.

**Efficiency.** DuckDB/Parquet avoid loading a full uncompressed CSV into a Python
dataframe. The model recipe uses two threads and bounded histogram resources.
Source identities and membership hashes catch alignment errors. Using a complex
distributed stack would not resolve the scientific limitations of this benchmark.

**Reproducibility.** Distinguish code reproduction, artifact reconstruction and a
scientifically fresh evaluation. The presentation rerenders saved aggregate values;
it does not rerun the one-time analysis. Hashes establish byte identity, not causal
identification, durable storage by themselves or administrator-proof security.

## Anticipated interviewer questions

1. **Why abstain when the holdout estimates are positive?**
   The primary recommendation was frozen from a stricter development decision rule
   that incorporated sensitivity, marginal uncertainty, support and hypothetical
   economics. Secondary diagnostics answer narrower assumption-dependent questions.
   Replacing the recommendation after seeing them would violate the policy lock.

2. **Does a zero primary effect prove the ads did nothing?**
   No. A policy compared with itself has zero incremental gain by identity. People
   can visit without targeting. Advertising effectiveness and policy optimality
   are different claims requiring evidence beyond that identity.

3. **Why not use the observed treatment fraction as the true propensity?**
   A pooled fraction does not recover hidden experiment-specific assignment
   probabilities or the privacy sampling mechanism. I used five explicitly assumed
   scenarios; sensitivity is not a calibrated probability distribution over e.

4. **Does DR fix an incorrect propensity assumption?**
   Under identification, DR is consistent if the propensity or required outcome
   regressions are correct. It does not automatically repair sample selection,
   hidden confounding, interference or dependence. Stable estimates do not certify
   correct nuisance functions.

5. **Can you say S and T are equivalent?**
   No. Their paired simultaneous intervals include zero, so this family does not
   detect a reliable difference under its working model. That is not an equivalence
   test, nor proof of identical performance across settings.

6. **Why not average the five split estimates and divide the SD by sqrt(5)?**
   The splits share observations and learned decisions. That formula would imply
   independent replications that do not exist. I report development stability and
   within-evaluation paired uncertainty with their separate qualifications.

7. **Why seal by treatment × visit if outcome composition matters for uncertainty?**
   Stratification preserves rare-event support and was predeclared. It changes the
   sampling/conditioning story. The nominal IID covariance is primary; a mandatory
   fixed-stratum sensitivity is separate and cannot be selected for narrower bounds.

8. **Why not deduplicate identical feature vectors?**
   Anonymized equal vectors do not identify the same customer. Deduplication would
   change the sample and estimand without justification. I reported overlap and
   acknowledged possible dependence instead.

9. **What would make this deployable?**
   Known assignment and release-sampling mechanisms, real costs/value, experiment
   and dependence identifiers, appropriate fairness/privacy validation and a fresh
   prospective trial of a predeclared policy. This portfolio is not that deployment.

10. **What is your strongest engineering contribution?**
    I connected strict data identity and row alignment to frozen policies, fair
    paired evaluation and an auditable one-time final boundary. The safeguards stop
    on ambiguous writes and cannot silently manufacture a fresh evaluation.

## Evidence-backed resume wording

“Built a reproducible offline marketing decision engine on 13.98M Criteo records;
compared random, response, S- and T-learner targeting using five frozen development
splits, IPW/DR sensitivity and a one-time 2.10M-record holdout; reported 765 paired
diagnostic comparisons while preserving a predeclared abstention policy.”

Do not claim a deployed dashboard, realized ROI, percentage revenue lift,
causal superiority or optimal targeting. The [case study](CASE_STUDY.md) and
[figure guide](../reports/portfolio/README.md) supply the numerical evidence.

## Explain the reviewer reconciliation

The 40 original development configurations all abstained, but the reason matters:
five zero-value gates, five infeasible initial reaches, and 120 first-tranche
candidate stops in the other 30 configurations, all bound by unnormalized IPW
at assumed e=.90. That stress-test design was frozen; it is not proof that
advertising is ineffective or zero spend universally optimal.

IPW and DR differ by a nuisance augmentation, not by cohort size. At assumed
e=.85 their all-targeting difference is −2.922122088 per 1,000 eligible. Factual
calibration cannot prove counterfactual correctness. IPW's constant-propensity
sweep mechanically changes its weights; DR stability is not causal validation.
Response has the larger shared-DR points at 30–50% reach, but all nine relevant
simultaneous pairwise intervals include zero. Do not turn that into a new winner.
