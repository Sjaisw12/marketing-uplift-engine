# Phase 10: local disclosure and reproducibility review

**Status: local candidate materials only.** No push, public PR, merge, external
upload or publication is authorized. The owner must review the exact file set
before any public release. This document records a technical disclosure review,
not a guarantee of anonymity or a substitute for the dataset license.

## Scope and immutable evidence

The authoritative nine-page roadmap was read in full. The owner's Phase 10 scope
is portfolio finalization: README, architecture, figures, case study, interview
materials, reproduction code and tests. The roadmap also describes a Streamlit app,
deployed demo and recording. Those are outside this approved phase and remain
unimplemented; portfolio materials do not claim them.

The base evaluation commit is `ac97b467bd3723c6f3ee76f3dff7c3418f30eb4f`.
The child lock is `b7dca1de6089f2f621c4972d078c906f126205d837e8485064633a326f9e212c`.
The final result-manifest SHA-256 is
`447eaa876994dbf77f141d956e80881b96892778943bb72bbcef5a7a554c0ac2`.
These are provenance identities, not permission to execute again.

Stage B completed and closed on 2026-10-20. Phase 10 never constructs an operator,
reads outcomes/features, loads fitted models, resamples, scores or refits. Historical
locks and sealed protocol files remain unchanged, including their historical
preparation-only statements. Their present-day status is superseded by the
completion record and phase checklist, not by editing frozen evidence.

## Candidate disclosure inventory

| Included locally for review | Why / review boundary |
|---|---|
| Whole-holdout arm visit/nonvisit counts | Four large aggregate cells, minimum 12,016; no subgroup or feature disclosures |
| 765 saved contrasts × two uncertainty methods | Complete predeclared family; aggregate estimates/SEs/intervals only |
| Aggregate source/result/model/data hash identities | Provenance without model bytes or private operational payloads |
| Static PNG/SVG and aggregate CSV | No embedded row-level sources, scripts, signatures or credential links |
| Narrative and model card | Limits and hypothetical economics stated; no claims of profitability |

**Excluded:** row IDs, membership files, feature values, outcomes by record,
prediction arrays, nuisance arrays, multiplier draws, covariance files, fitted
models, private repository contents/URLs, encrypted checkpoint chunks, absolute
private paths, receipts/journal payloads, approval envelopes, signatures and keys.
Existing historical public files are not copied wholesale into presentation assets.

The candidate JSON uses an exact allowlist at every object level. Extra row-level
or operational fields fail validation. The allowed comparison keys require all
15 evaluator/propensity combinations and both uncertainty methods, without duplicate
or missing contrasts. This is a low-dimensional aggregate disclosure; it is not
differential privacy and does not claim zero inferential disclosure risk.

## Provenance checks performed

1. Verify the existing private final result manifest and hashes of its saved result files.
2. Independently reconcile every candidate estimate, SE and both interval endpoints
   against the saved aggregate arrays: 1,530 rows × six numeric fields.
3. Reconcile the four support counts with the saved result metadata.
4. Copy only the allowed fields into `reports/portfolio/aggregate_results.json`.
5. Pin its exact byte SHA-256 in the presentation module:
   `358c331d72df76d0ca1e4fddd36c7c35be32b1a0b2dd0ae12949c5967ac46169`.

No outcome records are opened for these checks. This binds the candidate assets to
the already completed analysis; hashes do not independently validate the underlying
causal assumptions. The smaller snapshot omits the private operational binding and
does not claim to be the original result manifest.

## Safe reproduction

```sh
uv sync --locked
make portfolio
uv run --locked pytest tests/test_portfolio.py -q
make check
```

The renderer is `python -m portfolio`, isolated from analytical/execution modules.
It validates the pinned snapshot, draws saved statistics, and writes PNG/SVG,
the full aggregate CSV and `figure_manifest.json`. It does not derive new confidence
intervals or run bootstrap/multiplier draws. Its only new calculation of observed
rates is division of saved aggregate counts; paired T-minus-S display reverses a
saved S-minus-T contrast and swaps/negates its saved endpoints.

Matplotlib 3.11.2 is already resolved in unchanged `uv.lock`; no new dependency
or lockfile modification is needed. PNG/SVG byte reproducibility is tested in the
same pinned runtime. Font/rendering differences across OS/Python versions may change
image hashes; the snapshot, plotted numbers and interval semantics remain identical.
The figure manifest records the installed plotting version and output hashes.

The public-style package can render without a raw dataset, private models, MLflow,
campaign directory, network access or authorization. Historical `make reproduce`
is **not** the presentation command and must not be used for this finalization.
The completed holdout analysis is not rerunnable; scientific replication would
require a separately designed study, not replaying the consumed campaign.

## Owner publication gate

- [x] Source provenance and all saved aggregate values reconciled locally.
- [x] Candidate field allowlist excludes row-level and private operational material.
- [x] Dataset attribution and CC BY-NC-SA 4.0 treatment included.
- [x] No-targeting primary policy and all predeclared comparison coverage preserved.
- [x] Assumed e, units, multiplicity and working-model limitations accompany figures.
- [ ] Owner reviews the exact local aggregate snapshot, figures and narratives.
- [ ] Owner explicitly approves public disclosure and the exact publication operation.

No publication action is performed by this phase. Private local artifacts do not
gain cross-task durability from this documentation; no backup operation was performed.
