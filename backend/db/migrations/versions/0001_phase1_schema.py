"""Create the Phase 1 gateway schema.

Revision ID: 0001_phase1
Revises:
Create Date: 2026-06-14
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_phase1"
down_revision = None
branch_labels = None
depends_on = None


RISK_TIER = sa.Enum(
	"LOW",
	"MEDIUM",
	"HIGH",
	"CRITICAL",
	name="risk_tier",
	native_enum=False,
	create_constraint=True,
)
SYNC_STATUS = sa.Enum(
	"PENDING",
	"SYNCED",
	"FAILED",
	"CONFLICT",
	name="sync_status",
	native_enum=False,
	create_constraint=True,
)
FACILITY_TYPE = sa.Enum(
	"SC",
	"PHC",
	"CHC",
	"SDH",
	"DH",
	"OTHER",
	name="facility_type",
	native_enum=False,
	create_constraint=True,
)
FEEDBACK_DISPOSITION = sa.Enum(
	"CONFIRMED",
	"MODIFIED",
	"REJECTED",
	"UNSURE",
	name="feedback_disposition",
	native_enum=False,
	create_constraint=True,
)
MODEL_STATUS = sa.Enum(
	"STAGED",
	"ACTIVE",
	"RETIRED",
	"FAILED",
	name="model_status",
	native_enum=False,
	create_constraint=True,
)
SYNC_OPERATION = sa.Enum(
	"UPSERT",
	"DELETE",
	name="sync_operation",
	native_enum=False,
	create_constraint=True,
)
DEVICE_TYPE = sa.Enum(
	"GATEWAY",
	"ANDROID",
	"SENSOR",
	"CLOUD",
	name="device_type",
	native_enum=False,
	create_constraint=True,
)
DEVICE_STATUS = sa.Enum(
	"ACTIVE",
	"INACTIVE",
	"REVOKED",
	name="device_status",
	native_enum=False,
	create_constraint=True,
)
FL_ROUND_STATUS = sa.Enum(
	"PENDING",
	"TRAINING",
	"READY",
	"SYNCED",
	"FAILED",
	name="fl_round_status",
	native_enum=False,
	create_constraint=True,
)
CONSENT_STATUS = sa.Enum(
	"GRANTED",
	"WITHDRAWN",
	"EXPIRED",
	name="consent_status",
	native_enum=False,
	create_constraint=True,
)
AUDIT_OUTCOME = sa.Enum(
	"SUCCESS",
	"DENIED",
	"FAILURE",
	name="audit_outcome",
	native_enum=False,
	create_constraint=True,
)


def _create_table(*args, **kwargs) -> sa.Table:
	kwargs.setdefault("if_not_exists", True)
	return op.create_table(*args, **kwargs)


def _create_index(*args, **kwargs) -> None:
	kwargs.setdefault("if_not_exists", True)
	op.create_index(*args, **kwargs)


def _timestamps() -> tuple[sa.Column[int], sa.Column[int]]:
	return (
		sa.Column("created_at", sa.Integer(), nullable=False),
		sa.Column("updated_at", sa.Integer(), nullable=False),
	)


def _column_names(inspector: sa.Inspector, table: str) -> set[str]:
	return {column["name"] for column in inspector.get_columns(table)}


def _index_names(inspector: sa.Inspector, table: str) -> set[str]:
	return {index["name"] for index in inspector.get_indexes(table)}


def _add_legacy_columns(bind: sa.Connection) -> None:
	inspector = sa.inspect(bind)
	if "patients" in inspector.get_table_names():
		columns = _column_names(inspector, "patients")
		with op.batch_alter_table("patients") as batch_op:
			if "updated_at" not in columns:
				batch_op.add_column(
					sa.Column("updated_at", sa.Integer(), nullable=False, server_default="0")
				)
		inspector = sa.inspect(bind)
		indexes = _index_names(inspector, "patients")
		if "ix_patients_asha_id" not in indexes:
			_create_index("ix_patients_asha_id", "patients", ["asha_id"])
		if "ix_patients_village" not in indexes:
			_create_index("ix_patients_village", "patients", ["village"])

	if "cases" in inspector.get_table_names():
		columns = _column_names(inspector, "cases")
		with op.batch_alter_table("cases") as batch_op:
			if "created_at" not in columns:
				batch_op.add_column(
					sa.Column("created_at", sa.Integer(), nullable=False, server_default="0")
				)
			if "updated_at" not in columns:
				batch_op.add_column(
					sa.Column("updated_at", sa.Integer(), nullable=False, server_default="0")
				)
		inspector = sa.inspect(bind)
		indexes = _index_names(inspector, "cases")
		if "ix_cases_patient_timestamp" not in indexes:
			_create_index("ix_cases_patient_timestamp", "cases", ["patient_id", "timestamp"])
		if "ix_cases_risk_timestamp" not in indexes:
			_create_index("ix_cases_risk_timestamp", "cases", ["risk_tier", "timestamp"])

	if "recommendations" in inspector.get_table_names():
		columns = _column_names(inspector, "recommendations")
		with op.batch_alter_table("recommendations") as batch_op:
			if "model_version_id" not in columns:
				batch_op.add_column(sa.Column("model_version_id", sa.String(64)))
			if "updated_at" not in columns:
				batch_op.add_column(
					sa.Column("updated_at", sa.Integer(), nullable=False, server_default="0")
				)
		inspector = sa.inspect(bind)
		indexes = _index_names(inspector, "recommendations")
		if "ix_recommendations_model_version_id" not in indexes:
			_create_index(
				"ix_recommendations_model_version_id",
				"recommendations",
				["model_version_id"],
			)


def upgrade() -> None:
	_create_table(
		"villages",
		sa.Column("id", sa.String(64), primary_key=True),
		sa.Column("name", sa.String(256), nullable=False),
		sa.Column("district", sa.String(128)),
		sa.Column("state", sa.String(128)),
		sa.Column("pincode", sa.String(12)),
		sa.Column("latitude", sa.Float()),
		sa.Column("longitude", sa.Float()),
		sa.Column("active", sa.Boolean(), nullable=False),
		sa.Column("metadata_json", sa.JSON(), nullable=False),
		*_timestamps(),
		sa.UniqueConstraint("name", "district", "state", name="uq_villages_location"),
	)
	_create_index("ix_villages_active_name", "villages", ["active", "name"])

	_create_table(
		"facilities",
		sa.Column("id", sa.String(64), primary_key=True),
		sa.Column("name", sa.String(256), nullable=False),
		sa.Column("type", FACILITY_TYPE, nullable=False),
		sa.Column(
			"village_id",
			sa.String(64),
			sa.ForeignKey("villages.id", ondelete="SET NULL"),
		),
		sa.Column("latitude", sa.Float(), nullable=False),
		sa.Column("longitude", sa.Float(), nullable=False),
		sa.Column("address", sa.Text()),
		sa.Column("phone", sa.String(32)),
		sa.Column("active", sa.Boolean(), nullable=False),
		sa.Column("metadata_json", sa.JSON(), nullable=False),
		*_timestamps(),
		sa.UniqueConstraint("name", "latitude", "longitude", name="uq_facilities_location"),
	)
	_create_index("ix_facilities_type_active", "facilities", ["type", "active"])
	_create_index("ix_facilities_village_id", "facilities", ["village_id"])

	_create_table(
		"road_edges",
		sa.Column("id", sa.String(64), primary_key=True),
		sa.Column("from_node_id", sa.String(64), nullable=False),
		sa.Column("to_node_id", sa.String(64), nullable=False),
		sa.Column("distance_km", sa.Float(), nullable=False),
		sa.Column("travel_time_minutes", sa.Integer()),
		sa.Column("road_class", sa.String(64)),
		sa.Column("bidirectional", sa.Boolean(), nullable=False),
		sa.Column("active", sa.Boolean(), nullable=False),
		sa.Column("metadata_json", sa.JSON(), nullable=False),
		*_timestamps(),
		sa.UniqueConstraint("from_node_id", "to_node_id", name="uq_road_edges_nodes"),
	)
	_create_index("ix_road_edges_from_active", "road_edges", ["from_node_id", "active"])
	_create_index("ix_road_edges_to_active", "road_edges", ["to_node_id", "active"])

	_create_table(
		"patients",
		sa.Column("id", sa.String(64), primary_key=True),
		sa.Column("abha_id", sa.String(64)),
		sa.Column("name", sa.String(256)),
		sa.Column("age_months", sa.Integer(), nullable=False),
		sa.Column("sex", sa.String(16), nullable=False),
		sa.Column("village", sa.String(128)),
		sa.Column("asha_id", sa.String(64), nullable=False),
		*_timestamps(),
		sa.UniqueConstraint("abha_id", name="uq_patients_abha_id"),
	)
	_create_index("ix_patients_asha_id", "patients", ["asha_id"])
	_create_index("ix_patients_village", "patients", ["village"])

	_create_table(
		"devices",
		sa.Column("id", sa.String(64), primary_key=True),
		sa.Column("device_type", DEVICE_TYPE, nullable=False),
		sa.Column("status", DEVICE_STATUS, nullable=False),
		sa.Column("owner_id", sa.String(64)),
		sa.Column("display_name", sa.String(128)),
		sa.Column("public_key_fingerprint", sa.String(128)),
		sa.Column("app_version", sa.String(64)),
		sa.Column("last_seen_at", sa.Integer()),
		sa.Column("metadata_json", sa.JSON(), nullable=False),
		*_timestamps(),
		sa.UniqueConstraint(
			"public_key_fingerprint", name="uq_devices_public_key_fingerprint"
		),
	)
	_create_index("ix_devices_type_status", "devices", ["device_type", "status"])

	_create_table(
		"model_versions",
		sa.Column("id", sa.String(64), primary_key=True),
		sa.Column("model_name", sa.String(128), nullable=False),
		sa.Column("version", sa.String(64), nullable=False),
		sa.Column("status", MODEL_STATUS, nullable=False),
		sa.Column("artifact_uri", sa.Text()),
		sa.Column("checksum_sha256", sa.String(64)),
		sa.Column("metrics", sa.JSON(), nullable=False),
		sa.Column("activated_at", sa.Integer()),
		*_timestamps(),
		sa.UniqueConstraint("model_name", "version", name="uq_model_versions_name_version"),
	)
	_create_index(
		"ix_model_versions_name_status", "model_versions", ["model_name", "status"]
	)
	_add_legacy_columns(op.get_bind())

	_create_table(
		"cases",
		sa.Column("id", sa.String(64), primary_key=True),
		sa.Column(
			"patient_id",
			sa.String(64),
			sa.ForeignKey("patients.id", ondelete="CASCADE"),
			nullable=False,
		),
		sa.Column("timestamp", sa.Integer(), nullable=False),
		sa.Column("spo2", sa.Float()),
		sa.Column("heart_rate", sa.Float()),
		sa.Column("temperature", sa.Float()),
		sa.Column("weight", sa.Float()),
		sa.Column("symptoms", sa.JSON(), nullable=False),
		sa.Column("risk_tier", RISK_TIER, nullable=False),
		sa.Column("sync_status", SYNC_STATUS, nullable=False),
		*_timestamps(),
	)
	_create_index("ix_cases_patient_timestamp", "cases", ["patient_id", "timestamp"])
	_create_index("ix_cases_sync_status", "cases", ["sync_status"])
	_create_index("ix_cases_risk_timestamp", "cases", ["risk_tier", "timestamp"])

	_create_table(
		"recommendations",
		sa.Column("id", sa.String(64), primary_key=True),
		sa.Column(
			"case_id",
			sa.String(64),
			sa.ForeignKey("cases.id", ondelete="CASCADE"),
			nullable=False,
		),
		sa.Column(
			"model_version_id",
			sa.String(64),
			sa.ForeignKey("model_versions.id", ondelete="SET NULL"),
		),
		sa.Column("primary_diagnosis", sa.String(256), nullable=False),
		sa.Column("confidence", sa.String(16), nullable=False),
		sa.Column("differential_json", sa.JSON(), nullable=False),
		sa.Column("action_plan", sa.JSON(), nullable=False),
		sa.Column("referral_facility", sa.String(128)),
		sa.Column("drug_dosage", sa.String(256)),
		sa.Column("counseling", sa.Text()),
		sa.Column("citation_source", sa.String(256)),
		sa.Column("citation_text", sa.Text()),
		*_timestamps(),
		sa.UniqueConstraint("case_id", name="uq_recommendations_case_id"),
	)
	_create_index(
		"ix_recommendations_model_version_id",
		"recommendations",
		["model_version_id"],
	)

	_create_table(
		"clinical_feedback",
		sa.Column("id", sa.String(64), primary_key=True),
		sa.Column(
			"case_id",
			sa.String(64),
			sa.ForeignKey("cases.id", ondelete="CASCADE"),
			nullable=False,
		),
		sa.Column(
			"recommendation_id",
			sa.String(64),
			sa.ForeignKey("recommendations.id", ondelete="SET NULL"),
		),
		sa.Column("reviewer_id", sa.String(64), nullable=False),
		sa.Column("disposition", FEEDBACK_DISPOSITION, nullable=False),
		sa.Column("confirmed_diagnosis", sa.String(256)),
		sa.Column("notes", sa.Text()),
		sa.Column("structured_feedback", sa.JSON(), nullable=False),
		*_timestamps(),
		sa.UniqueConstraint("case_id", "reviewer_id", name="uq_feedback_case_reviewer"),
	)
	_create_index("ix_feedback_case_created", "clinical_feedback", ["case_id", "created_at"])

	_create_table(
		"telemetry_events",
		sa.Column("id", sa.String(64), primary_key=True),
		sa.Column(
			"device_id",
			sa.String(64),
			sa.ForeignKey("devices.id", ondelete="RESTRICT"),
			nullable=False,
		),
		sa.Column(
			"case_id",
			sa.String(64),
			sa.ForeignKey("cases.id", ondelete="SET NULL"),
		),
		sa.Column("event_type", sa.String(64), nullable=False),
		sa.Column("timestamp", sa.Integer(), nullable=False),
		sa.Column("readings", sa.JSON(), nullable=False),
		sa.Column("received_at", sa.Integer(), nullable=False),
	)
	_create_index(
		"ix_telemetry_device_timestamp",
		"telemetry_events",
		["device_id", "timestamp"],
	)
	_create_index(
		"ix_telemetry_case_timestamp",
		"telemetry_events",
		["case_id", "timestamp"],
	)

	_create_table(
		"sync_resources",
		sa.Column("id", sa.String(64), primary_key=True),
		sa.Column("resource_type", sa.String(64), nullable=False),
		sa.Column("resource_id", sa.String(64), nullable=False),
		sa.Column("operation", SYNC_OPERATION, nullable=False),
		sa.Column(
			"source_device_id",
			sa.String(64),
			sa.ForeignKey("devices.id", ondelete="SET NULL"),
		),
		sa.Column("version", sa.Integer(), nullable=False),
		sa.Column("payload", sa.JSON(), nullable=False),
		sa.Column("checksum_sha256", sa.String(64)),
		sa.Column(
			"sync_status",
			sa.Enum(
				"PENDING",
				"SYNCED",
				"FAILED",
				"CONFLICT",
				name="resource_sync_status",
				native_enum=False,
				create_constraint=True,
			),
			nullable=False,
		),
		sa.Column("synced_at", sa.Integer()),
		*_timestamps(),
		sa.UniqueConstraint(
			"resource_type", "resource_id", "version", name="uq_sync_resource_version"
		),
	)
	_create_index(
		"ix_sync_resources_status_created",
		"sync_resources",
		["sync_status", "created_at"],
	)

	_create_table(
		"fl_rounds",
		sa.Column("id", sa.String(64), primary_key=True),
		sa.Column(
			"device_id",
			sa.String(64),
			sa.ForeignKey("devices.id", ondelete="SET NULL"),
		),
		sa.Column(
			"base_model_version_id",
			sa.String(64),
			sa.ForeignKey("model_versions.id", ondelete="SET NULL"),
		),
		sa.Column(
			"result_model_version_id",
			sa.String(64),
			sa.ForeignKey("model_versions.id", ondelete="SET NULL"),
		),
		sa.Column("round_number", sa.Integer(), nullable=False),
		sa.Column("status", FL_ROUND_STATUS, nullable=False),
		sa.Column("sample_count", sa.Integer(), nullable=False),
		sa.Column("metrics", sa.JSON(), nullable=False),
		sa.Column("started_at", sa.Integer()),
		sa.Column("completed_at", sa.Integer()),
		*_timestamps(),
		sa.UniqueConstraint("device_id", "round_number", name="uq_fl_round_device_number"),
	)
	_create_index("ix_fl_rounds_status_created", "fl_rounds", ["status", "created_at"])

	_create_table(
		"privacy_budgets",
		sa.Column("id", sa.String(64), primary_key=True),
		sa.Column(
			"device_id",
			sa.String(64),
			sa.ForeignKey("devices.id", ondelete="CASCADE"),
			nullable=False,
		),
		sa.Column("scope", sa.String(64), nullable=False),
		sa.Column("period_start", sa.Integer(), nullable=False),
		sa.Column("period_end", sa.Integer(), nullable=False),
		sa.Column("epsilon_limit", sa.Float(), nullable=False),
		sa.Column("epsilon_spent", sa.Float(), nullable=False),
		sa.Column("delta", sa.Float(), nullable=False),
		sa.Column(
			"last_round_id",
			sa.String(64),
			sa.ForeignKey("fl_rounds.id", ondelete="SET NULL"),
		),
		*_timestamps(),
		sa.UniqueConstraint(
			"device_id", "scope", "period_start", name="uq_privacy_budget_period"
		),
	)
	_create_index(
		"ix_privacy_budget_device_period",
		"privacy_budgets",
		["device_id", "period_end"],
	)

	_create_table(
		"consent_records",
		sa.Column("id", sa.String(64), primary_key=True),
		sa.Column(
			"patient_id",
			sa.String(64),
			sa.ForeignKey("patients.id", ondelete="CASCADE"),
			nullable=False,
		),
		sa.Column("consent_type", sa.String(64), nullable=False),
		sa.Column("status", CONSENT_STATUS, nullable=False),
		sa.Column("recorded_by", sa.String(64), nullable=False),
		sa.Column("recorded_at", sa.Integer(), nullable=False),
		sa.Column("expires_at", sa.Integer()),
		sa.Column("withdrawn_at", sa.Integer()),
		sa.Column("evidence", sa.JSON(), nullable=False),
		*_timestamps(),
		sa.UniqueConstraint(
			"patient_id", "consent_type", "recorded_at", name="uq_consent_patient_type_time"
		),
	)
	_create_index("ix_consent_patient_status", "consent_records", ["patient_id", "status"])

	_create_table(
		"audit_events",
		sa.Column("id", sa.String(64), primary_key=True),
		sa.Column("timestamp", sa.Integer(), nullable=False),
		sa.Column("actor_id", sa.String(64)),
		sa.Column(
			"device_id",
			sa.String(64),
			sa.ForeignKey("devices.id", ondelete="SET NULL"),
		),
		sa.Column("action", sa.String(128), nullable=False),
		sa.Column("resource_type", sa.String(64)),
		sa.Column("resource_id", sa.String(64)),
		sa.Column("outcome", AUDIT_OUTCOME, nullable=False),
		sa.Column("details", sa.JSON(), nullable=False),
		sa.Column("correlation_id", sa.String(64)),
	)
	_create_index("ix_audit_timestamp", "audit_events", ["timestamp"])
	_create_index("ix_audit_resource", "audit_events", ["resource_type", "resource_id"])
	_create_index(
		"ix_audit_actor_timestamp", "audit_events", ["actor_id", "timestamp"]
	)
	_add_legacy_columns(op.get_bind())


def downgrade() -> None:
	for table_name in (
		"audit_events",
		"consent_records",
		"privacy_budgets",
		"fl_rounds",
		"sync_resources",
		"telemetry_events",
		"clinical_feedback",
		"recommendations",
		"cases",
		"model_versions",
		"devices",
		"patients",
		"road_edges",
		"facilities",
		"villages",
	):
		op.drop_table(table_name)
