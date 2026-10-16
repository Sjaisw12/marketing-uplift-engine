UV ?= uv
# Keep setup usable in workspaces with a read-only home directory.
export UV_CACHE_DIR ?= $(CURDIR)/.cache/uv

.PHONY: setup check status acquire validate ingest split audit ate baselines reproduce
setup:
	$(UV) sync --locked

check:
	$(UV) run --locked ruff check .
	$(UV) run --locked ruff format --check .
	$(UV) run --locked pytest -m "not full_data"

status:
	$(UV) run --locked uplift status

validate:
	$(UV) run --locked uplift validate --full

acquire ingest split audit ate baselines:
	$(UV) run --locked uplift $@

# This command stops at ATE until Phase 5 is implemented and approved.
# Later stages must reuse sealed memberships; never regenerate them on a rerun.
reproduce:
	$(UV) run --locked uplift acquire
	$(UV) run --locked uplift validate --full
	$(UV) run --locked uplift ingest
	$(UV) run --locked uplift split
	$(UV) run --locked uplift audit
	$(UV) run --locked uplift ate
	$(UV) run --locked uplift baselines
