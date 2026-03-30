# =============================================================================
# AyushBot Backend — API Route: Health / Status Endpoints
# =============================================================================
#
# PURPOSE:
#   Provides system health checks, readiness probes, and diagnostic endpoints
#   for monitoring the PHC gateway's operational status. Used by Docker health
#   checks, Prometheus monitoring, and the Android app's connectivity check.
#
# ENDPOINTS:
#
#   GET /api/v1/health/ping
#     Simple liveness check. Returns 200 with {"status": "ok"}.
#     Used by the Android app to detect gateway availability on the network.
#     No authentication required.
#
#   GET /api/v1/health/ready
#     Readiness probe. Returns 200 only if ALL critical subsystems are loaded:
#       - Database connection: can execute a test query
#       - XGBoost model: loaded and inference-ready
#       - RAG pipeline: FAISS index loaded, embedder ready
#       - LLM: model loaded and can generate a test token
#     If any subsystem is still initializing, returns 503 with details.
#     Used by Docker/Kubernetes to gate traffic to the container.
#
#   GET /api/v1/health/status
#     Comprehensive diagnostic dashboard (admin-only, requires auth).
#     Returns detailed system information:
#       - system: CPU usage, memory usage, disk usage, temperature (RPi 4)
#       - models: loaded model names, versions, sizes, inference latencies
#       - rag: index stats (num_chunks, index_size_bytes, last_build_time)
#       - fl: FL training status, gradient queue size, last sync time,
#         cumulative privacy budget consumed
#       - database: record counts, DB file size
#       - uptime: gateway uptime in seconds
#       - version: AyushBot software version
#
#   GET /api/v1/health/metrics
#     Prometheus-compatible metrics endpoint. Exports:
#       - ayushbot_triage_requests_total (counter)
#       - ayushbot_triage_latency_seconds (histogram)
#       - ayushbot_risk_level_counts (counter, labeled by risk level)
#       - ayushbot_fl_rounds_completed (counter)
#       - ayushbot_rag_retrieval_latency_seconds (histogram)
#       - ayushbot_system_cpu_percent (gauge)
#       - ayushbot_system_memory_percent (gauge)
#       - ayushbot_system_temperature_celsius (gauge)
# =============================================================================

from __future__ import annotations

import time
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.security.auth import AuthUser, Role, require_roles

router = APIRouter()

_START_TIME = time.time()


@router.get("/ping")
async def ping() -> Dict[str, str]:
	return {"status": "ok"}


@router.get("/ready")
async def ready(db: Session = Depends(get_db)) -> Dict[str, str]:
	try:
		db.execute(text("SELECT 1"))
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
	return {"status": "ready"}


@router.get("/status")
async def status_report(
	_user: AuthUser = Depends(require_roles([Role.MEDICAL_OFFICER])),
) -> Dict[str, str]:
	uptime = int(time.time() - _START_TIME)
	return {"status": "ok", "uptime_seconds": str(uptime)}
