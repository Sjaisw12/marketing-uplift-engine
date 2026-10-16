# Phase 9 Stage A — frozen preparation protocol

Only Stage A is approved. No holdout feature rows, assignment, visit, conversion,
exposure, outcomes, predictions or performance are read or calculated. Frozen ID
membership metadata and byte hashes may be verified. Existing source, partitions,
models, predictions, MLflow, configurations, protocol sources and all Phase 1–8
reports remain immutable. New code/config/artifacts are additive; uv.lock unchanged.

## Primary policy and secondary diagnostic recipes

Primary policy pi0(X)=0 in each of the eight unchanged Phase8 economic scenarios.
Record model=null, ranking=null, reach0, assignments0, hypothetical spending0 and
incremental gain over pi0 exactly0 by identity. No estimated confidence interval is
required for that identity. V(pi0) need not equal0: users can visit without assignment.
This does not prove advertising ineffective, abstention optimal or campaigns harmful.
Preserve development reason codes and all40 recommendations; do not rerun the engine
on holdout labels or substitute any favorable diagnostic result for abstention.

Secondary policies: random, treated-response, S and T top10/20/30/40/50%, none/all
anchors. All are predeclared; no winner selection. Full-development refits are new
artifacts, not revisions to historical Phase6/7. Exactly f0–f11 in canonical order
are user predictors. Arm assignment routes treatment/control fits only. S receives
separate binary __intervention_treatment; this is not a user predictor export.

Use configs/baselines.toml unchanged: binary GBDT200 rounds, learning rate.05,
31leaves, minleaf1000, max_bin63, training bin sample200000, two threads, deterministic
column-wise,256MB histogram pool, full row/feature fractions. No preprocessing,
feature selection, calibration fitting, tuning, early stopping, weighting, imputation,
deduplication or validation-driven recipe changes. Seeds in configs/phase9.toml
are fixed before training:9000001 arm/S,9000002 nuisance folds,9000003 random rank,
9000004 IID multiplier,9000005 stratified multiplier,9000100+10*k+arm nuisance fits.

All11,882,653 frozen development rows train final S; arm models use their respective
development assignment arms. New nuisance folds: PCG64(9000002).permutation(n) over
sorted development positions, round-robin modulo3. Persist labels and hashes before
fits. Each of six models fits only its arm outside fold k. Model hashes, exact fit
mask/ID hashes and event support are recorded. Mean three fold-model predictions
per arm is the primary shared DR nuisance for EVERY policy. New final S p0,p1 are
the shared nuisance sensitivity. They are not the historical saved S predictions.
No evaluation data participates in nuisance fitting. Development OOF predictions
may verify exclusion; full-refit development probes are correctness checks, NOT
out-of-sample performance estimates. No holdout scoring occurs in Stage A.

## Transfer and economics frozen for a future Stage B

Stage B, if separately authorized after reviewing this lock, would first score only
holdout f0–f11 using frozen models, then persist prediction/membership hashes before
any outcome read. Sorted source IDs are alignment/tie metadata only. PCG64(9000003)
priorities over sorted cohort IDs; descending score, descending priority, ascending
source ID. Random ranking uses those same priorities. Top ceil(q*N); none0/allN.
No learned threshold or holdout outcome-dependent cutoff. Store nominal/actual reach.

Preserve eight economics from configs/phase8.toml without price/model/reach selection.
B=b*N; cost c per assignment and value v per incremental visit remain hypothetical.
Decimal exact budget checks and floor(maxreach*N) caps; reject infeasible ceil-rounded
grid candidates without trimming/interpolation. All is only an economic comparator
when feasible. Same cap is not equal actual spending. Primary none and its matched-
spending comparators all target0; positive-reach diagnostics are separate.

## Estimands, formulas and identification

The causal target is V(pi)=E[Y(pi(X))], gain Delta(pi)=V(pi)-V(0) in the released
benchmark. Observable estimators under fixed assumed e are scenario functionals;
causal interpretation requires consistency, no interference, positivity,
exchangeability and suitable nuisance correctness after selection into the release.
Five e assumptions .80,.825,.85,.875,.90; .85 is reference only. Do not estimate e
from holdout assignment share or treat scenarios as a calibrated distribution.

IPW H0=(1-T)Y/(1-e), Z=TY/e-(1-T)Y/(1-e).
DR H0=m0+(1-T)(Y-m0)/(1-e),
Z=m1-m0+T(Y-m1)/e-(1-T)(Y-m0)/(1-e).
Policy value=mean(H0+pi*Z), gain=mean(pi*Z), paired contrast=mean((piA-piB)*Z).
Use primary shared fold-average DR and final-S DR sensitivity separately, fairly
for all policies. Never select the favorable evaluator or clip negative estimates.
Units: visits/eligible record or1000 eligible records, not visits/targeted user.
Hypothetical net value=v*N*gain-c*n_selected; no observed revenue, ROI or savings.
DR double robustness does not resolve privacy selection, hidden experiment-specific
propensities, dependence or invalid causal identification.

## Paired uncertainty and full diagnostic family

2000 correlated Gaussian-multiplier draws per method, fixed seeds. For IID working
model compute sample contribution covariance S (ddof1), covariance of means S/N;
draw delta~N(0,S/N). Equivalent in distribution to centered Gaussian row multipliers
sum xi_i(h_i-hbar)/sqrt(N*(N-1)), NOT ordinary row bootstrap or exact randomization.
Use fixed fitted models, nuisance predictions, ranks and memberships in every draw;
no refitting, reranking, seed selection or policy changes. Shared draws retain all
pairing across policies/evaluators/e. Streaming continuous cell moments recover375
coordinates:15 scenarios*(one baseline+4rankings*6bins). At most1296 joint rank cells.
Basis:TY,(1-T)Y,m1-m0,T(Y-m1),(1-T)(Y-m0),s1-s0,T(Y-s1),(1-T)(Y-s0),m0,s0.

The TWO-SIDED simultaneous family is765 contrasts: each15 evaluator/propensity
combination includes20 policy-vs-none gains,30 same-reach unordered pairwise ranking
differences (6pairs*5reaches) and1 all-vs-none gain. It is NOT Phase8's300 lower-bound
family. Critical=linear95th percentile max absolute standardized centered draw over
all765; intervals=estimate +/- critical*analyticSE. Pointwise intervals separately
use linear.025/.975 quantiles of shared shifts. Absolute values have pointwise
intervals only; no multiplicity-adjusted claims for those values or ranking areas.
Zero variance tolerance1e-12*max covariance diagonal; eigenvalues below-1e-10*scale
fail, tiny negative roundoff zeroed/recorded. Singular comparisons get no fake noise.
Numerical zero-width intervals do not establish causal certainty.

Mandatory SECONDARY stratified sensitivity: fix observed T x Y stratum proportions
w_h=n_h/N and original cohort ranking memberships. Within each of four strata use
sample covariance S_h; C_strat=sum_h w_h^2*S_h/n_h. No reranking within strata.
Absent strata have weight0; a nonempty stratum with<2 records stops that sensitivity
as undefined, not substituted by IID. Point estimates are the same weighted means.
Draw2000 correlated Gaussian vectors with seed9000005, construct the same765-family
bands separately. This conditions away random stratum composition; even all-vs-none
IPW can have zero conditional variance. Not a randomization CI or correction for
privacy selection/unknown clusters. It must not replace the primary IID uncertainty.
No joint coverage across uncertainty methods is claimed, no favorable-method choice.

Both methods are nominal working models, conditional on fitted models and policies;
omit training, threshold-estimation, unknown customer/experiment dependence and
selection-history uncertainty. Stratification and release design constrain coverage.
No independent-replication CI from the five overlapping development splits.
Optional IPW AUUC/Qini retain full n+1 prefixes, trapezoid integration and unnormalized
Qini=AUUC-.5*allgain, no area CI or DR area; no spending or winner selection by areas.

## Access, approval and one-time execution gate

Stage A reads only an explicit JOIN to verified development IDs, never generic
arbitrary-membership extraction. API checks IDs are a subset of development before
opening Parquet, then checks row alignment/types/nonfinites without coercion.
Future holdout feature scoring and outcome evaluation have separate entry points.
Both real holdout interfaces are DISABLED in this implementation, regardless of
boolean arguments, claimed approval strings, lock files or environment variables.
Synthetic array evaluation is reusable but is not a real holdout reader.

Blocker: this workspace has no configured/verifiable required-reviewer protected
StageB execution service and no independently durable append-only create-once
receipt store shared across tasks/runners. Gitignored local JSON, chmod, workflow
booleans and environment names alone do not enforce either requirement. Therefore
Stage B remains disabled. No real execution-start receipt is written in Stage A.

Future activation requires separate explicit approval tied to EXACT final lock and
model-manifest digests; verified human approval in a protected environment; trusted
approval verification; durable atomic create-once receipt BEFORE any outcome read;
exclusive execution identity; code/model/data dependency checks; pre-outcome policy
hashes; immutable result/contribution archive and audit trail. A local payload is
not trusted proof of approval. A StageA PR merge is not StageB authorization.
The disabled workflow template must not be enabled by a boolean dispatch input.

Recovery: receipt is consumed before first outcome access, including failure after
that point. Never clear it to rerun or change a model/policy. Interruptions stop for
review; only the same locked execution may recover from verified saved checkpoints.
Arithmetic replay from immutable evidence is an audit, not a new policy evaluation.
If storage/approval cannot be enforced, remain disabled. Enabling requires new code
review/approval and re-locking code dependencies BEFORE StageB approval.

## Reproducibility, resources and gates

Freeze protocol, source/dependency hashes, nuisance fold labels and fit definitions
before fitting. Final lock binds final model manifest, versions, protocols, source
and membership hashes, unchanged economic scenarios/development reasons, code and
CI gate policy. Historical fingerprints verified before/after and on resume.
No raw records/model/prediction/fold files enter Git; publish only hashes/aggregates.
New artifacts/phase9 directory and separate local MLflow experiment; prior runs
read-only. Existing matching final fits resume only on exact provenance/artifact
checks; partial fits stop for review rather than overwrite or silently retrain.

Run synthetic references/leakage/gate tests first, then nine sequential development
fits. Use existing8GiB/two CPUs, bounded DuckDB2GB1thread, batch65536, disk preflight,
memmaps and no N*2000 matrix. Stop on resource failure without changing recipes.
Development-only probes verify model reloads, row alignment, nuisance exclusion,
formulas/covariance on permitted arrays; they are not tuning or final performance.
CI has synthetic/default checks and a separate manual StageA-only verification mode
using already verified development artifacts. Never route StageA through the old
whole-source validation/reconstruction workflow, which reads source outcome columns.
No acquisition, ingestion or split regeneration in this intact workspace.

## Portable review seal and training lineage

The final review identity hashes repository-relative file names and raw file bytes,
including the complete package, frozen configurations/protocols, tests, tracked
source/membership metadata, lockfile and Phase8 aggregate evidence. Historical
Phase6–8 path-dependent protocol IDs remain preserved provenance; they are not
recomputed as a public checkout identity. A relocation test must preserve the new
protocol digest. Raw datasets/models are not required for the public check.

JSON payload digests use SHA256 of UTF-8 JSON with sorted keys, compact separators
(',', ':'), and no nonfinite numbers. Lock digest excludes its enclosing digest
field; model-manifest digest covers the manifest payload. These canonical payload
digests are distinct from raw pretty-printed file byte hashes.

The initial development preparation record and its nine fits are immutable. A
review-seal operation may adopt those exact completed fits after verifying unchanged
training/feature/evaluation kernels, seed configuration, hyperparameters, caches,
fit IDs and model bytes. It records original training-protocol/code provenance and
the new portable evaluation identity separately. This fixes metadata portability,
not model recipes, performance or policy selection; no fit is repeated. Preserve
the original preparation record/MLflow run and create a separate review-lock run.
A completed final review lock cannot be replaced by that operation.
