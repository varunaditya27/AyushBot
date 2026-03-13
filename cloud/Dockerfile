# =============================================================================
# AyushBot Cloud — Dockerfile
# =============================================================================
#
# PURPOSE:
#   Builds a Docker container image for the AyushBot cloud services,
#   targeting x86_64 architecture (standard cloud VMs). This container runs
#   the FL server, cloud API, and analytics dashboard as separate processes
#   (or as individual containers in a docker-compose setup).
#
# BASE IMAGE:
#   python:3.11-slim-bookworm (x86_64)
#
# COMPONENTS INCLUDED:
#   - Flower FL server (cloud/fl_server/)
#   - Cloud API (cloud/api/)
#   - Analytics aggregator (cloud/analytics/)
#   - Dashboard app (cloud/analytics/dashboard/)
#
# RUNTIME:
#   - Uses supervisord or a process manager to run multiple services
#   - Alternatively, use docker-compose with separate containers per service
#   - Ports:
#       8080: FL server (gRPC/TLS)
#       8443: Cloud API (HTTPS)
#       8501: Dashboard (Streamlit default)
#
# VOLUMES:
#   - /opt/ayushbot/models/: Global model weights (shared with FL server)
#   - /opt/ayushbot/certs/: TLS certificates for mTLS
#
# ENVIRONMENT VARIABLES:
#   - POSTGRES_URL: Connection string for the cloud PostgreSQL database
#   - FL_MIN_CLIENTS: Minimum gateways per FL round
#   - FL_STRATEGY: Aggregation strategy (FedAvg/FedProx/SCAFFOLD)
# =============================================================================
