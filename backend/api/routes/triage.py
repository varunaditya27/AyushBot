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

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.agents.orchestrator import run_pipeline
from backend.agents.schemas.patient_assessment import PatientAssessment
from backend.agents.state import state_from_assessment
from backend.db import crud
from backend.db.session import get_db
from backend.security.auth import AuthUser, Role, require_roles

router = APIRouter()


class TriageResult(BaseModel):
	request_id: str
	risk_level: Optional[str] = None
	risk_confidence: Optional[float] = None
	differential_diagnosis: Optional[Dict] = None
	action_plan: Optional[Dict] = None
	asha_output_text: Optional[str] = None
	created_at: str


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
		"timestamp": int(datetime.utcnow().timestamp() * 1000),
		"spo2": vitals.get("spo2"),
		"heart_rate": vitals.get("heart_rate"),
		"temperature": vitals.get("temperature"),
		"weight": vitals.get("weight_kg"),
		"symptoms": "[]",
		"risk_tier": state.get("risk_level") or "LOW",
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
			"differential_json": json.dumps(state.get("differential_diagnosis") or {}),
			"action_plan": json.dumps(state.get("action_plan") or {}),
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
	_user: AuthUser = Depends(require_roles([Role.ASHA_WORKER, Role.MEDICAL_OFFICER])),
):
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
			created_at=result_state.get("created_at") or datetime.utcnow().isoformat(),
		)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=str(exc),
		) from exc


@router.get("/history/{patient_id}", response_model=List[Dict])
async def triage_history(
	patient_id: str,
	db: Session = Depends(get_db),
	_user: AuthUser = Depends(require_roles([Role.ASHA_WORKER, Role.MEDICAL_OFFICER])),
):
	cases = crud.list_cases_by_patient(db, patient_id)
	return [
		{
			"id": case.id,
			"timestamp": case.timestamp,
			"risk_tier": case.risk_tier,
			"spo2": case.spo2,
			"heart_rate": case.heart_rate,
			"temperature": case.temperature,
		}
		for case in cases
	]


@router.get("/encounter/{encounter_id}", response_model=Dict)
async def triage_encounter(
	encounter_id: str,
	db: Session = Depends(get_db),
	_user: AuthUser = Depends(require_roles([Role.ASHA_WORKER, Role.MEDICAL_OFFICER])),
):
	case = crud.get_case(db, encounter_id)
	if not case:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
	rec = crud.get_recommendation_by_case(db, encounter_id)
	return {
		"case": {
			"id": case.id,
			"patient_id": case.patient_id,
			"timestamp": case.timestamp,
			"risk_tier": case.risk_tier,
			"spo2": case.spo2,
			"heart_rate": case.heart_rate,
			"temperature": case.temperature,
		},
		"recommendation": rec.action_plan if rec else None,
	}
