# Frozen Phase 6 protocol

Frozen before performance examination; settings in configs/baselines.toml are shared
by all five existing development splits. No tuning, early stopping, feature selection,
resampling, class weights or learned transformations. LightGBM binary GBDT uses 200
rounds, learning rate .05, 31 leaves, minimum 1,000 records per leaf, 63 bins,
200,000 training-only bin samples, two threads, deterministic column-wise training,
256 MB histogram pool, full feature/row fractions. All model seeds equal split seed.
Treated response trains on assigned-treatment training rows only. The S-learner
uses f0–f11 plus an internal separately supplied intervention indicator; predictions
are m1-m0. User feature exports always contain exactly f0–f11 in order, float64.

Ranking: descending score; ties use PCG64 uniform priorities (split seed+1,000,000)
over sorted validation IDs, then source ID as final tie break. Random targeting uses
the same priorities. Top ceil(q*n) records at q=.1,.2,.3,.4,.5; policies are nested.
None/all anchors have exactly zero/n selected. No outcome enters ranking.

For each constant propensity scenario e, W=T*Y/e-(1-T)*Y/(1-e).
V(pi)=mean(pi*T*Y/e+(1-pi)*(1-T)*Y/(1-e)); gain over none=mean(pi*W).
Policy differences are paired mean((piA-piB)*W). Values and gains are also
reported per 1,000 eligible validation records, not per targeted record. e=.85 is a
reference assumption, not a verified assignment probability; .80,.825,.875,.90
are separate sensitivity scenarios. No clipping of estimates or negative gains.
Within-selected-arm visit-rate differences are descriptive only.

Full-prefix grid q_j=j/n, j=0..n. G(q_j)=sum(top j W)/n. ipw_auuc is the exact
trapezoidal integral of this piecewise-linear curve, equivalently
sum_{j=1}^n W_(j)*(n-j+.5)/n^2. ipw_qini_area=ipw_auuc-G(1)/2 is unnormalized
area above the random diagonal. These are explicitly defined IPW conventions,
not normalized scikit-uplift metrics. Fixed-reach tables do not approximate these areas.
Predictive diagnostics: binary log loss, Brier, ROC AUC and average precision;
response model evaluated on treated validation rows; S factual probabilities on all.

Bootstrap: 2,000 ordinary IID paired row resamples, PCG64 splitseed+2,000,000.
Conditional on trained models and fixed original policy memberships: no refitting,
reranking or fixed-reach enforcement inside replicates. Compress joint memberships
in the six nested reach bins for each of three rankings, crossed with T,Y (at most
864 cells). Multinomial(n, cell proportions) counts reproduce ordinary row bootstrap
for these fixed-policy statistics exactly in distribution. All policies and scenarios
share resampled counts. Pointwise intervals use percentile .025/.975, NumPy linear
quantiles. Primary simultaneous family is five S-minus-response gains within each
split at e=.85: bootstrap maximum absolute standardized centered deviation, divided
by bootstrap sample SD (ddof=1); 95th percentile gives symmetric max-t bands.
Zero-SD coordinates have zero width. These bands do not adjust across splits or
sensitivity scenarios. Ranking-area uncertainty is not estimated.

These are nominal IID working-model intervals, not exact randomization inference.
Outcome-stratified development construction, repeated feature vectors/unknown
customer dependence, selected privacy subsampling, pooled unknown experiments and
unknown assignment mechanisms limit interpretation. Causal policy values require
consistency, no interference, exchangeability, positivity and the correct propensity
in the released population. Constant scenarios cannot establish those assumptions.
Five overlapping splits describe stability, not independent replication: report mean,
range and per-split estimates; no standard-error-of-five confidence interval.
No business ROI, treatment-on-treated or final-policy selection is supported.

Execution: synthetic gates first, then split 104729 with alignment/resource checks,
then four unchanged recipes. Batch extraction/prediction, sequential models/splits,
private memory-mapped arrays, bounded DuckDB. No holdout outcome query, no source or
membership rewrites. Resume only matching protocol/source/membership evidence.
MLflow records settings, versions, Git/code and dataset provenance, metrics and models.
