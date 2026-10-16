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
