"""Transaction-safe CRUD and database services."""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any, TypeVar

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.db.models import (
	AuditEvent,
	Case,
	ClinicalFeedback,
	ConsentRecord,
	Device,
	Facility,
	FLRound,
	IdempotencyRecord,
	ModelVersion,
	Patient,
	PrivacyBudget,
	Recommendation,
	RoadEdge,
	SyncResource,
	TelemetryEvent,
	TokenRecord,
	UserAccount,
	Village,
	now_ms,
)

ModelT = TypeVar("ModelT")
JSON_FIELDS = {
	Case: {"symptoms", "risk_explanation", "errors"},
	Recommendation: {"differential_json", "action_plan", "citations"},
}


def _coerce_json(value: Any, default: Any) -> Any:
	if value is None:
		return default
	if not isinstance(value, str):
		return value
	text = value.strip()
	if not text:
		return default
	try:
		return json.loads(text)
	except json.JSONDecodeError:
		return value


def _normalize(model: type[ModelT], data: dict[str, Any]) -> dict[str, Any]:
	normalized = dict(data)
	for field in JSON_FIELDS.get(model, set()):
		if field in normalized:
			default = [] if field in {"symptoms", "differential_json"} else {}
			normalized[field] = _coerce_json(normalized[field], default)
	return normalized


def _create(db: Session, model: type[ModelT], data: dict[str, Any]) -> ModelT:
	record = model(**_normalize(model, data))
	try:
		with db.begin_nested():
			db.add(record)
			db.flush()
	except IntegrityError as exc:
		raise ValueError(f"Failed to create {model.__name__}; integrity error") from exc
	return record


def _update(record: ModelT, updates: dict[str, Any], model: type[ModelT]) -> ModelT:
	for key, value in _normalize(model, updates).items():
		if key not in {"id", "created_at"} and hasattr(record, key):
			setattr(record, key, value)
	if hasattr(record, "updated_at"):
		setattr(record, "updated_at", now_ms())
	return record


def _update_record(
	db: Session, record: ModelT, updates: dict[str, Any], model: type[ModelT]
) -> ModelT:
	try:
		with db.begin_nested():
			_update(record, updates, model)
			db.flush()
	except IntegrityError as exc:
		raise ValueError(f"Failed to update {model.__name__}; integrity error") from exc
	return record


def _get(db: Session, model: type[ModelT], record_id: str) -> ModelT | None:
	return db.get(model, record_id)


def create_patient(db: Session, patient_data: dict[str, Any]) -> Patient:
	return _create(db, Patient, patient_data)


def get_patient(db: Session, patient_id: str) -> Patient | None:
	return _get(db, Patient, patient_id)


def list_patients(db: Session, skip: int = 0, limit: int = 100) -> list[Patient]:
	return list(db.scalars(select(Patient).offset(skip).limit(limit)))


def update_patient(
	db: Session, patient_id: str, updates: dict[str, Any]
) -> Patient | None:
	patient = get_patient(db, patient_id)
	if patient is None:
		return None
	return _update_record(db, patient, updates, Patient)


def delete_patient(db: Session, patient_id: str) -> bool:
	patient = get_patient(db, patient_id)
	if patient is None:
		return False
	db.delete(patient)
	db.flush()
	return True


def create_case(db: Session, case_data: dict[str, Any]) -> Case:
	return _create(db, Case, case_data)


def create_cases_bulk(db: Session, cases: Iterable[dict[str, Any]]) -> list[Case]:
	created: list[Case] = []
	try:
		with db.begin_nested():
			for payload in cases:
				record = Case(**_normalize(Case, payload))
				db.add(record)
				created.append(record)
			db.flush()
	except IntegrityError as exc:
		raise ValueError("Failed to create cases; integrity error") from exc
	return created


def get_case(db: Session, case_id: str) -> Case | None:
	return _get(db, Case, case_id)


def list_cases(db: Session, skip: int = 0, limit: int = 100) -> list[Case]:
	return list(db.scalars(select(Case).offset(skip).limit(limit)))


def list_cases_by_patient(
	db: Session, patient_id: str, skip: int = 0, limit: int = 100
) -> list[Case]:
	statement = (
		select(Case)
		.where(Case.patient_id == patient_id)
		.order_by(Case.timestamp.desc())
		.offset(skip)
		.limit(limit)
	)
	return list(db.scalars(statement))


def count_cases_by_patient(db: Session, patient_id: str) -> int:
	return int(
		db.scalar(select(func.count()).select_from(Case).where(Case.patient_id == patient_id))
		or 0
	)


def update_case(db: Session, case_id: str, updates: dict[str, Any]) -> Case | None:
	case = get_case(db, case_id)
	if case is None:
		return None
	return _update_record(db, case, updates, Case)


def delete_case(db: Session, case_id: str) -> bool:
	case = get_case(db, case_id)
	if case is None:
		return False
	db.delete(case)
	db.flush()
	return True


def create_recommendation(
	db: Session, recommendation_data: dict[str, Any]
) -> Recommendation:
	return _create(db, Recommendation, recommendation_data)


def get_recommendation(
	db: Session, recommendation_id: str
) -> Recommendation | None:
	return _get(db, Recommendation, recommendation_id)


def get_recommendation_by_case(
	db: Session, case_id: str
) -> Recommendation | None:
	return db.scalar(select(Recommendation).where(Recommendation.case_id == case_id))


def list_recommendations(
	db: Session, skip: int = 0, limit: int = 100
) -> list[Recommendation]:
	return list(db.scalars(select(Recommendation).offset(skip).limit(limit)))


def update_recommendation(
	db: Session, recommendation_id: str, updates: dict[str, Any]
) -> Recommendation | None:
	recommendation = get_recommendation(db, recommendation_id)
	if recommendation is None:
		return None
	return _update_record(db, recommendation, updates, Recommendation)


def delete_recommendation(db: Session, recommendation_id: str) -> bool:
	recommendation = get_recommendation(db, recommendation_id)
	if recommendation is None:
		return False
	db.delete(recommendation)
	db.flush()
	return True


def upsert_village(db: Session, data: dict[str, Any]) -> Village:
	village = get_village(db, str(data["id"]))
	if village is None:
		return _create(db, Village, data)
	return _update_record(db, village, data, Village)


def get_village(db: Session, village_id: str) -> Village | None:
	return _get(db, Village, village_id)


def list_villages(db: Session, active_only: bool = True) -> list[Village]:
	statement = select(Village).order_by(Village.name)
	if active_only:
		statement = statement.where(Village.active.is_(True))
	return list(db.scalars(statement))


def upsert_facility(db: Session, data: dict[str, Any]) -> Facility:
	facility = get_facility(db, str(data["id"]))
	if facility is None:
		return _create(db, Facility, data)
	return _update_record(db, facility, data, Facility)


def get_facility(db: Session, facility_id: str) -> Facility | None:
	return _get(db, Facility, facility_id)


def list_facilities(
	db: Session, facility_type: str | None = None, active_only: bool = True
) -> list[Facility]:
	statement = select(Facility).order_by(Facility.name)
	if facility_type:
		statement = statement.where(Facility.type == facility_type)
	if active_only:
		statement = statement.where(Facility.active.is_(True))
	return list(db.scalars(statement))


def upsert_road_edge(db: Session, data: dict[str, Any]) -> RoadEdge:
	edge = _get(db, RoadEdge, str(data["id"]))
	if edge is None:
		return _create(db, RoadEdge, data)
	return _update_record(db, edge, data, RoadEdge)


def create_clinical_feedback(
	db: Session, data: dict[str, Any]
) -> ClinicalFeedback:
	return _create(db, ClinicalFeedback, data)


def get_clinical_feedback(
	db: Session, case_id: str, reviewer_id: str
) -> ClinicalFeedback | None:
	return db.scalar(
		select(ClinicalFeedback).where(
			ClinicalFeedback.case_id == case_id,
			ClinicalFeedback.reviewer_id == reviewer_id,
		)
	)


def list_clinical_feedback(
	db: Session, case_id: str | None = None, skip: int = 0, limit: int = 100
) -> list[ClinicalFeedback]:
	statement = select(ClinicalFeedback).order_by(ClinicalFeedback.created_at.desc())
	if case_id:
		statement = statement.where(ClinicalFeedback.case_id == case_id)
	return list(db.scalars(statement.offset(skip).limit(limit)))


def register_model_version(db: Session, data: dict[str, Any]) -> ModelVersion:
	return _create(db, ModelVersion, data)


def create_sync_resource(db: Session, data: dict[str, Any]) -> SyncResource:
	return _create(db, SyncResource, data)


def get_sync_resource(db: Session, resource_id: str) -> SyncResource | None:
	return _get(db, SyncResource, resource_id)


def list_active_sync_resources(
	db: Session, resource_type: str | None = None
) -> list[SyncResource]:
	statement = select(SyncResource).where(SyncResource.active.is_(True))
	if resource_type:
		statement = statement.where(SyncResource.resource_type == resource_type)
	statement = statement.order_by(
		SyncResource.resource_type, SyncResource.resource_id, SyncResource.version.desc()
	)
	return list(db.scalars(statement))


def create_telemetry_event(db: Session, data: dict[str, Any]) -> TelemetryEvent:
	return _create(db, TelemetryEvent, data)


def get_telemetry_event(db: Session, event_id: str) -> TelemetryEvent | None:
	return _get(db, TelemetryEvent, event_id)


def get_idempotency_record(
	db: Session, user_id: str, endpoint: str, idempotency_key: str
) -> IdempotencyRecord | None:
	return db.scalar(
		select(IdempotencyRecord).where(
			IdempotencyRecord.user_id == user_id,
			IdempotencyRecord.endpoint == endpoint,
			IdempotencyRecord.idempotency_key == idempotency_key,
		)
	)


def create_idempotency_record(
	db: Session, data: dict[str, Any]
) -> IdempotencyRecord:
	return _create(db, IdempotencyRecord, data)


def register_device(db: Session, data: dict[str, Any]) -> Device:
	device = _get(db, Device, str(data["id"]))
	if device is None:
		return _create(db, Device, data)
	return _update_record(db, device, data, Device)


def get_device(db: Session, device_id: str) -> Device | None:
	return _get(db, Device, device_id)


def list_devices_for_owner(db: Session, owner_id: str) -> list[Device]:
	return list(db.scalars(select(Device).where(Device.owner_id == owner_id)))


def create_fl_round(db: Session, data: dict[str, Any]) -> FLRound:
	return _create(db, FLRound, data)


def create_privacy_budget(db: Session, data: dict[str, Any]) -> PrivacyBudget:
	return _create(db, PrivacyBudget, data)


def spend_privacy_budget(
	db: Session, budget_id: str, epsilon: float, round_id: str | None = None
) -> PrivacyBudget:
	if epsilon <= 0:
		raise ValueError("epsilon must be positive")
	budget = _get(db, PrivacyBudget, budget_id)
	if budget is None:
		raise ValueError("Privacy budget not found")
	new_total = budget.epsilon_spent + epsilon
	if new_total > budget.epsilon_limit:
		raise ValueError("Privacy budget would be exceeded")
	budget.epsilon_spent = new_total
	budget.last_round_id = round_id
	budget.updated_at = now_ms()
	db.flush()
	return budget


def create_consent_record(db: Session, data: dict[str, Any]) -> ConsentRecord:
	return _create(db, ConsentRecord, data)


def create_audit_event(db: Session, data: dict[str, Any]) -> AuditEvent:
	return _create(db, AuditEvent, data)


def create_user_account(db: Session, data: dict[str, Any]) -> UserAccount:
	return _create(db, UserAccount, data)


def get_user_account(db: Session, user_id: str) -> UserAccount | None:
	return _get(db, UserAccount, user_id)


def get_user_by_username(db: Session, username: str) -> UserAccount | None:
	return db.scalar(select(UserAccount).where(UserAccount.username == username))


def update_user_account(
	db: Session, user_id: str, updates: dict[str, Any]
) -> UserAccount | None:
	user = get_user_account(db, user_id)
	if user is None:
		return None
	return _update_record(db, user, updates, UserAccount)


def create_token_record(db: Session, data: dict[str, Any]) -> TokenRecord:
	return _create(db, TokenRecord, data)


def get_token_record_by_hash(db: Session, jti_hash: str) -> TokenRecord | None:
	return db.scalar(select(TokenRecord).where(TokenRecord.jti_hash == jti_hash))


def list_token_family(db: Session, family_id: str) -> list[TokenRecord]:
	return list(
		db.scalars(select(TokenRecord).where(TokenRecord.family_id == family_id))
	)
