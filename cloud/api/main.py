# =============================================================================
# AyushBot Cloud — Cloud API Entry Point
# =============================================================================
#
# PURPOSE:
#   FastAPI application for the cloud service. Unlike the backend API (which
#   runs on the RPi 4 gateway), this API runs in the cloud and serves two
#   primary functions:
#
#   1. FL Coordination API
#      Administrative endpoints for managing the FL training process:
#        POST /api/v1/fl/trigger-round    — Manually trigger an FL round
#        GET  /api/v1/fl/rounds           — List FL round history
#        GET  /api/v1/fl/rounds/{id}      — Get details of a specific round
#        GET  /api/v1/fl/models           — List model registry entries
#        POST /api/v1/fl/rollback/{id}    — Roll back to a specific model version
#
#   2. Statistics Ingestion API
#      Endpoints for receiving anonymized aggregate stats from gateways:
#        POST /api/v1/stats/ingest        — Upload statistics summary
#        GET  /api/v1/stats/national      — Get national aggregated stats
#        GET  /api/v1/stats/district/{id} — Get district-level stats
#
#   3. Gateway Management API
#      Endpoints for managing the PHC gateway fleet:
#        GET  /api/v1/gateways            — List all registered gateways
#        GET  /api/v1/gateways/{id}       — Get gateway status and details
#        POST /api/v1/gateways/register   — Register a new PHC gateway
#        POST /api/v1/gateways/{id}/cert  — Issue a new client certificate
#
# AUTHENTICATION:
#   - Gateway-to-cloud: mTLS (client certificates issued during registration)
#   - Admin-to-cloud: API key or OAuth2 (for dashboard and management APIs)
#
# DEPLOYMENT:
#   Runs as a Docker container in the cloud (separate from FL server container).
#   Both containers share the same PostgreSQL database and model storage.
# =============================================================================
