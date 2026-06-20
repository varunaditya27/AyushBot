"""Add authentication and token security tables.

Revision ID: 0002_auth_security
Revises: 0001_phase1
Create Date: 2026-06-14
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_auth_security"
down_revision = "0001_phase1"
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.create_table(
		"user_accounts",
		sa.Column("id", sa.String(64), primary_key=True),
		sa.Column("username", sa.String(128), nullable=False),
		sa.Column("password_hash", sa.Text(), nullable=False),
		sa.Column(
			"role",
			sa.Enum(
				"AshaWorker",
				"MedicalOfficer",
				name="user_role",
				native_enum=False,
				create_constraint=True,
			),
			nullable=False,
		),
		sa.Column("display_name", sa.String(256)),
		sa.Column("active", sa.Boolean(), nullable=False),
		sa.Column("password_changed_at", sa.Integer(), nullable=False),
		sa.Column("last_login_at", sa.Integer()),
		sa.Column("created_at", sa.Integer(), nullable=False),
		sa.Column("updated_at", sa.Integer(), nullable=False),
		sa.UniqueConstraint("username", name="uq_user_accounts_username"),
	)
	op.create_index(
		"ix_user_accounts_role_active", "user_accounts", ["role", "active"]
	)
	op.create_table(
		"token_records",
		sa.Column("id", sa.String(64), primary_key=True),
		sa.Column("jti_hash", sa.String(64), nullable=False),
		sa.Column("family_id", sa.String(64), nullable=False),
		sa.Column(
			"user_id",
			sa.String(64),
			sa.ForeignKey("user_accounts.id", ondelete="CASCADE"),
			nullable=False,
		),
		sa.Column(
			"device_id",
			sa.String(64),
			sa.ForeignKey("devices.id", ondelete="CASCADE"),
		),
		sa.Column(
			"token_type",
			sa.Enum(
				"access",
				"refresh",
				name="token_type",
				native_enum=False,
				create_constraint=True,
			),
			nullable=False,
		),
		sa.Column("issued_at", sa.Integer(), nullable=False),
		sa.Column("expires_at", sa.Integer(), nullable=False),
		sa.Column("used_at", sa.Integer()),
		sa.Column("revoked_at", sa.Integer()),
		sa.Column("replaced_by_hash", sa.String(64)),
		sa.UniqueConstraint("jti_hash", name="uq_token_records_jti_hash"),
	)
	op.create_index("ix_token_records_user_type", "token_records", ["user_id", "token_type"])
	op.create_index("ix_token_records_family", "token_records", ["family_id"])
	op.create_index("ix_token_records_expires", "token_records", ["expires_at"])


def downgrade() -> None:
	op.drop_table("token_records")
	op.drop_table("user_accounts")
