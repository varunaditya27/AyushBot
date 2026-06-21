# =============================================================================
# AyushBot Backend — API Route: Triage Endpoints
# =============================================================================
#
# PURPOSE:
#   Defines the core patient assessment API endpoints. These are the primary
#   endpoints that the ASHA's Android app calls to run a triage.
#
# ENDPOINTS:
#
#   POST /api/v1/triage/assess
#     The main triage endpoint. Accepts a PatientAssessment request body
#     and returns a complete triage result.
#     - Request body: PatientAssessment schema (from agents/schemas/)
#     - Invokes the LangGraph orchestrator to run all agents
#     - Response: TriageResult containing:
#       - risk_level: LOW / MEDIUM / HIGH / CRITICAL
#       - differential_diagnosis: ranked conditions with citations
#       - action_plan: referral + medications + instructions
#       - asha_output_text: translated response in local language
#       - asha_output_audio_url: URL to download TTS audio (if generated)
#     - Latency target: < 1 second end-to-end
#     - HTTP 200 on success
#     - HTTP 422 on validation error (bad request body)
#     - HTTP 500 on internal pipeline failure (with safe error message)
#
#   GET /api/v1/triage/history/{patient_id}
#     Retrieves the triage history for a specific patient.
#     - Returns a list of past TriageResult objects ordered by timestamp
#     - Used by the ASHA to review previous visits
#     - Paginated: ?page=1&per_page=10
#
#   GET /api/v1/triage/encounter/{encounter_id}
#     Retrieves a single triage encounter by its unique ID.
#     - Returns the full TriageResult including agent execution metadata
#     - Used for auditing and debugging
#
# REQUEST FLOW:
#   POST /assess → Validate input → Orchestrator → Agents 5→1→2→3→5 → Store
#   in DB → Return response
#
# ERROR HANDLING:
#   - Validation errors: Return 422 with field-level error details
#   - Agent failures: Return 200 with degraded response (fallback messages)
#   - Database errors: Return 500 with generic "Internal error" message
#   - Never expose internal stack traces or model details in error responses
# =============================================================================

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend.agents.orchestrator import run_pipeline
from backend.agents.schemas.patient_assessment import PatientAssessment
from backend.agents.state import state_from_assessment
from backend.db import crud
from backend.db.session import get_db
from backend.security.auth import (
	AuthUser,
	Role,
	require_case_access,
	require_patient_access,
	require_roles,
)

router = APIRouter()
logger = logging.getLogger(__name__)


class ContractModel(BaseModel):
	model_config = ConfigDict(extra="forbid")


class TriageResult(ContractModel):
	request_id: str
	risk_level: Optional[str] = None
	risk_confidence: Optional[float] = None
	differential_diagnosis: Optional[Dict] = None
	action_plan: Optional[Dict] = None
	asha_output_text: Optional[str] = None
	created_at: str
	ruleset_version: str | None = None
	growth_reference_version: str | None = None
	triage_model_version: str | None = None


class HistoryItem(ContractModel):
	id: str
	patient_id: str
	timestamp: int
	risk_tier: str
	risk_explanation: dict[str, Any] | list[Any]
	symptoms: list[Any] | dict[str, Any]
	spo2: float | None
	heart_rate: float | None
	temperature: float | None
	version: int
	updated_at: int
	ruleset_version: str | None
	growth_reference_version: str | None
	triage_model_version: str | None


class HistoryPage(ContractModel):
	items: list[HistoryItem]
	page: int
	page_size: int
	total: int
	total_pages: int


class RecommendationResponse(ContractModel):
	id: str
	primary_diagnosis: str
	confidence: str
	differential_diagnosis: list[Any] | dict[str, Any]
	action_plan: list[Any] | dict[str, Any] | str
	citations: list[Any] | dict[str, Any]
	referral_facility: str | None
	counseling: str | None
	version: int
	updated_at: int


class EncounterResponse(ContractModel):
	case: HistoryItem
	recommendation: RecommendationResponse | None
	errors: list[Any] | dict[str, Any] = Field(default_factory=list)


def _persist_state(db: Session, state: Dict) -> None:
	patient_id = state.get("patient_id") or str(uuid.uuid4())
	if not state.get("patient_id"):
		state["patient_id"] = patient_id
	patient_payload = {
		"id": patient_id,
		"abha_id": None,
		"name": state.get("patient_name"),
		"age_months": state.get("age_months"),
		"sex": state.get("sex"),
		"village": state.get("village_id"),
		"asha_id": state.get("asha_id"),
	}
	if crud.get_patient(db, patient_id):
		crud.update_patient(db, patient_id, patient_payload)
	else:
		crud.create_patient(db, patient_payload)

	case_id = state.get("request_id") or str(uuid.uuid4())
	state["request_id"] = case_id
	vitals = state.get("validated_vitals", {})
	case_payload = {
		"id": case_id,
		"patient_id": patient_id,
		"timestamp": int(datetime.now(UTC).timestamp() * 1000),
		"spo2": vitals.get("spo2"),
		"heart_rate": vitals.get("heart_rate"),
		"temperature": vitals.get("temperature"),
		"weight": vitals.get("weight_kg"),
		"symptoms": state.get("translated_symptoms")
		or state.get("normalized_symptoms")
		or ([state["symptom_text"]] if state.get("symptom_text") else []),
		"risk_tier": state.get("risk_level") or "LOW",
		"risk_explanation": state.get("risk_explanation")
		or state.get("risk_factors")
		or {},
		"errors": state.get("errors") or state.get("agent_errors") or [],
		"ruleset_version": state.get("ruleset_version"),
		"growth_reference_version": state.get("growth_reference_version"),
		"triage_model_version": state.get("model_version"),
		"sync_status": "PENDING",
	}
	if crud.get_case(db, case_id):
		crud.update_case(db, case_id, case_payload)
	else:
		crud.create_case(db, case_payload)

	if state.get("action_plan") or state.get("differential_diagnosis"):
		rec_payload = {
			"id": str(uuid.uuid4()),
			"case_id": case_id,
			"primary_diagnosis": (
				state.get("action_plan", {}).get("primary_diagnosis")
				or state.get("differential_diagnosis", {}).get("diagnoses", [{}])[0].get(
					"condition_name", ""
				)
			),
			"confidence": "Low",
			"differential_json": state.get("differential_diagnosis") or {},
			"action_plan": state.get("action_plan") or {},
			"citations": state.get("citations")
			or (state.get("differential_diagnosis") or {}).get("citations", []),
			"referral_facility": state.get("action_plan", {}).get("referral", {}).get(
				"facility_name"
			)
			if state.get("action_plan")
			else None,
		}
		existing = crud.get_recommendation_by_case(db, case_id)
		if existing:
			crud.update_recommendation(db, existing.id, rec_payload)
		else:
			crud.create_recommendation(db, rec_payload)


@router.post("/assess", response_model=TriageResult)
async def assess_patient(
	assessment: PatientAssessment,
	db: Session = Depends(get_db),
	user: AuthUser = Depends(require_roles([Role.ASHA_WORKER, Role.MEDICAL_OFFICER])),
):
	if user.role == Role.ASHA_WORKER and assessment.asha_id != user.user_id:
		raise HTTPException(status_code=403, detail="Access denied")
	if assessment.patient_id and crud.get_patient(db, assessment.patient_id):
		require_patient_access(db, user, assessment.patient_id)
	try:
		state = state_from_assessment(assessment)
		state["request_id"] = str(uuid.uuid4())
		result_state = run_pipeline(state)
		_persist_state(db, result_state)
		return TriageResult(
			request_id=result_state.get("request_id"),
			risk_level=result_state.get("risk_level"),
			risk_confidence=result_state.get("risk_confidence"),
			differential_diagnosis=result_state.get("differential_diagnosis"),
			action_plan=result_state.get("action_plan"),
			asha_output_text=result_state.get("asha_output_text"),
			created_at=result_state.get("created_at") or datetime.now(UTC).isoformat(),
			ruleset_version=result_state.get("ruleset_version"),
			growth_reference_version=result_state.get("growth_reference_version"),
			triage_model_version=result_state.get("model_version"),
		)
	except HTTPException:
		raise
	except Exception as exc:
		logger.exception("Triage assessment failed")
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Internal server error",
		) from exc


@router.get("/history/{patient_id}", response_model=HistoryPage)
async def triage_history(
	patient_id: str,
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
	db: Session = Depends(get_db),
	user: AuthUser = Depends(require_roles([Role.ASHA_WORKER, Role.MEDICAL_OFFICER])),
):
	require_patient_access(db, user, patient_id)
	total = crud.count_cases_by_patient(db, patient_id)
	cases = crud.list_cases_by_patient(
		db, patient_id, skip=(page - 1) * page_size, limit=page_size
	)
	return HistoryPage(
		items=[
			HistoryItem(
				id=case.id,
				patient_id=case.patient_id,
				timestamp=case.timestamp,
				risk_tier=case.risk_tier.value,
				risk_explanation=case.risk_explanation,
				symptoms=case.symptoms,
				spo2=case.spo2,
				heart_rate=case.heart_rate,
				temperature=case.temperature,
				version=case.version,
				updated_at=case.updated_at,
				ruleset_version=case.ruleset_version,
				growth_reference_version=case.growth_reference_version,
				triage_model_version=case.triage_model_version,
			)
			for case in cases
		],
		page=page,
		page_size=page_size,
		total=total,
		total_pages=(total + page_size - 1) // page_size,
	)


@router.get("/encounter/{encounter_id}", response_model=EncounterResponse)
async def triage_encounter(
	encounter_id: str,
	db: Session = Depends(get_db),
	user: AuthUser = Depends(require_roles([Role.ASHA_WORKER, Role.MEDICAL_OFFICER])),
):
	require_case_access(db, user, encounter_id)
	case = crud.get_case(db, encounter_id)
	if not case:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
	rec = crud.get_recommendation_by_case(db, encounter_id)
	case_response = HistoryItem(
		id=case.id,
		patient_id=case.patient_id,
		timestamp=case.timestamp,
		risk_tier=case.risk_tier.value,
		risk_explanation=case.risk_explanation,
		symptoms=case.symptoms,
		spo2=case.spo2,
		heart_rate=case.heart_rate,
		temperature=case.temperature,
		version=case.version,
		updated_at=case.updated_at,
		ruleset_version=case.ruleset_version,
		growth_reference_version=case.growth_reference_version,
		triage_model_version=case.triage_model_version,
	)
	recommendation = (
		RecommendationResponse(
			id=rec.id,
			primary_diagnosis=rec.primary_diagnosis,
			confidence=rec.confidence,
			differential_diagnosis=rec.differential_json,
			action_plan=rec.action_plan,
			citations=rec.citations,
			referral_facility=rec.referral_facility,
			counseling=rec.counseling,
			version=rec.version,
			updated_at=rec.updated_at,
		)
		if rec
		else None
	)
	return EncounterResponse(
		case=case_response,
		recommendation=recommendation,
		errors=case.errors,
	)
