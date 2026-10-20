UV ?= uv
# Keep setup usable in workspaces with a read-only home directory.
export UV_CACHE_DIR ?= $(CURDIR)/.cache/uv

.PHONY: setup check status acquire validate ingest split audit ate baselines advanced decisions final-prepare reproduce portfolio
setup:
	$(UV) sync --locked

check:
	$(UV) run --locked ruff check .
	$(UV) run --locked ruff format --check .
	$(UV) run --locked pytest -m "not full_data"

status:
	$(UV) run --locked uplift status

# Presentation only: saved aggregates; no dataset/model/Stage B interfaces.
portfolio:
	$(UV) run --locked python -m portfolio

validate:
	$(UV) run --locked uplift validate --full

acquire ingest split audit ate baselines advanced decisions final-prepare:
	$(UV) run --locked uplift $@

# Reproduce approved stages through development baselines; no final holdout evaluation.
# Later stages must reuse sealed memberships; never regenerate them on a rerun.
reproduce:
	$(UV) run --locked uplift acquire
	$(UV) run --locked uplift validate --full
	$(UV) run --locked uplift ingest
	$(UV) run --locked uplift split
	$(UV) run --locked uplift audit
	$(UV) run --locked uplift ate
	$(UV) run --locked uplift baselines
