# =============================================================================
# AyushBot Backend — FastAPI Application Entry Point
# =============================================================================
#
# PURPOSE:
#   Creates and configures the FastAPI application instance that serves as
#   the HTTP interface on the PHC gateway (Raspberry Pi 4). This is the
#   process that the Android app communicates with over the local Wi-Fi
#   network at the PHC.
#
# APPLICATION LIFECYCLE:
#
#   Startup (on_startup event):
#     1. Load configuration from config.yaml
#     2. Initialize the SQLite database connection (via db/session.py)
#     3. Load the XGBoost triage model (for Agent 1)
#     4. Load the RAG pipeline (FAISS index, BM25 index, bi-encoder, reranker)
#     5. Load the LLM model (Phi-3 Mini or Gemma-3 via llm/loader.py)
#     6. Load language models (IndicBERT, IndicTrans2 via Agent 5 dependencies)
#     7. Initialize the LangGraph orchestrator with all agents
#     8. Start the FL background scheduler (Agent 4)
#     9. Log total startup time and memory usage
#
#   Shutdown (on_shutdown event):
#     1. Flush any pending FL gradient updates to disk
#     2. Close the database connection pool
#     3. Unload models to free memory
#     4. Log shutdown confirmation
#
# ROUTE REGISTRATION:
#   The app registers the following routers:
#     - /api/v1/triage — Patient assessment endpoints (routes/triage.py)
#     - /api/v1/sync — Data sync endpoints for ASHA phones (routes/sync.py)
#     - /api/v1/health — Gateway health/status endpoints (routes/health.py)
#
# MIDDLEWARE STACK:
#   Applied in order (outermost first):
#     1. CORS middleware — Allow requests from the local Android app
#     2. Rate limiter — Prevent abuse (routes/middleware/rate_limiter.py)
#     3. Request logging — Structured JSON logging for every request
#     4. Error handler — Catch unhandled exceptions, return safe 500 responses
#
# SECURITY:
#   The API runs on the PHC's LOCAL network only (not exposed to the internet).
#   Security layers:
#     - HTTPS with self-signed certificates (generated during RPi setup)
#     - API key authentication (shared secret between Android app and gateway)
#     - Rate limiting to prevent accidental DoS from buggy app versions
#     - Input validation via Pydantic schemas on all request bodies
#
# DEPLOYMENT:
#   Run via Uvicorn ASGI server:
#     uvicorn backend.api.main:app --host 0.0.0.0 --port 8443 --ssl-keyfile ...
#   Or via the Docker container (see backend/Dockerfile).
#
# CONFIGURATION:
#   All API settings (host, port, cors_origins, rate_limit, etc.) are loaded
#   from the "api" section of config.yaml.
# =============================================================================
