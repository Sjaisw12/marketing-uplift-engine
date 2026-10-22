# Phase 11 — final focused UI/UX polish

Local branch: `codex/phase-11-final-polish`.
Base: `29d94120840ddff5416c1145223a3b097cc12990` (premium redesign).

## Changes

The navy/cobalt theme, navigation, page composition and statistical logic remain.

- Executive overview adds **How this helps a marketing decision-maker**, covering
  policy comparison, uncertainty, budget trade-offs and conservative decisions.
  A native button opens Policy performance without changing any recommendation.
- Policy charts use 14px axes/legend labels, explicit legend titles, larger opaque
  points, clearer whiskers and responsive spacing. Compact insight cards describe
  the selected saved intervals and exact paired T-minus-S contrast. They never
  label a ranking the best causal policy. If S/T are hidden, the second card
  explains the equal-reach denominator and unchanged 765-comparison family instead.
- Sensitivity adds a prominent panel showing the selected policy/reach's five-point
  IPW and shared-DR ranges. Relative stability is described conditionally from those
  saved points, with an explicit statement that these ranges are not confidence
  intervals and do not verify causal identification or nuisance correctness.
- Budget keeps No targeting selected on initial entry. A prominent instruction
  explains the policy/reach and financial inputs. Exploratory selections receive
  a labeled output panel and accented tiles; the same unchanged calculations apply.
- Mobile controls, labels, compact cards and chart spacing are refined; no new
  frontend dependencies or external services are introduced.

## Actual final checks

| Check | Result |
|---|---|
| Full applicable `make check` | **476 passed, 20 full-data deselected**, 148.79 seconds |
| Focused dashboard tests | **78 passed**, including all original 65 and four new polish regressions |
| Ruff lint / format | PASS; **114 Python files** |
| Browser | Five pages at 390, 768, 1024 and 1440px; **20 checks**, no app exceptions or document-width overflow |
| Interaction | Overview CTA navigates correctly; exploratory budget policy selected successfully in Chromium |
| Minimal runtime | Python 3.12.14; all five pages and actual HTTP health 200 PASS |
| Standalone preview | Same five-page/HTTP smoke, using only copied approved public inputs |

The browser harness initially clicked the select wrapper rather than its native
combobox. Focusing the native combobox and using its keyboard interaction resolved
that harness failure; the app needed no workaround. Final screenshots include all
five pages at four widths plus focused captures of the four polished sections.
Automated palette and responsive checks are not a formal accessibility certification.

New tests cover CTA state transitions, exact selected paired values, hidden-policy
fallback text, sensitivity text under both ordinary and reversed relative stability,
no-targeting initialization, exploratory budget interaction and readable chart fonts.

## Preservation and disclosure

The approved public snapshot SHA-256 remains
`358c331d72df76d0ca1e4fddd36c7c35be32b1a0b2dd0ae12949c5967ac46169`.
The loader, financial module, snapshot, minimal dependencies, root lockfile,
project configuration and premium theme configuration are byte-identical to the
base. Historical experiment code/results, execution locks, models and memberships
are unchanged. Preservation checks read public committed files only, not private data.

No experiments, outcome access, model training/scoring, private campaign access,
checkpoint operation or remote write occurred. No statistical interval or estimate
was recomputed. Textual ranges/counts summarize selected saved aggregates only;
paired values are exact lookups. The original 765-comparison simultaneous family
and pointwise/conditional qualifications remain. Positive illustrative net benefit
is not validated ROI, deployment advice or a new policy recommendation. No targeting
remains the frozen primary recommendation. MIT software and Criteo-derived
CC BY-NC-SA 4.0 attribution remain intact.

## Review package

The updated review-only ZIP includes exact polish files, a polish diff, cumulative
Phase 11 diff, verification logs, 24 screenshots, member hashes and a standalone
`preview/` folder containing only allowlisted public source and approved aggregate
inputs. Mac launch instructions are in START-HERE.md and docs/DASHBOARD.md.
No private Git history, credential, signature, row-level prediction, model binary,
checkpoint or raw record is included. Nothing is uploaded or deployed by packaging.
Owner review and any later transfer/publication remain separate actions.
