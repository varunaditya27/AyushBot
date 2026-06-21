"""Record pre-triage rules, growth, and model versions.

Revision ID: 0005_pretriage_versions
Revises: 0004_offline_sync_contracts
Create Date: 2026-06-15
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_pretriage_versions"
down_revision = "0004_offline_sync_contracts"
branch_labels = None
depends_on = None


def upgrade() -> None:
	columns = {
		column["name"]
		for column in sa.inspect(op.get_bind()).get_columns("cases")
	}
	missing = {
		"ruleset_version",
		"growth_reference_version",
		"triage_model_version",
	} - columns
	if missing:
		with op.batch_alter_table("cases") as batch_op:
			for name in sorted(missing):
				batch_op.add_column(sa.Column(name, sa.String(length=128)))


def downgrade() -> None:
	with op.batch_alter_table("cases") as batch_op:
		batch_op.drop_column("triage_model_version")
		batch_op.drop_column("growth_reference_version")
		batch_op.drop_column("ruleset_version")
