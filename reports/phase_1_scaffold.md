# Phase 1 completion evidence

Status: content approved by user; remote publication and CI verification in progress.

## What changed and why

- Renamed uplift-AGENTS.md to AGENTS.md and recorded the approved phase-only workflow.
- Added src/marketing_uplift/, pyproject.toml, uv.lock and .python-version for a
  Python package with pinned direct and transitive dependencies.
- Added configs/project.toml with pinned source identity, visit outcome, feature
  allowlist, approved split fractions, five fixed development seeds and mlruns/.
- Added Makefile and CLI commands. Status is available; future phases return exit
  code 2 without creating data, splits, reports or runs.
- Added tests/test_scaffold.py and .github/workflows/ci.yml. Cheap checks run on
  PRs; the manual cached full-data stage remains disabled until Phases 2/3 exist.
- Added ignored data/artifact directories, README provenance/license instructions,
  docs/PHASES.md and INTERVIEW.md. Code stays MIT; data rights remain CC BY-NC-SA 4.0.

## Verification

- Locked install succeeded in both the existing environment and a newly created
  empty Python 3.12.14 environment.
- All 156 installed packages in the clean environment passed uv dependency checks.
- All 12 declared runtime dependencies imported in both environments.
- make check: lint and format passed; 10 tests passed in both environments.
- make status: reported the declared protocol and explicitly unvalidated state.
- Tests confirmed all seven reserved stages fail with no filesystem side effects.
- Git ignore checks protect raw/processed data, predictions and mlruns/ while
  allowing data/manifest.json, artifacts/splits.json and reports/data_audit.md.
- No data acquisition, split creation, model training or holdout evaluation occurred.

Run from the repository root:

```sh
make setup
make check
make status
```

uv is pinned to 0.12.23. Make uses a writable repository-local cache by default.
The GitHub Actions workflow has been configured, but has not been executed on
GitHub. Local verification used Python 3.12; the CI matrix also covers Python 3.11.
Full-data contract validation and per-export leakage gates remain Phase 3 work;
Phase 1 tests check declared configuration and command safety only.
