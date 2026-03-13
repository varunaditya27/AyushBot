# =============================================================================
# AyushBot — Makefile
# =============================================================================
#
# PURPOSE:
#   Convenience targets for common development and deployment tasks.
#   Provides a single entry point for building, testing, deploying, and
#   managing the AyushBot system across all components.
#
# TARGETS:
#
#   --- Setup ---
#
#   make install
#     Install Python dependencies from backend/requirements.txt into a venv.
#     Creates .venv/ if it doesn't exist.
#
#   make install-dev
#     Install development dependencies (pytest, black, ruff, mypy, pre-commit).
#
#   --- Backend ---
#
#   make run-backend
#     Start the FastAPI backend server locally (development mode with reload).
#     Command: uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
#
#   make build-rag-index
#     Run the RAG pipeline to build/rebuild the FAISS vector index from
#     the PDF corpus. Command: python -m backend.rag.build_index
#
#   --- ML Training ---
#
#   make train-triage
#     Run the full triage classifier training pipeline (Steps 1-6).
#     Command: for each step in ml/triage_classifier/0*.py, run sequentially.
#
#   make train-language
#     Train the intent classifier and NER models.
#
#   make run-fl-simulation
#     Run all FL simulation experiments (FedAvg, FedProx, SCAFFOLD, Byzantine).
#
#   --- Testing ---
#
#   make test
#     Run all unit tests. Command: pytest tests/unit/ -v
#
#   make test-integration
#     Run integration tests (requires Docker for MQTT broker).
#     Command: pytest tests/integration/ -v
#
#   make test-all
#     Run unit + integration tests. Command: pytest tests/ -v --ignore=tests/simulation
#
#   make test-simulation
#     Run ASHA scenario simulations (slow, requires real models).
#     Command: pytest tests/simulation/ -v -m simulation
#
#   --- Code Quality ---
#
#   make lint
#     Run ruff linter on all Python code. Command: ruff check .
#
#   make format
#     Format all Python code with black. Command: black .
#
#   make typecheck
#     Run mypy type checking. Command: mypy backend/ --ignore-missing-imports
#
#   --- Infrastructure ---
#
#   make docker-up
#     Build and start all Docker containers (development mode).
#     Command: docker compose -f infra/docker-compose.yml up --build
#
#   make docker-up-prod
#     Start Docker containers with production overrides.
#     Command: docker compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml up -d
#
#   make docker-down
#     Stop all Docker containers.
#
#   make gen-certs
#     Generate TLS certificates. Command: bash infra/certs/generate_certs.sh
#
#   --- Firmware ---
#
#   make firmware-build
#     Build the Arduino sensor pack firmware using PlatformIO.
#     Command: cd firmware/sensor_pack && pio run
#
#   make firmware-upload
#     Build and upload firmware to Arduino via USB.
#     Command: cd firmware/sensor_pack && pio run --target upload
#
#   --- Cleanup ---
#
#   make clean
#     Remove __pycache__, .pytest_cache, build artifacts.
#
#   make clean-data
#     Remove all processed data and model artifacts (retains raw data).
# =============================================================================
