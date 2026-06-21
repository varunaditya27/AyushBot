"""SQLAlchemy models for the AyushBot gateway database."""

from __future__ import annotations

import enum
import time
from typing import Any

from sqlalchemy import (
	Boolean,
	Enum,
	Float,
	ForeignKey,
	Index,
	Integer,
	JSON,
	String,
	Text,
	UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def now_ms() -> int:
	return int(time.time() * 1000)


def enum_type(enum_class: type[enum.Enum], name: str) -> Enum:
	return Enum(
		enum_class,
		name=name,
		native_enum=False,
		create_constraint=True,
		validate_strings=True,
		values_callable=lambda values: [item.value for item in values],
	)


class RiskTier(str, enum.Enum):
	LOW = "LOW"
	MEDIUM = "MEDIUM"
	HIGH = "HIGH"
	CRITICAL = "CRITICAL"


class SyncStatus(str, enum.Enum):
	PENDING = "PENDING"
	SYNCED = "SYNCED"
	FAILED = "FAILED"
	CONFLICT = "CONFLICT"


class FacilityType(str, enum.Enum):
	SC = "SC"
	PHC = "PHC"
	CHC = "CHC"
	SDH = "SDH"
	DH = "DH"
	OTHER = "OTHER"


class FeedbackDisposition(str, enum.Enum):
	CONFIRMED = "CONFIRMED"
	MODIFIED = "MODIFIED"
	REJECTED = "REJECTED"
	UNSURE = "UNSURE"


class ModelStatus(str, enum.Enum):
	STAGED = "STAGED"
	ACTIVE = "ACTIVE"
	RETIRED = "RETIRED"
	FAILED = "FAILED"


class SyncOperation(str, enum.Enum):
	UPSERT = "UPSERT"
	DELETE = "DELETE"


class DeviceType(str, enum.Enum):
	GATEWAY = "GATEWAY"
	ANDROID = "ANDROID"
	SENSOR = "SENSOR"
	CLOUD = "CLOUD"


class DeviceStatus(str, enum.Enum):
	ACTIVE = "ACTIVE"
	INACTIVE = "INACTIVE"
	REVOKED = "REVOKED"


class FLRoundStatus(str, enum.Enum):
	PENDING = "PENDING"
	TRAINING = "TRAINING"
	READY = "READY"
	SYNCED = "SYNCED"
	FAILED = "FAILED"


class ConsentStatus(str, enum.Enum):
	GRANTED = "GRANTED"
	WITHDRAWN = "WITHDRAWN"
	EXPIRED = "EXPIRED"


class AuditOutcome(str, enum.Enum):
	SUCCESS = "SUCCESS"
	DENIED = "DENIED"
	FAILURE = "FAILURE"


class UserRole(str, enum.Enum):
	ASHA_WORKER = "AshaWorker"
	MEDICAL_OFFICER = "MedicalOfficer"


class TokenType(str, enum.Enum):
	ACCESS = "access"
	REFRESH = "refresh"


class Base(DeclarativeBase):
	__abstract__ = True


class TimestampMixin:
	created_at: Mapped[int] = mapped_column(Integer, default=now_ms, nullable=False)
	updated_at: Mapped[int] = mapped_column(
		Integer, default=now_ms, onupdate=now_ms, nullable=False
	)


class Village(TimestampMixin, Base):
	__tablename__ = "villages"

	id: Mapped[str] = mapped_column(String(64), primary_key=True)
	name: Mapped[str] = mapped_column(String(256), nullable=False)
	district: Mapped[str | None] = mapped_column(String(128))
	state: Mapped[str | None] = mapped_column(String(128))
	pincode: Mapped[str | None] = mapped_column(String(12))
	latitude: Mapped[float | None] = mapped_column(Float)
	longitude: Mapped[float | None] = mapped_column(Float)
	active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

	__table_args__ = (
		UniqueConstraint("name", "district", "state", name="uq_villages_location"),
		Index("ix_villages_active_name", "active", "name"),
	)


class Facility(TimestampMixin, Base):
	__tablename__ = "facilities"

	id: Mapped[str] = mapped_column(String(64), primary_key=True)
	name: Mapped[str] = mapped_column(String(256), nullable=False)
	type: Mapped[FacilityType] = mapped_column(
		enum_type(FacilityType, "facility_type"), nullable=False
	)
	village_id: Mapped[str | None] = mapped_column(
		String(64), ForeignKey("villages.id", ondelete="SET NULL")
	)
	latitude: Mapped[float] = mapped_column(Float, nullable=False)
	longitude: Mapped[float] = mapped_column(Float, nullable=False)
	address: Mapped[str | None] = mapped_column(Text)
	phone: Mapped[str | None] = mapped_column(String(32))
	active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

	village: Mapped[Village | None] = relationship()

	__table_args__ = (
		UniqueConstraint("name", "latitude", "longitude", name="uq_facilities_location"),
		Index("ix_facilities_type_active", "type", "active"),
		Index("ix_facilities_village_id", "village_id"),
	)


class RoadEdge(TimestampMixin, Base):
	__tablename__ = "road_edges"

	id: Mapped[str] = mapped_column(String(64), primary_key=True)
	from_node_id: Mapped[str] = mapped_column(String(64), nullable=False)
	to_node_id: Mapped[str] = mapped_column(String(64), nullable=False)
	distance_km: Mapped[float] = mapped_column(Float, nullable=False)
	travel_time_minutes: Mapped[int | None] = mapped_column(Integer)
	road_class: Mapped[str | None] = mapped_column(String(64))
	bidirectional: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

	__table_args__ = (
		UniqueConstraint("from_node_id", "to_node_id", name="uq_road_edges_nodes"),
		Index("ix_road_edges_from_active", "from_node_id", "active"),
		Index("ix_road_edges_to_active", "to_node_id", "active"),
	)


class Patient(TimestampMixin, Base):
	__tablename__ = "patients"

	id: Mapped[str] = mapped_column(String(64), primary_key=True)
	abha_id: Mapped[str | None] = mapped_column(String(64), unique=True)
	name: Mapped[str | None] = mapped_column(String(256))
	age_months: Mapped[int] = mapped_column(Integer, nullable=False)
	sex: Mapped[str] = mapped_column(String(16), nullable=False)
	village: Mapped[str | None] = mapped_column(String(128))
	asha_id: Mapped[str] = mapped_column(String(64), nullable=False)
	version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

	cases: Mapped[list[Case]] = relationship(
		back_populates="patient", cascade="all, delete-orphan", passive_deletes=True
	)
	consents: Mapped[list[ConsentRecord]] = relationship(
		back_populates="patient", cascade="all, delete-orphan", passive_deletes=True
	)

	__table_args__ = (
		Index("ix_patients_asha_id", "asha_id"),
		Index("ix_patients_village", "village"),
	)


class UserAccount(TimestampMixin, Base):
	__tablename__ = "user_accounts"

	id: Mapped[str] = mapped_column(String(64), primary_key=True)
	username: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
	password_hash: Mapped[str] = mapped_column(Text, nullable=False)
	role: Mapped[UserRole] = mapped_column(
		enum_type(UserRole, "user_role"), nullable=False
	)
	display_name: Mapped[str | None] = mapped_column(String(256))
	active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	password_changed_at: Mapped[int] = mapped_column(Integer, default=now_ms, nullable=False)
	last_login_at: Mapped[int | None] = mapped_column(Integer)

	__table_args__ = (
		Index("ix_user_accounts_role_active", "role", "active"),
	)


class Case(TimestampMixin, Base):
	__tablename__ = "cases"

	id: Mapped[str] = mapped_column(String(64), primary_key=True)
	patient_id: Mapped[str] = mapped_column(
		String(64), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
	)
	timestamp: Mapped[int] = mapped_column(Integer, default=now_ms, nullable=False)
	spo2: Mapped[float | None] = mapped_column(Float)
	heart_rate: Mapped[float | None] = mapped_column(Float)
	temperature: Mapped[float | None] = mapped_column(Float)
	weight: Mapped[float | None] = mapped_column(Float)
	symptoms: Mapped[list[Any] | dict[str, Any]] = mapped_column(
		JSON, default=list, nullable=False
	)
	risk_tier: Mapped[RiskTier] = mapped_column(
		enum_type(RiskTier, "risk_tier"), default=RiskTier.LOW, nullable=False
	)
	sync_status: Mapped[SyncStatus] = mapped_column(
		enum_type(SyncStatus, "sync_status"), default=SyncStatus.PENDING, nullable=False
	)
	version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
	risk_explanation: Mapped[dict[str, Any] | list[Any]] = mapped_column(
		JSON, default=dict, nullable=False
	)
	errors: Mapped[list[Any] | dict[str, Any]] = mapped_column(
		JSON, default=list, nullable=False
	)
	ruleset_version: Mapped[str | None] = mapped_column(String(128))
	growth_reference_version: Mapped[str | None] = mapped_column(String(128))
	triage_model_version: Mapped[str | None] = mapped_column(String(128))

	patient: Mapped[Patient] = relationship(back_populates="cases")
	recommendation: Mapped[Recommendation | None] = relationship(
		back_populates="case",
		cascade="all, delete-orphan",
		passive_deletes=True,
		uselist=False,
	)

	__table_args__ = (
		Index("ix_cases_patient_timestamp", "patient_id", "timestamp"),
		Index("ix_cases_sync_status", "sync_status"),
		Index("ix_cases_risk_timestamp", "risk_tier", "timestamp"),
	)


class ModelVersion(TimestampMixin, Base):
	__tablename__ = "model_versions"

	id: Mapped[str] = mapped_column(String(64), primary_key=True)
	model_name: Mapped[str] = mapped_column(String(128), nullable=False)
	version: Mapped[str] = mapped_column(String(64), nullable=False)
	status: Mapped[ModelStatus] = mapped_column(
		enum_type(ModelStatus, "model_status"), default=ModelStatus.STAGED, nullable=False
	)
	artifact_uri: Mapped[str | None] = mapped_column(Text)
	checksum_sha256: Mapped[str | None] = mapped_column(String(64))
	metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
	activated_at: Mapped[int | None] = mapped_column(Integer)

	__table_args__ = (
		UniqueConstraint("model_name", "version", name="uq_model_versions_name_version"),
		Index("ix_model_versions_name_status", "model_name", "status"),
	)


class Recommendation(TimestampMixin, Base):
	__tablename__ = "recommendations"

	id: Mapped[str] = mapped_column(String(64), primary_key=True)
	case_id: Mapped[str] = mapped_column(
		String(64), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, unique=True
	)
	model_version_id: Mapped[str | None] = mapped_column(
		String(64), ForeignKey("model_versions.id", ondelete="SET NULL")
	)
	primary_diagnosis: Mapped[str] = mapped_column(String(256), nullable=False)
	confidence: Mapped[str] = mapped_column(String(16), default="Low", nullable=False)
	differential_json: Mapped[list[Any] | dict[str, Any]] = mapped_column(
		JSON, default=list, nullable=False
	)
	action_plan: Mapped[list[Any] | dict[str, Any] | str] = mapped_column(
		JSON, default=dict, nullable=False
	)
	referral_facility: Mapped[str | None] = mapped_column(String(128))
	drug_dosage: Mapped[str | None] = mapped_column(String(256))
	counseling: Mapped[str | None] = mapped_column(Text)
	citation_source: Mapped[str | None] = mapped_column(String(256))
	citation_text: Mapped[str | None] = mapped_column(Text)
	citations: Mapped[list[Any] | dict[str, Any]] = mapped_column(
		JSON, default=list, nullable=False
	)
	version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

	case: Mapped[Case] = relationship(back_populates="recommendation")
	model_version: Mapped[ModelVersion | None] = relationship()
	feedback: Mapped[list[ClinicalFeedback]] = relationship(
		back_populates="recommendation", cascade="all, delete-orphan"
	)

	__table_args__ = (Index("ix_recommendations_model_version_id", "model_version_id"),)


class ClinicalFeedback(TimestampMixin, Base):
	__tablename__ = "clinical_feedback"

	id: Mapped[str] = mapped_column(String(64), primary_key=True)
	case_id: Mapped[str] = mapped_column(
		String(64), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
	)
	recommendation_id: Mapped[str | None] = mapped_column(
		String(64), ForeignKey("recommendations.id", ondelete="SET NULL")
	)
	reviewer_id: Mapped[str] = mapped_column(String(64), nullable=False)
	disposition: Mapped[FeedbackDisposition] = mapped_column(
		enum_type(FeedbackDisposition, "feedback_disposition"), nullable=False
	)
	confirmed_diagnosis: Mapped[str | None] = mapped_column(String(256))
	notes: Mapped[str | None] = mapped_column(Text)
	structured_feedback: Mapped[dict[str, Any]] = mapped_column(
		JSON, default=dict, nullable=False
	)

	recommendation: Mapped[Recommendation | None] = relationship(back_populates="feedback")

	__table_args__ = (
		UniqueConstraint("case_id", "reviewer_id", name="uq_feedback_case_reviewer"),
		Index("ix_feedback_case_created", "case_id", "created_at"),
	)


class Device(TimestampMixin, Base):
	__tablename__ = "devices"

	id: Mapped[str] = mapped_column(String(64), primary_key=True)
	device_type: Mapped[DeviceType] = mapped_column(
		enum_type(DeviceType, "device_type"), nullable=False
	)
	status: Mapped[DeviceStatus] = mapped_column(
		enum_type(DeviceStatus, "device_status"), default=DeviceStatus.ACTIVE, nullable=False
	)
	owner_id: Mapped[str | None] = mapped_column(String(64))
	display_name: Mapped[str | None] = mapped_column(String(128))
	public_key_fingerprint: Mapped[str | None] = mapped_column(String(128), unique=True)
	app_version: Mapped[str | None] = mapped_column(String(64))
	last_seen_at: Mapped[int | None] = mapped_column(Integer)
	metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

	__table_args__ = (Index("ix_devices_type_status", "device_type", "status"),)


class TokenRecord(Base):
	__tablename__ = "token_records"

	id: Mapped[str] = mapped_column(String(64), primary_key=True)
	jti_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
	family_id: Mapped[str] = mapped_column(String(64), nullable=False)
	user_id: Mapped[str] = mapped_column(
		String(64), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False
	)
	device_id: Mapped[str | None] = mapped_column(
		String(64), ForeignKey("devices.id", ondelete="CASCADE")
	)
	token_type: Mapped[TokenType] = mapped_column(
		enum_type(TokenType, "token_type"), nullable=False
	)
	issued_at: Mapped[int] = mapped_column(Integer, nullable=False)
	expires_at: Mapped[int] = mapped_column(Integer, nullable=False)
	used_at: Mapped[int | None] = mapped_column(Integer)
	revoked_at: Mapped[int | None] = mapped_column(Integer)
	replaced_by_hash: Mapped[str | None] = mapped_column(String(64))

	__table_args__ = (
		Index("ix_token_records_user_type", "user_id", "token_type"),
		Index("ix_token_records_family", "family_id"),
		Index("ix_token_records_expires", "expires_at"),
	)


class TelemetryEvent(Base):
	__tablename__ = "telemetry_events"

	id: Mapped[str] = mapped_column(String(64), primary_key=True)
	device_id: Mapped[str] = mapped_column(
		String(64), ForeignKey("devices.id", ondelete="RESTRICT"), nullable=False
	)
	case_id: Mapped[str | None] = mapped_column(
		String(64), ForeignKey("cases.id", ondelete="SET NULL")
	)
	event_type: Mapped[str] = mapped_column(String(64), default="vitals", nullable=False)
	timestamp: Mapped[int] = mapped_column(Integer, default=now_ms, nullable=False)
	readings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
	received_at: Mapped[int] = mapped_column(Integer, default=now_ms, nullable=False)

	__table_args__ = (
		Index("ix_telemetry_device_timestamp", "device_id", "timestamp"),
		Index("ix_telemetry_case_timestamp", "case_id", "timestamp"),
	)


class SyncResource(TimestampMixin, Base):
	__tablename__ = "sync_resources"

	id: Mapped[str] = mapped_column(String(64), primary_key=True)
	resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
	resource_id: Mapped[str] = mapped_column(String(64), nullable=False)
	operation: Mapped[SyncOperation] = mapped_column(
		enum_type(SyncOperation, "sync_operation"), default=SyncOperation.UPSERT, nullable=False
	)
	source_device_id: Mapped[str | None] = mapped_column(
		String(64), ForeignKey("devices.id", ondelete="SET NULL")
	)
	version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
	payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
	checksum_sha256: Mapped[str | None] = mapped_column(String(64))
	sync_status: Mapped[SyncStatus] = mapped_column(
		enum_type(SyncStatus, "resource_sync_status"),
		default=SyncStatus.PENDING,
		nullable=False,
	)
	synced_at: Mapped[int | None] = mapped_column(Integer)
	artifact_path: Mapped[str | None] = mapped_column(Text)
	media_type: Mapped[str] = mapped_column(
		String(128), default="application/octet-stream", nullable=False
	)
	size_bytes: Mapped[int | None] = mapped_column(Integer)
	signature: Mapped[str | None] = mapped_column(Text)
	published_at: Mapped[int | None] = mapped_column(Integer)
	active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

	__table_args__ = (
		UniqueConstraint(
			"resource_type", "resource_id", "version", name="uq_sync_resource_version"
		),
		Index("ix_sync_resources_status_created", "sync_status", "created_at"),
		Index("ix_sync_resources_type_active_version", "resource_type", "active", "version"),
	)


class IdempotencyRecord(Base):
	__tablename__ = "idempotency_records"

	id: Mapped[str] = mapped_column(String(64), primary_key=True)
	user_id: Mapped[str] = mapped_column(String(64), nullable=False)
	endpoint: Mapped[str] = mapped_column(String(128), nullable=False)
	idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
	request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
	response_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
	status_code: Mapped[int] = mapped_column(Integer, nullable=False)
	created_at: Mapped[int] = mapped_column(Integer, default=now_ms, nullable=False)
	expires_at: Mapped[int] = mapped_column(Integer, nullable=False)

	__table_args__ = (
		UniqueConstraint(
			"user_id",
			"endpoint",
			"idempotency_key",
			name="uq_idempotency_user_endpoint_key",
		),
		Index("ix_idempotency_expires_at", "expires_at"),
	)


class FLRound(TimestampMixin, Base):
	__tablename__ = "fl_rounds"

	id: Mapped[str] = mapped_column(String(64), primary_key=True)
	device_id: Mapped[str | None] = mapped_column(
		String(64), ForeignKey("devices.id", ondelete="SET NULL")
	)
	base_model_version_id: Mapped[str | None] = mapped_column(
		String(64), ForeignKey("model_versions.id", ondelete="SET NULL")
	)
	result_model_version_id: Mapped[str | None] = mapped_column(
		String(64), ForeignKey("model_versions.id", ondelete="SET NULL")
	)
	round_number: Mapped[int] = mapped_column(Integer, nullable=False)
	status: Mapped[FLRoundStatus] = mapped_column(
		enum_type(FLRoundStatus, "fl_round_status"),
		default=FLRoundStatus.PENDING,
		nullable=False,
	)
	sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
	metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
	started_at: Mapped[int | None] = mapped_column(Integer)
	completed_at: Mapped[int | None] = mapped_column(Integer)

	__table_args__ = (
		UniqueConstraint("device_id", "round_number", name="uq_fl_round_device_number"),
		Index("ix_fl_rounds_status_created", "status", "created_at"),
	)


class PrivacyBudget(TimestampMixin, Base):
	__tablename__ = "privacy_budgets"

	id: Mapped[str] = mapped_column(String(64), primary_key=True)
	device_id: Mapped[str] = mapped_column(
		String(64), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
	)
	scope: Mapped[str] = mapped_column(String(64), default="federated_learning", nullable=False)
	period_start: Mapped[int] = mapped_column(Integer, nullable=False)
	period_end: Mapped[int] = mapped_column(Integer, nullable=False)
	epsilon_limit: Mapped[float] = mapped_column(Float, nullable=False)
	epsilon_spent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
	delta: Mapped[float] = mapped_column(Float, nullable=False)
	last_round_id: Mapped[str | None] = mapped_column(
		String(64), ForeignKey("fl_rounds.id", ondelete="SET NULL")
	)

	__table_args__ = (
		UniqueConstraint(
			"device_id", "scope", "period_start", name="uq_privacy_budget_period"
		),
		Index("ix_privacy_budget_device_period", "device_id", "period_end"),
	)


class ConsentRecord(TimestampMixin, Base):
	__tablename__ = "consent_records"

	id: Mapped[str] = mapped_column(String(64), primary_key=True)
	patient_id: Mapped[str] = mapped_column(
		String(64), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
	)
	consent_type: Mapped[str] = mapped_column(String(64), nullable=False)
	status: Mapped[ConsentStatus] = mapped_column(
		enum_type(ConsentStatus, "consent_status"), nullable=False
	)
	recorded_by: Mapped[str] = mapped_column(String(64), nullable=False)
	recorded_at: Mapped[int] = mapped_column(Integer, default=now_ms, nullable=False)
	expires_at: Mapped[int | None] = mapped_column(Integer)
	withdrawn_at: Mapped[int | None] = mapped_column(Integer)
	evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

	patient: Mapped[Patient] = relationship(back_populates="consents")

	__table_args__ = (
		UniqueConstraint(
			"patient_id", "consent_type", "recorded_at", name="uq_consent_patient_type_time"
		),
		Index("ix_consent_patient_status", "patient_id", "status"),
	)


class AuditEvent(Base):
	__tablename__ = "audit_events"

	id: Mapped[str] = mapped_column(String(64), primary_key=True)
	timestamp: Mapped[int] = mapped_column(Integer, default=now_ms, nullable=False)
	actor_id: Mapped[str | None] = mapped_column(String(64))
	device_id: Mapped[str | None] = mapped_column(
		String(64), ForeignKey("devices.id", ondelete="SET NULL")
	)
	action: Mapped[str] = mapped_column(String(128), nullable=False)
	resource_type: Mapped[str | None] = mapped_column(String(64))
	resource_id: Mapped[str | None] = mapped_column(String(64))
	outcome: Mapped[AuditOutcome] = mapped_column(
		enum_type(AuditOutcome, "audit_outcome"), nullable=False
	)
	details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
	correlation_id: Mapped[str | None] = mapped_column(String(64))

	__table_args__ = (
		Index("ix_audit_timestamp", "timestamp"),
		Index("ix_audit_resource", "resource_type", "resource_id"),
		Index("ix_audit_actor_timestamp", "actor_id", "timestamp"),
	)
