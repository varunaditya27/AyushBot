# =============================================================================
# AyushBot Backend — Dockerfile
# =============================================================================
#
# PURPOSE:
#   Builds a Docker container image for the AyushBot backend service,
#   targeting ARM64 architecture (Raspberry Pi 4). The container runs the
#   FastAPI application, all agents, the RAG pipeline, the LLM, and the
#   FL background scheduler.
#
# BASE IMAGE:
#   python:3.11-slim-bookworm (Debian-based, ARM64 compatible)
#   Chosen for minimal size while including the system libraries needed
#   by numpy, faiss-cpu, and llama-cpp-python.
#
# BUILD STAGES:
#
#   Stage 1 — System Dependencies
#     Install OS packages required by native Python extensions:
#       - libopenblas-dev (for numpy/faiss on ARM64)
#       - libffi-dev (for cryptography package)
#       - build-essential (for compiling C extensions)
#
#   Stage 2 — Python Dependencies
#     Copy requirements.txt and install all Python packages:
#       - fastapi, uvicorn, pydantic (API framework)
#       - sqlalchemy, alembic (database ORM + migrations)
#       - sentence-transformers (bi-encoder + cross-encoder models)
#       - faiss-cpu (vector index)
#       - rank-bm25 (sparse retrieval)
#       - llama-cpp-python (LLM inference)
#       - flwr (Flower FL client)
#       - jinja2 (prompt templates)
#       - pyyaml (config loading)
#       - numpy, scipy, scikit-learn, xgboost
#     Use --no-cache-dir to minimize image size.
#
#   Stage 3 — Application Code
#     Copy the backend/ source code into the container.
#     Do NOT copy models or data — these are mounted as Docker volumes
#     at runtime (they're too large for the image and vary per deployment).
#
# RUNTIME:
#   - Entrypoint: uvicorn backend.api.main:app --host 0.0.0.0 --port 8443
#   - Volumes:
#       /opt/ayushbot/models/ — Pre-downloaded model files (LLM, embedders, etc.)
#       /opt/ayushbot/data/   — SQLite database + RAG index files
#   - Ports: 8443 (HTTPS API)
#   - Health check: curl -f https://localhost:8443/api/v1/health/ping
#
# SIZE OPTIMIZATION:
#   Target: < 2 GB image (challenging due to ML dependencies on ARM64)
#   Strategies: multi-stage build, apt clean, pip --no-cache-dir,
#   exclude dev dependencies, .dockerignore for tests/docs/research.
#
# ARM64 NOTES:
#   Some Python packages (faiss-cpu, llama-cpp-python) require compilation
#   from source on ARM64. The Dockerfile handles this with appropriate
#   build flags and may need cross-compilation support if building on x86.
# =============================================================================
