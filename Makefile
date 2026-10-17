PY ?= python

.PHONY: help run openapi data data-dry data-check data-sync adzuna check lint test secrets

help:
	@echo "make run         start the API on :8000 with reload"
	@echo "make openapi     export docs/openapi.json for the frontend client"
	@echo "make data        fetch scripted sources (ONS crosswalks, ASHE 2011-2025, Nomis defs)"
	@echo "make data-dry    show what would be fetched"
	@echo "make data-check  check data/manifest.yaml against data/raw, write checksums"
	@echo "make data-sync   rsync data/raw and snapshots to the cluster (needs .env)"
	@echo "make adzuna      take a dated Adzuna snapshot (laptop, keys in .env)"
	@echo "make check       lint + tests + secret scan, run before every push"

run:
	$(PY) -m uvicorn avenir_api.app:app --reload --port 8000

openapi:
	$(PY) -m avenir_api.export_openapi

data:
	$(PY) scripts/fetch/ons_files.py
	$(PY) scripts/fetch/ons_ashe.py --years 2011-2025
	$(PY) scripts/fetch/nomis_aps.py NM_218_1 --describe
	$(PY) scripts/fetch/nomis_aps.py NM_168_1 --describe
	@echo "Next: browser downloads for ESCO, ILO WP140 and Occupations in Demand (see data/manifest.yaml),"
	@echo "then the Nomis data pulls with the dimension codes printed above."

data-dry:
	$(PY) scripts/fetch/ons_files.py --dry-run
	$(PY) scripts/fetch/adzuna_snapshot.py --dry-run
	$(PY) scripts/fetch/nomis_aps.py NM_218_1 --dry-run

data-check:
	$(PY) scripts/fetch/check_manifest.py

data-sync:
	bash scripts/sync_to_cluster.sh

adzuna:
	$(PY) scripts/fetch/adzuna_snapshot.py

lint:
	ruff check .

test:
	@if ls packages/*/tests services/*/tests 2>/dev/null | grep -q .; then pytest -q; else echo "no tests yet"; fi

secrets:
	@command -v gitleaks >/dev/null && gitleaks detect --no-banner --redact || echo "gitleaks not installed; pre-commit runs it"

check: lint test secrets
