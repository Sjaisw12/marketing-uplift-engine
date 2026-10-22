# Scientific content map

Single authority: checksum-pinned `public/aggregate_results.json`. The frontend
copies saved values or applies the documented descriptive/illustrative arithmetic;
it never estimates treatment effects or confidence intervals.

| Number / claim | Exact source | Where and plain-English explanation |
|---|---|---|
| 13,979,592 records | `population.source_rows` | The study: benchmark records, not verified unique customers. Hero uses 13.98M display rounding. |
| 11,882,653 development records | `population.development_rows` | The practice ground: building and comparing frozen methods. |
| 2,096,939 held-out records | `population.holdout_rows` | The final exam: one-time evaluation after locking. The 85/15 graphic is nominal; exact counts are printed. |
| 3.8202% control visits | `support.control_visits / (control_visits + control_nonvisits)` | Observed rate bar; exact visits/denominators are printed. Descriptive assignment statistics. |
| 4.8543% treatment visits | analogous treatment fields | Assigned-ad group; assignment is not actual exposure. |
| 1.0341 percentage points | 100 × treatment/control rate difference | Descriptive gap, explicitly not verified causal lift or relative percent change. |
| Four rankings and 10/20/30/40/50% reach | `comparisons` contrasts `model:k_minus_none`; k=1…5 | The evidence: everyday-language model explanation before technical name; equal-reach interval plot and exact table. |
| Selected gains and bounds | `estimate_per_1000`, selected `pointwise_*` or `simultaneous_*` | Additional visits per 1,000 **eligible**, not per 1,000 ads. Every dot and whisker is a saved lookup. |
| T-minus-S | saved `s_learner_minus_t_learner:k`, negate value and swap/negate endpoints | Paired note: compare the direct paired contrast; no interval-overlap inference. |
| Zero no-targeting assignments, spending and relative gain | `primary` | Decision reveal and lab default: mathematical identities, not optimality/ineffectiveness proof. |
| 40 development abstentions | historical approved `../reports/phase_8_decisions.md` and owner's reviewed Phase 8 conclusion | Decision reveal: all 40 scenario/split combinations abstained; not 40 independent replications. |
| Assumed e=.80/.825/.85/.875/.90 | `methodology.propensity_scenarios` | Technical controls and reference sensitivity plot; discrete assumptions, not a distribution or known individual assignment. |
| IPW/shared-DR sensitivity | `all_minus_none`, both evaluators at five assumed e, IID simultaneous | Decision reveal: saved all-targeting reference. Min/max printed as ranges of saved point estimates, not new confidence intervals. No connecting/smoothing lines. |
| 765 comparisons, 2,000 draws, 95% | `methodology.simultaneous_family_size`, `replicates`, `confidence` | Evidence qualification and advanced section: nominal conditional uncertainty; family retained after filtering, including unselectable nuisance sensitivity. |
| Hypothetical budget outputs | selected saved gain/bounds plus numeric user assumptions | Decision Lab: Decimal arithmetic matching Python; N × gain / 1,000; ceiling assignments; reject over-cap candidates; no optimization or real ROI. |
| Three customer types | conceptual teaching graphic, no dataset classification | The question: explicitly invented examples, not observed individual causal types or fitted model outputs. |

The browser receives the approved aggregate snapshot, not models, memberships,
outcomes, checkpoint files, signatures, production refs or execution credentials.
