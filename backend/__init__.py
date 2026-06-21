# =============================================================================
# AyushBot Backend — Root Package
# =============================================================================
#
# The backend package is a Python application deployed on the PHC gateway host.
# ESP32 boards act as sensor clients that send telemetry into this service; they
# do not run the Python backend. The package contains:
#
#   agents/     — Five specialized clinical agents + LangGraph orchestrator
#   rag/        — EdgeRAG retrieval pipeline (chunker, embedder, indexer, retriever, reranker)
#   llm/        — Quantized LLM management (Phi-3 Mini / Gemma-3 1B)
#   fl/         — Federated learning client (Flower + differential privacy)
#   api/        — FastAPI HTTP interface for the Android app
#   db/         — SQLite database (SQLAlchemy ORM + Alembic migrations)
#   security/   — Authentication, certificates, MQTT broker security
#
# Entry point: backend.api.main (FastAPI app)
# CLI tools:   backend.rag.build_index (offline RAG index builder)
# =============================================================================
