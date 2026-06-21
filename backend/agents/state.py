"""AyushBot Backend — Shared Patient State Object Schema."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Dict, List, Literal, Optional, TypedDict

from backend.agents.schemas.patient_assessment import PatientAssessment


class PipelineError(TypedDict, total=False):
	stage: str
	code: str
	message: str
	recoverable: bool


class PatientState(TypedDict, total=False):
	patient_id: Optional[str]
	patient_name: Optional[str]
	age_months: int
	sex: str
	weight_kg: Optional[float]
	village_id: str
	asha_id: str
	location: tuple[float, float] | list[float]
	raw_vitals: Dict[str, Any]
	asha_input_text: Optional[str]
	asha_checklist: Dict[str, Optional[bool]]
	diarrhea_duration_days: Optional[float]
	input_language: Optional[str]
	intent: Optional[str]
	extracted_entities: List[Dict[str, Any]]
	translated_symptoms: List[str]
	validated_vitals: Dict[str, Any]
	derived_features: Dict[str, Any]
	risk_level: Optional[str]
	risk_confidence: Optional[float]
	risk_explanation: Dict[str, Any]
	signal_quality: Dict[str, Any]
	ruleset_version: Optional[str]
	growth_reference_version: Optional[str]
	model_version: Optional[str]
	classifier_status: Optional[str]
	medical_review_required: bool
	emergency_escalate: bool
	differential_diagnosis: Optional[Dict[str, Any]]
	retrieved_chunks: List[Dict[str, Any]]
	retrieval_metrics: Dict[str, Any]
	action_plan: Optional[Dict[str, Any]]
	routing_result: Optional[Dict[str, Any]]
	prescriptions: List[Dict[str, Any]]
	asha_output_text: Optional[str]
	asha_output_audio: Optional[bytes]
	request_id: Optional[str]
	created_at: Optional[str]
	agent_timings: Dict[str, float]
	errors: List[PipelineError]
	pipeline_status: Optional[Literal["IN_PROGRESS", "COMPLETED", "DEGRADED", "FAILED"]]


def add_pipeline_error(
	state: PatientState,
	*,
	stage: str,
	code: str,
	message: str | None = None,
	recoverable: bool = True,
) -> None:
	error: PipelineError = {
		"stage": stage,
		"code": code,
		"recoverable": recoverable,
	}
	if message:
		error["message"] = message
	state.setdefault("errors", []).append(error)


def state_from_assessment(assessment: PatientAssessment) -> PatientState:
	vitals = assessment.vitals
	raw_vitals = {
		"spo2": vitals.spo2 if vitals else None,
		"heart_rate": vitals.heart_rate if vitals else None,
		"temperature_celsius": vitals.temperature_celsius if vitals else None,
		"respiratory_rate": vitals.respiratory_rate if vitals else None,
		"weight_grams": vitals.weight_grams if vitals else None,
		"measurement_timestamp": vitals.measurement_timestamp.isoformat()
		if vitals and vitals.measurement_timestamp
		else None,
		"signal_quality": vitals.signal_quality if vitals else {},
		"history": [
			point.model_dump(mode="json") for point in (vitals.history if vitals else [])
		],
	}
	return PatientState(
		patient_id=assessment.patient_id,
		patient_name=assessment.patient_name,
		age_months=assessment.age_months,
		sex=assessment.sex,
		weight_kg=assessment.weight_kg,
		village_id=assessment.village_id,
		asha_id=assessment.asha_id,
		raw_vitals=raw_vitals,
		asha_input_text=assessment.symptom_text,
		asha_checklist=assessment.asha_checklist,
		diarrhea_duration_days=assessment.diarrhea_duration_days,
		input_language=assessment.input_language,
		translated_symptoms=[],
		extracted_entities=[],
		validated_vitals={},
		derived_features={},
		risk_level=None,
		risk_confidence=None,
		risk_explanation={},
		signal_quality={},
		retrieved_chunks=[],
		retrieval_metrics={},
		prescriptions=[],
		agent_timings={},
		ruleset_version=None,
		growth_reference_version=None,
		model_version=None,
		classifier_status=None,
		medical_review_required=True,
		emergency_escalate=False,
		errors=[],
		pipeline_status="IN_PROGRESS",
		created_at=datetime.now(UTC).isoformat(),
	)
