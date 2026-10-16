# Frozen Phase 7 protocol

This additive extension preserves Phase 6 and the dependency lockfile. Only frozen
development training and validation IDs are queried; no holdout outcomes are used.
Model recipes remain configs/baselines.toml: 200 binary LightGBM rounds, learning
rate .05, 31 leaves, minimum leaf size 1000, max_bin63, train-only bin samples
200000, full row/feature fractions, deterministic column-wise two-thread training.
No tuning, early stopping, weighting, imputation, calibration fitting or deduplication.
User predictors are exactly f0–f11. Assignment only selects T-learner arm records.
Reuse the verified Phase 6 response model/predictions for T's treatment arm; fit a
control model on all outer-training controls using the outer split seed.

Nuisance protocol: PCG64(outerseed+3000000) permutes sorted outer-training positions;
assign folds by round-robin modulo3 through that permutation. Persist uint8 labels
and their hashes before fitting. Fold k's outcome regressions use only outer-training
records outside k, separately by arm; model seeds outerseed+4000000+10*k+arm.
Produce OOF predictions only for each held inner fold's factual arm. Average each
arm's three models' outer-validation probabilities to define the common evaluator.
No outer-validation record enters any fit, preprocessing, fold definition or tuning.
OOF diagnostics are not additional policy evaluation records. As a nuisance sensitivity
only, use saved Phase 6 S m0/m1 for all policies; no evaluator is selected by results.
Model/prediction artifact hashes are published in a fit manifest before evaluation.

Policies: reuse Phase 6 random priorities PCG64(outerseed+1000000), descending score,
priority and then ascending source-ID tie breaks. Score T by reused response minus
new control probability. Top ceil(q*n) at .1,.2,.3,.4,.5, nested; none/all separate.
All policy rows are in sorted frozen validation-ID order. No IDs enter predictors.
IPW full-prefix AUUC and unnormalized Qini conventions remain unchanged, including
n+1 integration points and negative values. DR areas are not introduced.

Target V_causal(pi)=E[Y(pi(X))] in released development population. For assumed e,
IPW H0=(1-T)Y/(1-e), Z=TY/e-(1-T)Y/(1-e), Hpi=H0+pi*Z.
DR H0=m0+(1-T)(Y-m0)/(1-e),
Z=m1-m0+T(Y-m1)/e-(1-T)(Y-m0)/(1-e), Hpi=H0+pi*Z.
Values=mean Hpi; gain=mean pi*Z; paired difference=mean (piA-piB)*Z.
Per1000 units refer to eligible validation rows, not targeted rows. Constant e=.85
is a reference assumption, and .80,.825,.875,.90 separate illustrative scenarios.
None is a verified assignment probability or a bound on selection bias.
Double robustness requires identification (consistency, no interference, positivity,
conditional exchangeability) and either correct propensity or both correct outcome
regressions with suitable estimation conditions. It does not undo privacy selection,
hidden experiments, dependence or outcome-stratified development construction.
AIPW estimates can exceed probability bounds; never clip estimates or negative gains.

Uncertainty is conditional on fitted policies/nuisances, original rankings and fixed
membership thresholds: no refitting or reranking. Define a vector h_i of both IPW
and primary DR values across all five scenarios, none/all and 20 fixed policies.
Compute mean and sample covariance S=sum((h_i-mean)(h_i-mean)')/(n-1).
Covariance of means is S/n. For bounded memory, aggregate counts, first and second
moments of v=(TY,(1-T)Y,m1-m0,T(Y-m1),(1-T)(Y-m0),m0) within joint six-bin
memberships of four rankings. Within each cell h_i=B_cell*v_i, so these moments
recover the full mean/covariance. Combine centered within/between-cell moments.
This is a continuous moment calculation, NOT Phase 6's multinomial bootstrap.

Draw 2000 shared centered Gaussian vectors delta~N(0,S/n), PCG64 outerseed+5000000,
using symmetric eigenfactorization. This equals the Gaussian row-multiplier law
sum_i xi_i*(h_i-mean)/sqrt(n*(n-1)), xi_i iid standard Normal, in distribution;
it is NOT an exact ordinary row bootstrap. Shared vectors preserve all pairing and
cross-scenario correlation. Pointwise intervals: point plus linear .025/.975
quantiles of delta. Apply linear contrasts to the same draws for gains/comparisons.
Primary simultaneous family: T-minus-S at five reaches under IPW and primary DR
at e=.85 (ten coordinates within each split). Scale centered contrasts by analytic
SE from S/n; critical=linear .95 quantile of max absolute standardized deviation;
bands=point +/- critical*SE. No correction across splits or other scenarios/evaluators.
Zero-variance coordinates have zero width. Treat variance <=1e-12 times the largest
marginal covariance diagonal as numerical zero; negative eigenvalues below
-1e-10 times that scale stop execution, smaller roundoff negatives are zeroed and
recorded. Singular covariance is expected, not a reason to add artificial noise.
Secondary S-nuisance DR sensitivity reports point estimates without confidence bands.
No uncertainty for ranking areas. Nominal IID working-model coverage only; unknown
clusters, selection, stratification, refitting and estimated cutoffs are not covered.

Diagnostics: support (n and visits by arm) in cumulative and disjoint reach bands;
control visits<30 warning, absent-arm differences undefined. Fixed calibration edges
in phase7.toml, log loss/Brier/ROC AUC/AP by factual arm, plus OOF arm diagnostics.
Repeated-vector overlap uses exact f0–f11 grouping, never customer identity or
clustering claims. No deletion, new outer splits or feature-driven adjustments.

Sequence: synthetic tests, first real split, saved-model/alignment/fold/formula and
resource/protection gate, then remaining four unchanged recipes. Sequential fits,
bounded DuckDB, memmaps/batched prediction and streaming moments. Stop on resource
or contract failure; no silent smaller data/recipe substitutions. Resume only verified
provenance/artifact hashes. Store new private outputs under artifacts/phase7, use a
new local MLflow experiment; old runs are read-only. Report five overlapping splits
individually and as descriptive mean/range; never independent-replication CIs.
No final winner, cost/reach optimization, holdout evaluation or later-phase engine.
