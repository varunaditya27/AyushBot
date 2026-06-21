PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: install install-dev run-backend test test-all lint build-rag-index migrate-db seed-db bootstrap-admin demo-showcase

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip
	$(BIN)/python -m pip install -r backend/requirements.txt

install-dev:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip
	$(BIN)/python -m pip install -e ".[dev,ai]"

run-backend:
	$(BIN)/python -m uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000

test:
	$(BIN)/python -m pytest tests/unit

test-all:
	$(BIN)/python -m pytest tests --ignore=tests/simulation

lint:
	$(BIN)/python -m ruff check backend tests

build-rag-index:
	$(BIN)/python -m backend.rag.build_index

migrate-db:
	$(BIN)/python -m backend.db.migrate upgrade

seed-db:
	$(BIN)/python -m backend.db.seed --villages data/reference/villages.json --facilities data/reference/facilities.csv

bootstrap-admin:
	$(BIN)/python -m backend.security.bootstrap --user-id medical-officer-1 --username medical-officer

demo-showcase:
	@$(BIN)/python -m backend.demo.run_showcase
