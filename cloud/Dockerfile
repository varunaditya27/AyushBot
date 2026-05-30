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

# Stage 1: Builder
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY cloud/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim-bookworm

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 ayushbot

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/ayushbot/.local

# Copy application code
COPY cloud/ /app/

# Set environment variables
ENV PATH=/home/ayushbot/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AYUSHBOT_ENV=production

# Create necessary directories
RUN mkdir -p /app/logs /app/models /app/certs \
    && chown -R ayushbot:ayushbot /app

# Switch to non-root user
USER ayushbot

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default entry point (can be overridden at runtime)
ENTRYPOINT ["python"]
CMD ["-m", "fl_server.server", "--port", "8080"]

# Expose ports
EXPOSE 8080 8443 8501 9090
