PYTHON ?= python3
.PHONY: verify scan validate figures tables reproduce-public reproduce-full
verify:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) reproducibility/verify_reported_results.py
scan:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) reproducibility/validate_artifact.py --scan-only
validate:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) reproducibility/validate_artifact.py
figures:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) reproducibility/regenerate_assets.py --figures
tables:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) reproducibility/regenerate_assets.py --tables
reproduce-public:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) reproducibility/reproduction_paths.py public
reproduce-full:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) reproducibility/reproduction_paths.py full

.PHONY: paper aggregate-audits
paper:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) reproducibility/build_manuscript.py
aggregate-audits:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) reproducibility/audit_aggregate_records.py
