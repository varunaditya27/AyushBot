"""Normalize legacy patient, case, and recommendation columns.

Revision ID: 0003_normalize_legacy_core_schema
Revises: 0002_auth_security
Create Date: 2026-06-14
"""

from collections.abc import Iterable

from alembic import op
import sqlalchemy as sa


revision = "0003_normalize_legacy_core_schema"
down_revision = "0002_auth_security"
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


def _has_unique_constraint(
    inspector: sa.Inspector,
    table_name: str,
    columns: Iterable[str],
) -> bool:
    expected = set(columns)
    return any(
        set(constraint.get("column_names") or []) == expected
        for constraint in inspector.get_unique_constraints(table_name)
    )


def _has_check_constraint(
    inspector: sa.Inspector,
    table_name: str,
    constraint_name: str,
) -> bool:
    return any(
        constraint.get("name") == constraint_name
        for constraint in inspector.get_check_constraints(table_name)
    )


def _column_type(
    inspector: sa.Inspector,
    table_name: str,
    column_name: str,
) -> sa.types.TypeEngine:
    return next(
        column["type"]
        for column in inspector.get_columns(table_name)
        if column["name"] == column_name
    )


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if not _has_unique_constraint(inspector, "patients", ["abha_id"]):
        duplicate = connection.execute(
            sa.text(
                """
                SELECT abha_id
                FROM patients
                WHERE abha_id IS NOT NULL
                GROUP BY abha_id
                HAVING COUNT(*) > 1
                LIMIT 1
                """
            )
        ).scalar_one_or_none()
        if duplicate is not None:
            raise RuntimeError(
                "Cannot enforce unique patients.abha_id: duplicate non-null "
                f"value found ({duplicate!r})"
            )
        with op.batch_alter_table("patients") as batch_op:
            batch_op.create_unique_constraint("uq_patients_abha_id", ["abha_id"])

    case_changes = (
        not isinstance(_column_type(inspector, "cases", "symptoms"), sa.JSON),
        not _has_check_constraint(inspector, "cases", "risk_tier"),
        not _has_check_constraint(inspector, "cases", "sync_status"),
    )
    if any(case_changes):
        connection.execute(
            sa.text(
                "UPDATE cases SET symptoms = '[]' "
                "WHERE symptoms IS NULL OR trim(symptoms) = ''"
            )
        )
        with op.batch_alter_table("cases") as batch_op:
            if case_changes[0]:
                batch_op.alter_column(
                    "symptoms",
                    existing_type=sa.Text(),
                    type_=sa.JSON(),
                    existing_nullable=False,
                )
            if case_changes[1]:
                batch_op.alter_column(
                    "risk_tier",
                    existing_type=sa.String(length=50),
                    type_=RISK_TIER,
                    existing_nullable=True,
                )
            if case_changes[2]:
                batch_op.alter_column(
                    "sync_status",
                    existing_type=sa.String(length=50),
                    type_=SYNC_STATUS,
                    existing_nullable=False,
                )

    recommendation_changes = (
        not isinstance(
            _column_type(inspector, "recommendations", "differential_json"),
            sa.JSON,
        ),
        not isinstance(
            _column_type(inspector, "recommendations", "action_plan"),
            sa.JSON,
        ),
    )
    if any(recommendation_changes):
        connection.execute(
            sa.text(
                "UPDATE recommendations SET differential_json = '[]' "
                "WHERE differential_json IS NULL "
                "OR trim(differential_json) = ''"
            )
        )
        connection.execute(
            sa.text(
                "UPDATE recommendations SET action_plan = '{}' "
                "WHERE action_plan IS NULL OR trim(action_plan) = ''"
            )
        )
        with op.batch_alter_table("recommendations") as batch_op:
            if recommendation_changes[0]:
                batch_op.alter_column(
                    "differential_json",
                    existing_type=sa.Text(),
                    type_=sa.JSON(),
                    existing_nullable=True,
                )
            if recommendation_changes[1]:
                batch_op.alter_column(
                    "action_plan",
                    existing_type=sa.Text(),
                    type_=sa.JSON(),
                    existing_nullable=True,
                )


def downgrade() -> None:
    # This revision conditionally repairs legacy installations. Reversing it
    # could remove constraints that were already present before the upgrade.
    # Earlier revisions still provide a complete schema downgrade.
    pass
