# Interview notes

## Phase 1 — reproducible scaffold

I established a versioned Python package and a locked analysis environment before
accessing the data. Configuration declares the exact corrected Criteo archive,
visit outcome, feature allowlist, holdout fraction and five development seeds.
Commands for later phases fail explicitly until implemented, so a scaffold cannot
be mistaken for a validated experiment. CI checks the package without downloading
millions of rows. Data and local MLflow outputs are excluded from Git; provenance
and readable reports will be versioned separately.

**Why isn't a fixed seed enough to prove a reproducible split?**
A seed depends on algorithm, library version and input ordering. We must bind
membership to the verified source file, persist row indices and hashes, and reuse
that registry. Phase 1 only declares seeds; Phase 3 creates the actual partitions.

**Does a dependency lockfile make the experiment fully reproducible?**
It fixes Python package resolution and distribution hashes, but not hardware,
native runtimes, data identity, randomization or every model operation. We also
need checksum verification, recorded runtime and code versions, split artifacts,
training seeds and tested procedures. Those gates are added phase by phase.

## Phase 2 — verified dataset acquisition

I made acquisition reproducible by using a full repository commit and the exact
corrected v2.1 filename. The command streams compressed bytes to a temporary file,
then measures its actual size and calculates SHA-256 from disk. Only a matching
file becomes the published raw archive. An interrupted or corrupt download fails
without publishing it. Repeat runs verify the local file again without another
network download. The small provenance manifest can be reviewed in Git while the
311 MB archive stays outside Git. The manifest explicitly separates expected rows
from observed rows: acquisition has not parsed or counted any records.

**Does a matching SHA-256 prove that the data is valid for causal inference?**
No. It binds our local bytes to the reviewed reference digest, assuming that
reference is trustworthy. It does not validate schema, row count, randomized
assignment, missingness, or causal identification. Those require later, separately
approved checks. A file-size check catches truncation cheaply but cannot detect
same-size corruption; SHA-256 provides that second check.

**How do you preserve reproducibility when cloud workspaces can disappear or a
transfer is interrupted?**
The pinned source identity and digest are versioned, so a fresh workspace can
reacquire exactly the same bytes. Partial files are never promoted to the final
archive; a rerun starts a fresh download. Existing archives are rehashed before
reuse. A manifest records the last successful verification, not guaranteed current
file availability or permanent storage. Durable caching would be a separate
storage decision, and every restored archive must still pass verification.

## Phase 3 — strict contract, stable row identity, and sealed evaluation

I verified all 13,979,592 records before converting the source to Parquet. An
independent CSV parser checks record counts and field widths; numeric and binary
checks reject bad records instead of quietly dropping or changing them. Each row
gets its original record position as an identifier. I hash every identifier together
with all typed values, then require the Parquet representation to match. Repeated
anonymous rows stay separate because we have no real customer key.

I sealed a joint treatment-by-visit stratified 15% holdout before any exploration.
Five fixed-seed train/validation splits live strictly inside development. Membership
hashes, versions, and rounding rules are versioned; row-level files stay outside
Git. Reconstruction must reproduce every hash before missing memberships are
restored. Validation results live separately from acquisition metadata, so rerunning
a download check cannot erase evidence of measured rows.

**Why do row counts and fixed seeds fail to prove split reproducibility?**
A seed produces different memberships if input order, row identity, the split
algorithm, or its library behavior changes. Even identical IDs can be attached to
wrong values after conversion. I bind membership to a verified source-row/value
mapping, record algorithm versions, and check complete membership hashes,
disjointness, and coverage. Fresh reconstruction must match the frozen registry.

**Does stratifying on visit mean that the final holdout has already leaked?**
Predeclared mechanical stratification uses the labels to balance partitions, but
makes no modeling or policy decisions from holdout performance. Whole-file contract
gates establish data identity and validity; they are not an exploratory audit.
No holdout outcome summaries or effects are calculated. Subsequent exploration,
preprocessing decisions, tuning, and model selection must use development only.
The source file remains accessible, so the seal also depends on disciplined access
through the development boundary and an explicit final-evaluation approval gate.

## Phase 4 — development-only audit and measured limitations

I audited all 11,882,653 frozen development records through a verified membership
join, leaving the holdout sealed. The audit measured each anonymized feature's
shape, tails, repeated levels and treatment/control balance. All fields were finite
and nonmissing. The largest absolute marginal SMD was about 0.0488, but dispersion
was not identical: f1's treated/control variance ratio was about 1.312. Eight
nonconstant features had zero IQR, showing why a simple outlier rule can flag
ordinary minority values in a concentrated distribution. About 18.10% of development
rows shared an entire feature vector with another row. Without customer IDs,
those are repeated measurements in feature space, not proven duplicated users.
Nothing was removed or transformed; future preprocessing choices must be learned
inside development training folds. Hashes confirmed all existing data, memberships,
registry and Phase 3 provenance files stayed unchanged.

**Do small SMDs prove that treatment was randomized or causal estimates are valid?**
No. SMDs describe marginal feature mean differences; they do not establish joint
balance, known assignment probabilities, or generalizability. I also checked
variance ratios and exact ECDF counts on a declared percentile grid. The largest
grid gap is a lower bound on the full KS distance, not an exact KS test. Missing
experiment IDs and privacy subsampling remain causal limitations even if measured
marginal imbalance is small. This phase estimates no treatment effects.

**Why keep repeated vectors and values outside Tukey fences?**
Anonymous features can be discretized or share common numeric levels; identical
vectors do not supply a real entity key. Deduplication could change the benchmark
population, treatment mix and frozen evaluation protocol. Zero IQR can make every
minority level a Tukey tail, so that flag alone does not establish corruption.
I preserve observations, report the measured multiplicities and tails, and qualify
independence assumptions. Any later transformation or sensitivity analysis needs
the approved training/validation protocol and must not use holdout outcomes.

## Phase 5 — descriptive assignment contrast with honest nominal uncertainty

I calculated the difference in visit rates across the frozen development assignment
arms: 490,301 visits among 10,100,257 treated records (4.854342%) versus 68,089 among
1,782,396 control records (3.820083%). The difference is 1.034259 percentage points,
not a 1.034259% relative increase. It corresponds numerically to 10.342592 visit
outcomes per 1,000 assignments, with nominal 95% interval [10.030712, 10.652817].
I used the predeclared Newcombe–Wilson interval without continuity correction,
checking it against Statsmodels and independent high-precision score calculations.
The full development pool was counted once; all frozen memberships and prior
provenance stayed unchanged. Exposure was not used for conditioning or adjustment.

**The nominal interval excludes zero. Why not claim that ads caused this lift?**
The point estimate is an unadjusted descriptive assignment contrast. A causal ITT
interpretation needs exchangeable assignment and suitable selection assumptions,
as well as consistency and no interference. Non-uniform privacy subsampling and
pooled experiments with unknown assignment probabilities can violate these.
The nominal interval assumes independent Bernoulli observations; it does not
account for unknown clustering or the outcome-stratified development selection
and is not an exact randomization interval. Precision under a working model does
not measure selection bias or establish advertiser-wide causal impact.

**Why use Newcombe–Wilson, and why not estimate the effect among exposed users?**
Newcombe combines two Wilson score intervals, accommodates unequal arm sizes,
and handles zero/all-event cases where a simple Wald interval can degenerate.
The numerical formula is independently verified, but that does not verify the
sampling assumptions. Exposure is post-assignment; filtering or adjusting for it
changes the question and can induce selection bias. This phase compares assignment
arms only and makes no treatment-on-the-treated, individual uplift, revenue or
policy-optimization claim. Those questions are not answered by a narrow interval.


## Phase 6 — fixed development baselines

We compare three ways to rank advertising assignments: random order, a model of
visits among treated training records, and one model whose prediction changes
when we switch a separately supplied treatment indicator. High visit probability
is not the same as advertising responsiveness: someone may visit either way.
We freeze the recipes before seeing performance and reuse the five original
train/validation memberships. Only f0–f11 describe users; the holdout stays sealed.

Evaluation asks what a fixed targeting rule would score under a specified
assignment-propensity assumption. We report e=.85 separately from sensitivity
scenarios because the release does not establish individual assignment probabilities.
The resulting IPW differences are not proven causal gains. Two thousand paired
bootstrap resamples quantify a narrower working-model uncertainty: they hold the
trained models and original targeting rules fixed. Joint ranking-bin compression
makes that row-bootstrap calculation practical without changing its distribution.
Five-reach simultaneous bands address that family within a split, while ordinary
pointwise intervals do not. Overlapping splits summarize stability rather than
provide five independent replications. Full-prefix areas use every rank, even
though comparison tables show only five reach percentages.

**Two challenging questions**

1. **Why can a convincing IPW confidence interval still fail to establish causal
   targeting gains here?** The interval assumes the fixed propensity scenario and
   IID released records. Unknown experiment propensities, outcome-related privacy
   selection and dependence can bias the point estimate; development stratification,
   training variability and cutoff estimation are not captured by this bootstrap.
   A narrow conditional interval cannot validate those assumptions.
2. **How can fewer than 864 bootstrap cells represent millions of paired rows?**
   For fixed nested policies, every row in a joint rank-bin × assignment × outcome
   cell contributes the same value to every reported policy statistic. Summing
   ordinary row-bootstrap multiplicities within cells has exactly the multinomial
   cell law used by the compressed calculation. This does not justify compressed
   refitting, reranking or bootstrap uncertainty for full-prefix ranking areas.

Measured example: at 10% reach and reference e=.85, mean gain over no targeting
was 9.3593 per 1,000 for S versus 8.1106 for response. Their mean difference
changes from +1.2487 at e=.85 to −2.0561 at e=.80. This illustrates why model
ranking and narrow conditional bootstrap intervals cannot establish causal
superiority when assignment assumptions remain uncertain. Full evidence and
per-split uncertainty are in reports/phase_6_baselines.md.

## Phase 7 — T-learner and honest robust evaluation

The T-learner predicts visits separately for treated and control assignments, then
subtracts those probabilities. I reuse the verified treated-response model and
train the missing control model, keeping f0–f11 and the same frozen development
partitions. Separate models allow different response patterns across arms, but
the smaller control sample can make the difference noisier.

The shared doubly robust evaluator adds outcome-model residual corrections to
model-based policy values. Its outcome predictions come from training-only
nuisance folds, with every candidate policy evaluated using the same predictions.
Double robustness does not mean assumption-free causality: selection into the
release, unknown experiment propensities and dependence remain unresolved.
Propensity and alternative-nuisance sensitivity are reported without choosing
whichever evaluator favors the new model.

Two thousand correlated Gaussian-multiplier draws quantify conditional sampling
uncertainty. Continuous outcome predictions break the earlier exact multinomial
cell shortcut. Instead, within-cell first/second moments reconstruct the joint
covariance exactly up to floating-point error; Gaussian draws reproduce the
row-multiplier law, not an ordinary row-bootstrap distribution. Simultaneous
bands cover ten predeclared T-versus-S comparisons within a split. Overlapping
splits describe development stability, not independent confirmations.

**Two challenging questions**

1. **If either nuisance model can be wrong, why can't DR settle this benchmark's
   causal ranking?** Double robustness assumes an identified causal problem. A
   model of treatment patterns in selected released data is not a verified
   original assignment mechanism, and good outcome calibration does not prove
   exchangeability after outcome-related privacy selection. Both nuisances can
   be wrong, and conditional intervals omit these biases and model-fitting risk.
2. **Why replace the earlier compressed bootstrap, and what equivalence remains?**
   Rows sharing policy bins, assignment and outcome can have different DR residual
   contributions because their predicted probabilities differ. Multinomial cell
   counts cannot represent those differences. Continuous cell moments preserve
   covariance for the fixed linear policy statistics; Gaussian multiplier draws
   have that same joint law as Gaussian row multipliers. This neither reproduces
   exact multinomial bootstrap tails nor justifies intervals for refitted models.

Measured Phase 7 example: at 10% reach and reference e=.85, mean T-minus-S was
−0.3641 per1,000 with IPW and −0.1962 with shared DR. The first split's simultaneous
bands included zero under both methods, despite its IPW pointwise interval excluding
zero. Higher-reach response/S ordering changed between evaluators. The work did
not establish a T advantage or justify selecting a final policy; fair comparisons,
assumption sensitivity and preservation of the holdout are the outcome.

## Phase 8 — a budget is a ceiling, not an instruction to spend

I turned existing rankings into a development-only decision simulator. Every
scenario declares a hypothetical assignment cost, visit value, budget and maximum
reach. The engine examines successive 10% reach tranches and expands only when each
additional tranche has a positive conservative lower net value across all declared
propensity and evaluator assumptions. It can stop early or recommend no targeting.
It does not turn a high Qini score into a claim of profitable advertising.

I separated each frozen development validation partition into outcome-blind
selection and assessment roles without changing the original memberships. Decisions
and assessment assignment hashes are saved before assessment outcomes are queried.
This reduces direct optimizer bias, but these development outcomes were examined in
earlier phases, so assessment remains exploratory rather than confirmatory.

Two thousand paired Gaussian draws provide one-sided simultaneous bounds for 300
marginal comparisons per role/split. Those bounds address the declared comparisons
conditional on existing models and policies. They do not make assumed propensities
correct or remove privacy selection, unknown dependence or model-fitting uncertainty.
Every cost/value is hypothetical; there is no observed revenue or ROI.

Actual result: all 40 predeclared economic-scenario/split combinations recommend
zero assignments. Zero visit value and too-small budgets have distinct reasons;
other scenarios fail robustness to assumptions even with free assignments. For
example, first-split S first-tranche selection gains range from −1.2511 to +16.0286
visits per 1,000 across assumptions; its worst simultaneous lower bound is −2.7875.
I kept the rule unchanged instead of choosing a more flattering evaluator or price.
No final deployment policy was selected or locked and the holdout remains sealed.

**Two challenging questions**

1. **Why can a narrow positive reference-scenario interval coexist with a no-spend
   recommendation?** Conditional sampling precision is not robustness to causal
   assumptions. A different assumed propensity can reverse the gain. The engine
   requires every declared scenario to support positive marginal net value; the
   stress minimum is not a probability-weighted causal confidence statement.
   Simultaneous bounds cover the declared statistics, not misspecification bias.
2. **Does splitting validation into selection and assessment remove selection bias?**
   It prevents the new engine from using assessment labels to revise its selected
   policy, and tests changing those labels leave recommendations unchanged. It
   does not erase prior development inspection, unknown dependence or original
   outcome stratification. Overlapping outer splits are not independent trials.
   Final policy locking and a separately approved one-time holdout evaluation
   remain necessary before a confirmatory headline claim.

## Phase 9 Stage A — lock the question before unsealing outcomes

I separated final preparation from final evaluation. The approved preparation fits
nine fixed diagnostic models on development records only, records exact training
membership/fold/model hashes and freezes the complete statistical comparison suite.
It preserves every previous model and result. Development correctness probes verify
reloads, leakage boundaries and formulas; they do not estimate generalization.

The primary recommendation is no targeting because the conservative development
engine abstained across all declared scenarios. Its zero gain over the same
no-targeting policy is an identity, not a statistically discovered zero effect.
Users may still visit without advertising, and abstention is not proven optimal.
All targeting strategies remain secondary diagnostics and cannot replace that
recommendation after final holdout results become visible.

Two thousand correlated Gaussian draws support a frozen 765-contrast diagnostic
family, with pointwise and simultaneous intervals clearly separated. A second
uncertainty calculation conditions on treatment×visit stratum counts. Conditioning
can make an aggregate assignment contrast have zero variance; that is not exact
causal certainty. Unknown experiment propensities, privacy selection, dependence
and model estimation remain limitations under both methods.

Stage B cannot run: a local flag or approval JSON is not trusted authorization, and
this workspace has no integrated protected-reviewer/durable create-once receipt
service. All real holdout entry points reject access before I/O. Later activation
requires separately reviewed gate integration, re-locking and approval of the exact
code/model digests. Stage A review or merge never grants outcome access.

**Two challenging questions**

1. **Why evaluate a holdout if your primary policy targets nobody?** No outcome
   access is needed to establish its zero incremental gain relative to itself.
   A later separately approved holdout analysis can assess predeclared diagnostic
   strategies, but it cannot prove optimality or justify choosing a new winner.
   Keeping the holdout sealed remains a defensible alternative.
2. **Why is a signed-looking JSON or CI checkbox insufficient to authorize a
   one-time evaluation?** A local payload can be edited or copied, and a local
   receipt can disappear across cloud tasks. Authorization must be verified against
   a trusted reviewer decision bound to exact code/model hashes, and an external
   atomic create-once record must survive runners and interruptions. Without both,
   a fail-closed disabled interface is more honest than pretending one-time access
   is enforced. Even those controls cannot validate causal identification.


## Stage B safeguards preparation: approval is separate from execution

The models and policy are already frozen. I added a way to verify an owner's
Ed25519 signature over the exact execution identity, and a receipt design that
reserves one evaluation for the sealed cohort. A changed model, owner, or run ID
cannot create a fresh evaluation opportunity. Prediction hashes must be sealed
before outcomes, and a crash never clears the receipt. Current real access remains
disabled: synthetic and local Git tests cannot prove GitHub protections or that a
backup survives the loss of this Cloud workspace.

**Challenging question 1: Does a create-once Git tag guarantee exactly-once analysis?**
No. It can prevent accidental duplicate claims if server protections are verified,
but admins can change those protections. Crashes also make exactly one physical
read unrealistic. We enforce one locked campaign, preserve its claim, and stop on
ambiguous recovery rather than choose another model or start over.

**Challenging question 2: Why is a signed backup hash insufficient to prove durability?**
It proves the signer approved those bytes, not where they are stored or whether
they survive workspace deletion. The owner must verify an independent private copy
and a restore/hash check. Lost checkpoints cause a stop, not an independent rerun.
