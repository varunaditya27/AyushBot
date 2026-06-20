"""Add offline sync contracts and resource metadata.

Revision ID: 0004_offline_sync_contracts
Revises: 0003_normalize_legacy_core_schema
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_offline_sync_contracts"
down_revision = "0003_normalize_legacy_core_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
	bind = op.get_bind()
	inspector = sa.inspect(bind)

	patient_columns = {column["name"] for column in inspector.get_columns("patients")}
	if "version" not in patient_columns:
		with op.batch_alter_table("patients") as batch_op:
			batch_op.add_column(
				sa.Column("version", sa.Integer(), nullable=False, server_default="1")
			)

	case_columns = {column["name"] for column in inspector.get_columns("cases")}
	missing_case_columns = {
		"version",
		"risk_explanation",
		"errors",
	} - case_columns
	if missing_case_columns:
		with op.batch_alter_table("cases") as batch_op:
			if "version" in missing_case_columns:
				batch_op.add_column(
					sa.Column("version", sa.Integer(), nullable=False, server_default="1")
				)
			if "risk_explanation" in missing_case_columns:
				batch_op.add_column(
					sa.Column(
						"risk_explanation", sa.JSON(), nullable=False, server_default="{}"
					)
				)
			if "errors" in missing_case_columns:
				batch_op.add_column(
					sa.Column("errors", sa.JSON(), nullable=False, server_default="[]")
				)

	recommendation_columns = {
		column["name"] for column in inspector.get_columns("recommendations")
	}
	missing_recommendation_columns = {
		"citations",
		"version",
	} - recommendation_columns
	if missing_recommendation_columns:
		with op.batch_alter_table("recommendations") as batch_op:
			if "citations" in missing_recommendation_columns:
				batch_op.add_column(
					sa.Column(
						"citations", sa.JSON(), nullable=False, server_default="[]"
					)
				)
			if "version" in missing_recommendation_columns:
				batch_op.add_column(
					sa.Column("version", sa.Integer(), nullable=False, server_default="1")
				)

	resource_columns = {
		column["name"] for column in inspector.get_columns("sync_resources")
	}
	missing_resource_columns = {
		"artifact_path",
		"media_type",
		"size_bytes",
		"signature",
		"published_at",
		"active",
	} - resource_columns
	resource_indexes = {
		index["name"] for index in inspector.get_indexes("sync_resources")
	}
	if missing_resource_columns or (
		"ix_sync_resources_type_active_version" not in resource_indexes
	):
		with op.batch_alter_table("sync_resources") as batch_op:
			if "artifact_path" in missing_resource_columns:
				batch_op.add_column(sa.Column("artifact_path", sa.Text(), nullable=True))
			if "media_type" in missing_resource_columns:
				batch_op.add_column(
					sa.Column(
						"media_type",
						sa.String(length=128),
						nullable=False,
						server_default="application/octet-stream",
					)
				)
			if "size_bytes" in missing_resource_columns:
				batch_op.add_column(sa.Column("size_bytes", sa.Integer(), nullable=True))
			if "signature" in missing_resource_columns:
				batch_op.add_column(sa.Column("signature", sa.Text(), nullable=True))
			if "published_at" in missing_resource_columns:
				batch_op.add_column(sa.Column("published_at", sa.Integer(), nullable=True))
			if "active" in missing_resource_columns:
				batch_op.add_column(
					sa.Column(
						"active", sa.Boolean(), nullable=False, server_default=sa.true()
					)
				)
			if "ix_sync_resources_type_active_version" not in resource_indexes:
				batch_op.create_index(
					"ix_sync_resources_type_active_version",
					["resource_type", "active", "version"],
				)

	if "idempotency_records" not in inspector.get_table_names():
		op.create_table(
			"idempotency_records",
			sa.Column("id", sa.String(length=64), nullable=False),
			sa.Column("user_id", sa.String(length=64), nullable=False),
			sa.Column("endpoint", sa.String(length=128), nullable=False),
			sa.Column("idempotency_key", sa.String(length=128), nullable=False),
			sa.Column("request_hash", sa.String(length=64), nullable=False),
			sa.Column("response_payload", sa.JSON(), nullable=False),
			sa.Column("status_code", sa.Integer(), nullable=False),
			sa.Column("created_at", sa.Integer(), nullable=False),
			sa.Column("expires_at", sa.Integer(), nullable=False),
			sa.PrimaryKeyConstraint("id"),
			sa.UniqueConstraint(
				"user_id",
				"endpoint",
				"idempotency_key",
				name="uq_idempotency_user_endpoint_key",
			),
		)
		op.create_index(
			"ix_idempotency_expires_at",
			"idempotency_records",
			["expires_at"],
		)


def downgrade() -> None:
	op.drop_index("ix_idempotency_expires_at", table_name="idempotency_records")
	op.drop_table("idempotency_records")

	with op.batch_alter_table("sync_resources") as batch_op:
		batch_op.drop_index("ix_sync_resources_type_active_version")
		for column in (
			"active",
			"published_at",
			"signature",
			"size_bytes",
			"media_type",
			"artifact_path",
		):
			batch_op.drop_column(column)

	with op.batch_alter_table("recommendations") as batch_op:
		batch_op.drop_column("version")
		batch_op.drop_column("citations")

	with op.batch_alter_table("cases") as batch_op:
		batch_op.drop_column("errors")
		batch_op.drop_column("risk_explanation")
		batch_op.drop_column("version")

	with op.batch_alter_table("patients") as batch_op:
		batch_op.drop_column("version")
