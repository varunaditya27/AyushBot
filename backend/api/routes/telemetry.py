"""AyushBot Backend — API Route: Telemetry Endpoints."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend.db import crud
from backend.db.models import DeviceStatus
from backend.db.session import get_db
from backend.security.auth import AuthUser, Role, require_case_access, require_roles

router = APIRouter()
logger = logging.getLogger(__name__)


class TelemetryPayload(BaseModel):
	model_config = ConfigDict(extra="forbid")

	event_id: str = Field(default_factory=lambda: str(uuid.uuid4()), max_length=64)
	device_id: str = Field(..., min_length=1, max_length=64)
	case_id: str | None = Field(default=None, max_length=64)
	event_type: str = Field(default="vitals", min_length=1, max_length=64)
	timestamp: int | None = Field(default=None, ge=0)
	readings: dict[str, Any] = Field(default_factory=dict)

	def normalized(self) -> dict[str, Any]:
		return {
			"id": self.event_id,
			"device_id": self.device_id,
			"case_id": self.case_id,
			"event_type": self.event_type,
			"timestamp": self.timestamp
			or int(datetime.now(UTC).timestamp() * 1000),
			"readings": self.readings,
		}


class TelemetryAccepted(BaseModel):
	event_id: str
	status: str
	persisted: bool


@router.post(
	"",
	status_code=status.HTTP_202_ACCEPTED,
	response_model=TelemetryAccepted,
)
async def ingest_telemetry(
	payload: TelemetryPayload,
	db: Session = Depends(get_db),
	user: AuthUser = Depends(require_roles([Role.ASHA_WORKER, Role.MEDICAL_OFFICER])),
):
	device = crud.get_device(db, payload.device_id)
	if not device or device.status != DeviceStatus.ACTIVE:
		raise HTTPException(status_code=404, detail="Device not found")
	if user.role == Role.ASHA_WORKER and device.owner_id != user.user_id:
		raise HTTPException(status_code=403, detail="Access denied")
	if payload.case_id:
		require_case_access(db, user, payload.case_id)
	try:
		existing = crud.get_telemetry_event(db, payload.event_id)
		if existing:
			return TelemetryAccepted(
				event_id=existing.id, status="duplicate", persisted=True
			)
		event = crud.create_telemetry_event(db, payload.normalized())
		db.commit()
		return TelemetryAccepted(
			event_id=event.id, status="accepted", persisted=True
		)
	except Exception as exc:
		logger.exception("Telemetry ingestion failed")
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Internal server error",
		) from exc
