from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

pytest.importorskip("alembic")

from backend.db.migrate import downgrade, upgrade
from backend.db.models import Case, Recommendation


EXPECTED_TABLES = {
	"alembic_version",
	"audit_events",
	"cases",
	"clinical_feedback",
	"consent_records",
	"devices",
	"facilities",
	"fl_rounds",
	"idempotency_records",
	"model_versions",
	"patients",
	"privacy_budgets",
	"recommendations",
	"road_edges",
	"sync_resources",
	"telemetry_events",
	"token_records",
	"user_accounts",
	"villages",
}


def _url(path: Path) -> str:
	return f"sqlite:///{path}"


def test_fresh_upgrade_and_downgrade(tmp_path):
	database = tmp_path / "fresh.db"
	url = _url(database)
	upgrade(url)
	engine = sa.create_engine(url)
	inspector = sa.inspect(engine)
	assert EXPECTED_TABLES <= set(inspector.get_table_names())
	assert {"ix_cases_patient_timestamp", "ix_cases_risk_timestamp"} <= {
		index["name"] for index in inspector.get_indexes("cases")
	}
	assert any(
		key["referred_table"] == "patients"
		for key in inspector.get_foreign_keys("cases")
	)

	downgrade(url)
	assert set(sa.inspect(engine).get_table_names()) == {"alembic_version"}


def test_upgrade_preserves_legacy_core_records(tmp_path):
	database = tmp_path / "legacy.db"
	url = _url(database)
	engine = sa.create_engine(url)
	with engine.begin() as connection:
		connection.exec_driver_sql(
			"CREATE TABLE patients (id VARCHAR(64) PRIMARY KEY, abha_id VARCHAR(64), "
			"name VARCHAR(256), age_months INTEGER NOT NULL, sex VARCHAR(16) NOT NULL, "
			"village VARCHAR(128), asha_id VARCHAR(64) NOT NULL, created_at INTEGER NOT NULL)"
		)
		connection.exec_driver_sql(
			"CREATE TABLE cases (id VARCHAR(64) PRIMARY KEY, patient_id VARCHAR(64) NOT NULL, "
			"timestamp INTEGER NOT NULL, spo2 FLOAT, heart_rate FLOAT, temperature FLOAT, "
			"weight FLOAT, symptoms TEXT NOT NULL, risk_tier VARCHAR(16) NOT NULL, "
			"sync_status VARCHAR(16) NOT NULL, FOREIGN KEY(patient_id) REFERENCES patients(id))"
		)
		connection.exec_driver_sql(
			"CREATE TABLE recommendations (id VARCHAR(64) PRIMARY KEY, case_id VARCHAR(64) "
			"NOT NULL UNIQUE, primary_diagnosis VARCHAR(256) NOT NULL, confidence VARCHAR(16) "
			"NOT NULL, differential_json TEXT NOT NULL, action_plan TEXT NOT NULL, "
			"referral_facility VARCHAR(128), drug_dosage VARCHAR(256), counseling TEXT, "
			"citation_source VARCHAR(256), citation_text TEXT, created_at INTEGER NOT NULL, "
			"FOREIGN KEY(case_id) REFERENCES cases(id))"
		)
		connection.exec_driver_sql(
			"INSERT INTO patients VALUES "
			"('patient-synthetic-1', NULL, NULL, 24, 'female', 'village-synthetic', "
			"'asha-synthetic', 1)"
		)
		connection.exec_driver_sql(
			"INSERT INTO cases VALUES "
			"('case-synthetic-1', 'patient-synthetic-1', 2, 98, 100, 37, 10, "
			"'[\"fever\"]', 'LOW', 'PENDING')"
		)
		connection.exec_driver_sql(
			"INSERT INTO recommendations VALUES "
			"('recommendation-synthetic-1', 'case-synthetic-1', 'Synthetic', 'Low', "
			"'[]', '{\"urgency\":\"ROUTINE\"}', NULL, NULL, NULL, NULL, NULL, 3)"
		)

	upgrade(url)
	with Session(engine) as session:
		case = session.get(Case, "case-synthetic-1")
		recommendation = session.get(Recommendation, "recommendation-synthetic-1")
		assert case is not None and case.symptoms == ["fever"]
		assert recommendation is not None
		assert recommendation.action_plan == {"urgency": "ROUTINE"}
		assert recommendation.updated_at is not None
