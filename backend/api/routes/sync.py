# =============================================================================
# AyushBot Backend — API Route: Sync Endpoints
# =============================================================================
#
# PURPOSE:
#   Handles data synchronization between ASHA Android phones and the PHC
#   gateway. When an ASHA arrives at the PHC with her phone, these endpoints
#   manage the bidirectional data exchange over the local Wi-Fi network.
#
# ENDPOINTS:
#
#   POST /api/v1/sync/upload
#     ASHA phone → Gateway: Upload offline encounter data.
#     When ASHAs collect data in the field without gateway connectivity,
#     the Android app stores encounters locally. When the ASHA returns to
#     the PHC, this endpoint receives the queued data.
#     - Request body: list of PatientAssessment objects + BLE sensor readings
#     - Response: count of accepted records + list of any rejected records
#       (with rejection reasons)
#     - Deduplication: If the same encounter_id already exists, skip it
#
#   GET /api/v1/sync/download
#     Gateway → ASHA phone: Download updated models and reference data.
#     - Returns a manifest of available updates:
#       - model_updates: list of updated model files with version + checksum
#       - reference_data: updated drug formulary, facility list, etc.
#       - asha_messages: administrative messages from the PHC Medical Officer
#     - The Android app downloads individual files via separate GET calls
#
#   GET /api/v1/sync/download/{resource_id}
#     Download a specific resource file (model binary, reference data file).
#     - Streams the file with Content-Length and checksum headers
#     - Supports range requests for resumable downloads
#
#   POST /api/v1/sync/feedback
#     Upload outcome feedback from the PHC Medical Officer.
#     After a referred patient is seen by the doctor, the doctor can provide
#     feedback on the triage accuracy (confirmed/modified diagnosis). This
#     feedback replaces pseudo-labels in the FL training pipeline.
#     - Request body: encounter_id + confirmed_diagnosis + doctor_notes
#
# SYNC PROTOCOL:
#   The Android app discovers the gateway via mDNS on the local network.
#   Sync is initiated by the phone, not the gateway. The phone first
#   uploads pending data, then checks for available downloads.
#
# CONFLICT RESOLUTION:
#   If the same patient has data from both offline phone storage and a
#   previous gateway sync, the NEWER timestamp wins. Conflicts are logged
#   for manual review by the Medical Officer.
# =============================================================================

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.db import crud
from backend.db.session import get_db
from backend.security.auth import AuthUser, Role, require_roles

router = APIRouter()


class PatientPayload(BaseModel):
	id: str
	abha_id: Optional[str] = None
	name: Optional[str] = None
	age_months: int
	sex: str
	village: Optional[str] = None
	asha_id: str
	created_at: Optional[int] = None


class CasePayload(BaseModel):
	id: str
	patient_id: str
	timestamp: Optional[int] = None
	spo2: Optional[float] = None
	heart_rate: Optional[float] = None
	temperature: Optional[float] = None
	weight: Optional[float] = None
	symptoms: str = "[]"
	risk_tier: str = "LOW"
	sync_status: str = "PENDING"


class RecommendationPayload(BaseModel):
	id: str
	case_id: str
	primary_diagnosis: str
	confidence: str = "Low"
	differential_json: str = "[]"
	action_plan: str = ""
	referral_facility: Optional[str] = None
	drug_dosage: Optional[str] = None
	counseling: Optional[str] = None
	citation_source: Optional[str] = None
	citation_text: Optional[str] = None
	created_at: Optional[int] = None


class SyncRecord(BaseModel):
	patient: PatientPayload
	case: CasePayload
	recommendation: Optional[RecommendationPayload] = None


class SyncBatchRequest(BaseModel):
	records: List[SyncRecord] = Field(default_factory=list)


class SyncBatchResponse(BaseModel):
	accepted: int
	rejected: List[dict]


def _merge_updates(payload: BaseModel) -> dict:
	return payload.model_dump(exclude_none=True)


@router.post("", response_model=SyncBatchResponse, status_code=status.HTTP_200_OK)
async def sync_batch(
	batch: SyncBatchRequest,
	db: Session = Depends(get_db),
	_user: AuthUser = Depends(require_roles([Role.ASHA_WORKER, Role.MEDICAL_OFFICER])),
):
	if not batch.records:
		raise HTTPException(
			status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
			detail="No records provided",
		)

	accepted = 0
	rejected: List[dict] = []

	for record in batch.records:
		try:
			with db.begin_nested():
				patient_payload = record.patient
				case_payload = record.case
				rec_payload = record.recommendation

				patient = crud.get_patient(db, patient_payload.id)
				if patient:
					crud.update_patient(db, patient.id, _merge_updates(patient_payload))
				else:
					crud.create_patient(db, _merge_updates(patient_payload))

				case = crud.get_case(db, case_payload.id)
				if case:
					crud.update_case(db, case.id, _merge_updates(case_payload))
				else:
					crud.create_case(db, _merge_updates(case_payload))

				if rec_payload:
					existing = crud.get_recommendation_by_case(db, rec_payload.case_id)
					if existing:
						crud.update_recommendation(
							db, existing.id, _merge_updates(rec_payload)
						)
					else:
						crud.create_recommendation(db, _merge_updates(rec_payload))

			accepted += 1
		except Exception as exc:
			rejected.append(
				{
					"patient_id": record.patient.id,
					"case_id": record.case.id,
					"reason": str(exc),
				}
			)

	return SyncBatchResponse(accepted=accepted, rejected=rejected)
