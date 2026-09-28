SHELL := /bin/bash
.DEFAULT_GOAL := help

# Optional machine-specific settings (git-ignored).
-include .local.mk

STATE ?= andhra_pradesh
STORM ?= montha_2025
RUN ?=

PY := uv run --no-sync
PY_PACKAGES := -p aurora_engine -p aurora_agents -p aurora_api -p aurora_pipelines

.PHONY: help
help: ## List targets
	@grep -hE '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-16s %s\n", $$1, $$2}'

# ---------------------------------------------------------------- setup
.PHONY: setup check-tools
setup: check-tools ## Install Python and Node dependencies and git hooks
	uv sync --locked
	pnpm install --frozen-lockfile
	$(PY) pre-commit install
	@scripts/check_tools.sh --post-install

check-tools: ## Check required system tools
	@scripts/check_tools.sh

# ---------------------------------------------------------------- contracts
.PHONY: schemas
schemas: ## Generate Pydantic and TypeScript types from schemas/
	$(PY) python scripts/gen_py_types.py
	pnpm run schemas:ts

# ---------------------------------------------------------------- quality
.PHONY: test lint lint-py lint-web test-py test-web test-rules secrets
test: lint test-py test-web test-rules ## ruff, mypy, pytest, eslint, vitest, Firestore rules

lint: lint-py lint-web ## Linters and type checkers only

lint-py:
	$(PY) ruff check .
	$(PY) ruff format --check .
	$(PY) mypy $(PY_PACKAGES)

lint-web:
	pnpm --dir apps/web lint --max-warnings=0
	pnpm --dir apps/web typecheck

test-py:
	$(PY) pytest

test-web:
	pnpm --dir apps/web test

test-rules:
	@if [ -f infra/firestore.rules ]; then \
		pnpm exec firebase emulators:exec --only firestore "pnpm --dir apps/web test:rules"; \
	else echo "test-rules: no infra/firestore.rules yet (task 4.3); skipped"; fi

secrets: ## Scan the working tree and history for secrets
	gitleaks git --no-banner --redact .
	gitleaks dir --no-banner --redact --config .gitleaks.toml .

# ---------------------------------------------------------------- data and engine
.PHONY: download graph replay tiles validate eval publish sandbox-reset
download: ## Approval-free raw downloads (task 1.4a)
	pipelines/downloads/fetch_raw.sh

graph: ## Build the lifeline graph for STATE
	$(PY) python -m aurora_pipelines.build_graph --state $(STATE)

replay: ## Run the storm pipeline for STORM
	$(PY) python -m aurora_pipelines.storm_run --storm $(STORM)

tiles: ## Build MVT tiles and scenario JSON for STORM
	$(PY) python -m aurora_pipelines.tiles --storm $(STORM)

validate: ## Sentinel-1 road skill, baselines and surge table for STORM
	$(PY) python -m aurora_pipelines.backtest --storm $(STORM)

eval: ## Agent evaluation sets -> docs/eval-results.md
	$(PY) python -m aurora_agents.evaluate

publish: ## Load local run outputs to BigQuery, Cloud Storage and Firestore
	@test -n "$(RUN)" || (echo "usage: make publish RUN=<run_id>" && exit 2)
	$(PY) python -m aurora_pipelines.publish --run $(RUN)

sandbox-reset: ## Reset the demo-officer sandbox storm
	$(PY) python -m aurora_pipelines.sandbox_reset

# ---------------------------------------------------------------- web and deploy
.PHONY: web deploy-api deploy-web deploy-jobs
web: ## Run the web app locally
	pnpm --dir apps/web dev

deploy-web: ## Static export and deploy to Firebase Hosting
	pnpm --dir apps/web build
	pnpm exec firebase deploy --only hosting

deploy-api: ## Deploy the API to Cloud Run
	gcloud run deploy aurora-api --source services/api --region asia-south1 \
		--memory 2Gi --max-instances 10 --concurrency 80

deploy-jobs: ## Deploy the pipeline jobs to Cloud Run
	@echo "deploy-jobs: defined in task 1.2 once the Cloud project exists" && exit 1
