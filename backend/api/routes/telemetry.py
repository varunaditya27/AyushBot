"""AyushBot Backend — API Route: Telemetry Endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from backend.security.auth import Role, AuthUser, require_roles

router = APIRouter()


class TelemetryPayload(BaseModel):
    device_id: str = Field(..., min_length=1)
    case_id: Optional[str] = None
    timestamp: Optional[int] = None
    readings: Dict[str, Any] = Field(default_factory=dict)

    def normalized(self) -> Dict[str, Any]:
        ts = self.timestamp or int(datetime.utcnow().timestamp() * 1000)
        return {
            "device_id": self.device_id,
            "case_id": self.case_id,
            "timestamp": ts,
            "readings": self.readings,
        }


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def ingest_telemetry(
    payload: TelemetryPayload,
    request: Request,
    _user: AuthUser = Depends(require_roles([Role.ASHA_WORKER, Role.MEDICAL_OFFICER])),
):
    redis_client = getattr(request.app.state, "redis_client", None)
    if not redis_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telemetry queue unavailable",
        )
    try:
        redis_client.push_telemetry(payload.normalized())
        return {"status": "accepted"}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
