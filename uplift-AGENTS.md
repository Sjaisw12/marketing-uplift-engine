# AGENTS.md — Marketing Uplift & Causal Decision Engine

## Project
Build an offline causal marketing decision engine on the Criteo Uplift v2.1 dataset
(13,979,592 rows, randomized treatment/control). The authoritative spec is the final
roadmap PDF attached to this Codex project. If any document conflicts with it,
the final roadmap wins.

## Non-negotiable rules
1. DATA DISCIPLINE: Never print full dataframes or large outputs. Use `.head()`,
   DuckDB aggregations, or small samples. The raw file is ~3.2 GB uncompressed —
   dumping data into context wastes budget and breaks focus.
2. SEALED HOLDOUT: Create the 15% final holdout ONCE at the start, record index
   hashes, and never evaluate on it until the single final headline run. All
   tuning and model selection on development splits only.
3. NO WINNER RE-SELECTION: Never change the chosen model/policy after seeing
   holdout results. Post-hoc exploration goes in a separately labeled appendix.
4. LEAKAGE: `exposure`, `treatment`, `visit`, `conversion` are NEVER features.
   Enforce with automated tests on every feature export.
5. VERIFY, DON'T ASSUME: Checksum the download against the official SHA-256
   before ingesting. Confirm the v2.1 filename and row count (13,979,592).
6. EXPLAIN AS YOU GO: After each phase, summarize what was built and why in
   plain, interview-ready language.

## Stack
Python 3.11+, DuckDB + Parquet, Polars, LightGBM, scikit-learn, scikit-uplift,
MLflow, Streamlit, pytest, GitHub Actions.

## Workflow
- Work phase by phase from the roadmap. State the plan for each phase and wait
  for approval before coding.
- After each phase report: what was done, key numbers (with uncertainty where
  relevant), files changed, and how to verify it.
- Keep the repo reproducible: pinned dependencies, one-command rerun, no raw
  data committed (link to the official download instead).
- Maintain INTERVIEW.md: after each phase, append an interview-ready explanation
  plus the 2 toughest follow-up questions an interviewer could ask about it.
