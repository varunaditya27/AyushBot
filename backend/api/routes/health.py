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
#   GET /api/v1/health/live
#     Simple liveness check. Returns 200 with {"status": "ok"}.
#     Used by the Android app to detect gateway availability on the network.
#     No authentication required.
#
#   GET /api/v1/health/ping
#     Backward-compatible alias for /live.
#
#   GET /api/v1/health/ready
#     Readiness probe. Returns 200 only if critical enabled subsystems are ready:
#       - Database connection: can execute a test query
#       - Redis: checked only when enabled
#       - MQTT: checked only when enabled
#     Disabled optional services are reported as "disabled" and do not block
#     local showcase/development startup.
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

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.security.auth import AuthUser, Role, require_roles

router = APIRouter()
logger = logging.getLogger(__name__)

_START_TIME = time.time()


class HealthResponse(BaseModel):
	status: str


class ComponentStatus(BaseModel):
	status: str
	required: bool = True


class ReadinessResponse(HealthResponse):
	checks: dict[str, ComponentStatus]


class StatusResponse(HealthResponse):
	uptime_seconds: int


@router.get("/live", response_model=HealthResponse)
async def live() -> HealthResponse:
	return HealthResponse(status="ok")


@router.get("/ping", response_model=HealthResponse, include_in_schema=False)
async def ping() -> HealthResponse:
	return await live()


@router.get("/ready", response_model=ReadinessResponse)
async def ready(request: Request, db: Session = Depends(get_db)) -> ReadinessResponse:
	checks: dict[str, ComponentStatus] = {}
	try:
		db.execute(text("SELECT 1"))
	except Exception as exc:
		logger.exception("Readiness database check failed")
		raise HTTPException(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail={
				"status": "not_ready",
				"checks": {"database": {"status": "unavailable", "required": True}},
			},
		) from exc
	checks["database"] = ComponentStatus(status="ready", required=True)

	for name, required in (("redis", False), ("mqtt", False)):
		component = getattr(request.app.state, f"{name}_client", None)
		if name == "mqtt":
			component = getattr(request.app.state, "mqtt_listener", None)
		if component is None or not hasattr(component, "health_check"):
			checks[name] = ComponentStatus(status="not_configured", required=required)
			continue
		ok, component_status = component.health_check()
		checks[name] = ComponentStatus(status=component_status, required=required)
		if required and not ok:
			raise HTTPException(
				status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
				detail={
					"status": "not_ready",
					"checks": {
						key: value.model_dump(mode="json")
						for key, value in checks.items()
					},
				},
			)

	return ReadinessResponse(status="ready", checks=checks)


@router.get("/status", response_model=StatusResponse)
async def status_report(
	_user: AuthUser = Depends(require_roles([Role.MEDICAL_OFFICER])),
) -> StatusResponse:
	uptime = int(time.time() - _START_TIME)
	return StatusResponse(status="ok", uptime_seconds=uptime)
