# Frozen Phase 8 decision protocol

Separately approved development experiment; no final deployment policy selection,
model training, holdout outcome access, dashboard or later phase. Preserve Phase 6/7
protocols, configurations, models, predictions, results, MLflow trees, lockfile and
all twelve frozen memberships. Phase 8 is additive. Hash dependencies and inputs;
stop on mismatches. Model predictors remain f0–f11; T is only an intervention/routing
indicator. No exposure or identifier becomes a predictor.

## Freeze and roles

configs/phase8.toml predeclares eight hypothetical economic scenarios, including
zero value, insufficient budget, low/reference/high value, limited budget, free
assignment and an all-targeting-feasible comparator. Currency units have no observed
Criteo interpretation. Cost is per assignment, not observed exposure. Value is per
incremental visit. Budget density b gives B=b*N exactly for each cohort; c and v
are unchanged between selection and assessment. B is a cap, never a spending target.
No economics, propensity, evaluator, model recipe or gate is chosen by performance.

For each existing outer-validation partition in sorted source-ID order, use
PCG64(outerseed+6000000).permutation(n); its first floor(n/2) positions are selection
(label0), all others assessment (label1). This does not use T,Y or features and does
not alter original memberships. Save all five uint8 role arrays and manifest hashes
before reading Phase 8 outcomes. Selection and assessment have no overlapping IDs;
both remain inside outer validation and outside training and final holdout.

Restrict existing random priorities and scores to each role; rank descending score,
then descending existing priority, then ascending source ID. Do not reseed priorities
on subsets. Top ceil(q*N) for q=.1,.2,.3,.4,.5. This creates explicitly new Phase 8
role-specific policies while preserving the ranking rule and historical results.
Freeze recommendations, their selected-ID hashes, selection evidence and parameters
on disk BEFORE querying assessment T,Y. Apply the chosen model and nominal reach to
assessment using scores/IDs only. If integer rounding makes that reach infeasible,
use the largest lower grid reach permitted by the already approved selection prefix;
never consult assessment outcomes or select a new model. Record this adjustment.
Assessment support problems are diagnostic only and cannot revise the recommendation.
These are reused development outcomes, NOT a fresh confirmatory validation sample.

## Estimand and decision

Use the existing IPW Z=T*Y/e-(1-T)*Y/(1-e). Shared primary DR uses
Z=m1-m0+T*(Y-m1)/e-(1-T)*(Y-m0)/(1-e). Saved S m0/m1 define the third evaluator,
shared across every policy. Scenarios e=.80,.825,.85,.875,.90 are assumptions, with
.85 a reference only. None is a verified individual propensity or calibrated bound.
Gain g(pi)=mean(pi*Z), incremental visits per eligible record relative to no targeting.
Scenario net value J=v*N*g-c*n_selected, per1000=1000*(v*g-c*n_selected/N).
Do not clip negative gains or estimates outside probability bounds.

Compute marginal gains for five disjoint rank tranches. Let L[m,j,s] be the one-sided
simultaneous lower bound for mean(1_tranche*Z). Define
R[m,j]=min_s(v*N*L[m,j,s]-c*(n_j-n_(j-1))). Stress s crosses all five propensities
and three evaluators, without probability weighting. An admissible prefix requires
all its tranches to have R>0, both arms present, >=30 selection control visits per
tranche, and exact budget/reach compliance. Stop at the FIRST failing tranche;
never skip a failure to exploit a later positive tranche. Bound equal to zero fails.
The objective A[m,j]=sum_(l<=j) R[m,l] is a conservative marginal lower-bound net
value; choose the highest positive A among admissible prefixes and no targeting
(A=0). Worst scenarios may differ by tranche: deliberately more conservative than
min_s sum_l R_s. This is a hypothetical stress objective, NOT guaranteed causal profit.
Exact objective ties: lower spending, fewer assignments, then fixed model order
random,response,s_learner,t_learner. Strict floating >0; no performance-dependent
numerical epsilon. Ranking ties retain original priority and source-ID rules.

Budget/reach constraints use Decimal string inputs, finite nonnegative B,c,v and
0<=maxreach<=1. Counts use decimal ceil(q*N) preserving the original mathematical
rounding convention. A strict actual reach cap is floor(maxreach*N), which may
exclude a ceil-rounded boundary policy by one record. Do not silently trim or
interpolate a grid policy. Zero c removes the monetary cap only. Zero v recommends
none. B=0 with positive c forces none. No positive feasible grid reach is distinct
from evidence insufficient for one. Initial engine candidate grid ends at50%; all
is ONLY a comparator when both B>=c*N and maxreach>=1. No extra <10% policies.

Reason codes: selected; zero_value; no_feasible_positive_reach;
negative_estimated_net_benefit; inconclusive_lower_bound; assumption_sensitive;
insufficient_selection_support. Reasons can coexist. Integrity/invalid input failures
stop rather than masquerading as an economic abstention. Assessment support warnings
are separate. Always return spending, unspent budget, actual reach, counts, rejected
tranche details and all hypothetical assumptions. Abstention does not prove no useful
policy exists, particularly outside the grid or the stress set.

## Paired Gaussian working-model uncertainty

For each role compute centered contribution covariance S/(N), where S is sample
covariance with ddof1, using continuous joint-cell moments in bounded batches.
Each of four rankings has six bins (five10% tranches plus50–100% remainder); their
joint code has at most1296 cells. The continuous basis is
(TY,(1-T)Y,m1-m0,T(Y-m1),(1-T)(Y-m0),s1-s0,T(Y-s1),(1-T)(Y-s0)).
Linear maps reconstruct all360 tranche contributions (4*6*5*3). Combine centered
within-cell and between-cell moments; retain cross-policy/scenario/evaluator pairing.
All-target gains sum all six bins; prefix gains sum the first j bins.

Use2000 shared delta~N(0,S/N) vectors from symmetric eigenfactorization, PCG64
outerseed+7000000 selection and +8000000 assessment. Distribution equals row Gaussian
multipliers sum xi_i*(h_i-mean)/sqrt(N*(N-1)); NOT an ordinary row bootstrap.
Test the covariance and direct row Gaussian law independently on synthetic data.
The primary lower-bound family has300 coordinates, excluding each ranking's sixth
remainder bin: 4rankings*5tranches*5propensities*3evaluators. With SE=sqrt(diag(S/N)),
critical=linear95th percentile of max(delta_j/SE_j) over nonzero family coordinates;
L=point-critical*SE. If all variances are zero, critical=0. Zero variance gets zero
width. Reuse Phase7 tolerance: variance<=1e-12*maxdiag treated as numerical zero;
eigenvalues<-1e-10*maxdiag fail, tiny negative roundoff zeroed and recorded.
Pointwise gain/net/comparison intervals use .025/.975 linear quantiles of shared
draws. They are distinct from one-sided simultaneous decision bounds. The family is
within-role and within-split; no coverage across splits is claimed. Deterministic
nonnegative v and costs transform existing gain bounds; economics are not random.

All uncertainty is nominal IID working-model, conditional on fitted models,
nuisances, fixed original rankings and role-specific policies. No refitting,
reranking, unknown clusters, privacy selection, outcome stratification, selection
history or transport uncertainty is covered. The 2000-replicate quantile has Monte
Carlo error. Simultaneous bounds address declared comparisons, NOT causal bias.

## Comparison, validation and publication

Report selection evidence and independent-role assessment separately. At each fixed
economic scenario compare all budget-feasible fixed-grid policies, none and feasible
all. Also compare all four rankings at the engine's exact assessment assignment
count (including0). Same cap is NOT same spending. Paired contrasts use the same
Gaussian draws and clearly labeled pointwise intervals, never superiority claims
based on unadjusted multiple comparisons. At0 reach all matched comparators are0.
Assessment outcomes/support never alter frozen recommendations. Report each of five
overlapping splits, mean/range and abstention frequencies descriptively; no SE/sqrt5,
independent-replication confidence interval or final winner. Existing calibration and
repeated-vector diagnostics are referenced without treating vectors as customer IDs.

DR requires identification plus correct propensity or correct outcome regressions;
it does not fix hidden experiments, selection or dependence. Price sensitivity and
propensity/evaluator sensitivity are reported separately. No actual revenue, ROI,
causal superiority or realized savings. Future final-policy selection/locking and
one-time holdout evaluation need separate approval. No final_policy lock is produced.

Sequence: commit protocol and synthetic gates before real Phase8 evaluation; freeze
all role hashes; run first split; independently verify formulas, policies, leakage,
resources and protected hashes; only then continue four unchanged splits. Bounded
DuckDB1thread2GB, existing batch65536, BLAS2threads, sequential splits. No N*2000
array. Stop on resource failure without smaller data or estimator substitution.
New outputs only under artifacts/phase8 and new MLflow experiment. Resume verifies
provenance, role labels, recommendation hashes and artifact hashes without rewriting
existing matches. Publish aggregate-only Markdown/JSON and completion evidence.
