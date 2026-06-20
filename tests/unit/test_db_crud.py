from __future__ import annotations

import json

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from backend.db import crud
from backend.db.models import Base
from backend.db.seed import seed_reference_data


@pytest.fixture()
def db(tmp_path):
	engine = create_engine(f"sqlite:///{tmp_path / 'crud.db'}")

	@event.listens_for(engine, "connect")
	def _foreign_keys(connection, _record):
		connection.execute("PRAGMA foreign_keys=ON")

	Base.metadata.create_all(engine)
	with Session(engine, expire_on_commit=False) as session:
		yield session


def _patient(patient_id: str = "patient-synthetic-1") -> dict:
	return {
		"id": patient_id,
		"age_months": 24,
		"sex": "female",
		"village": "village-synthetic-1",
		"asha_id": "asha-synthetic-1",
	}


def test_core_crud_preserves_legacy_json_inputs(db):
	crud.create_patient(db, _patient())
	case = crud.create_case(
		db,
		{
			"id": "case-synthetic-1",
			"patient_id": "patient-synthetic-1",
			"symptoms": '["fever", "cough"]',
			"risk_tier": "HIGH",
		},
	)
	recommendation = crud.create_recommendation(
		db,
		{
			"id": "recommendation-synthetic-1",
			"case_id": case.id,
			"primary_diagnosis": "Synthetic diagnosis",
			"differential_json": '{"diagnoses": [{"name": "Synthetic"}]}',
			"action_plan": '{"urgency": "ROUTINE"}',
		},
	)
	db.commit()

	assert case.symptoms == ["fever", "cough"]
	assert recommendation.differential_json["diagnoses"][0]["name"] == "Synthetic"
	assert recommendation.action_plan == {"urgency": "ROUTINE"}


def test_integrity_failure_does_not_discard_other_session_work(db):
	crud.create_patient(db, _patient())
	with pytest.raises(ValueError):
		crud.create_patient(db, _patient())

	second = crud.create_patient(db, _patient("patient-synthetic-2"))
	db.commit()
	assert second.id == "patient-synthetic-2"
	assert len(crud.list_patients(db)) == 2


def test_update_integrity_failure_isolated_by_savepoint(db):
	crud.create_patient(db, {**_patient("patient-synthetic-1"), "abha_id": "abha-1"})
	crud.create_patient(db, {**_patient("patient-synthetic-2"), "abha_id": "abha-2"})
	with pytest.raises(ValueError):
		crud.update_patient(
			db, "patient-synthetic-2", {"abha_id": "abha-1"}
		)
	third = crud.create_patient(db, _patient("patient-synthetic-3"))
	db.commit()
	assert third.id == "patient-synthetic-3"


def test_operational_services_and_privacy_budget_guard(db):
	crud.create_patient(db, _patient())
	crud.register_device(
		db,
		{"id": "device-synthetic-1", "device_type": "GATEWAY", "status": "ACTIVE"},
	)
	crud.register_model_version(
		db,
		{
			"id": "model-synthetic-1",
			"model_name": "triage",
			"version": "0.0-test",
			"status": "STAGED",
		},
	)
	round_record = crud.create_fl_round(
		db,
		{
			"id": "round-synthetic-1",
			"device_id": "device-synthetic-1",
			"round_number": 1,
		},
	)
	budget = crud.create_privacy_budget(
		db,
		{
			"id": "budget-synthetic-1",
			"device_id": "device-synthetic-1",
			"period_start": 1,
			"period_end": 9999999999999,
			"epsilon_limit": 2.0,
			"epsilon_spent": 0.0,
			"delta": 0.000001,
		},
	)
	crud.spend_privacy_budget(db, budget.id, 0.5, round_record.id)
	with pytest.raises(ValueError, match="exceeded"):
		crud.spend_privacy_budget(db, budget.id, 2.0, round_record.id)

	crud.create_consent_record(
		db,
		{
			"id": "consent-synthetic-1",
			"patient_id": "patient-synthetic-1",
			"consent_type": "care_delivery",
			"status": "GRANTED",
			"recorded_by": "asha-synthetic-1",
		},
	)
	crud.create_audit_event(
		db,
		{
			"id": "audit-synthetic-1",
			"actor_id": "asha-synthetic-1",
			"device_id": "device-synthetic-1",
			"action": "synthetic.test",
			"outcome": "SUCCESS",
			"details": {"contains_patient_data": False},
		},
	)
	db.commit()
	assert budget.epsilon_spent == 0.5


def test_seed_reference_data_upserts_validated_records(db, tmp_path):
	villages = tmp_path / "villages.json"
	facilities = tmp_path / "facilities.csv"
	villages.write_text(
		json.dumps(
			[
				{
					"id": "village-synthetic-1",
					"name": "Synthetic Village",
					"latitude": 12.0,
					"longitude": 77.0,
				}
			]
		),
		encoding="utf-8",
	)
	facilities.write_text(
		"id,name,type,village_id,latitude,longitude,address,phone,active,metadata_json\n"
		"facility-synthetic-1,Synthetic PHC,PHC,village-synthetic-1,12.1,77.1,"
		"Synthetic address,,true,\"{\"\"source\"\":\"\"test\"\"}\"\n",
		encoding="utf-8",
	)

	counts = seed_reference_data(
		db, villages=villages, facilities=facilities
	)
	assert counts == {"villages": 1, "facilities": 1}
	assert crud.get_facility(db, "facility-synthetic-1").type.value == "PHC"


def test_seed_reference_data_rolls_back_unknown_village(db, tmp_path):
	facilities = tmp_path / "facilities.json"
	facilities.write_text(
		json.dumps(
			[
				{
					"id": "facility-invalid",
					"name": "Invalid Synthetic Facility",
					"type": "PHC",
					"village_id": "missing-village",
					"latitude": 12.0,
					"longitude": 77.0,
				}
			]
		),
		encoding="utf-8",
	)
	with pytest.raises(ValueError, match="unknown village"):
		seed_reference_data(db, facilities=facilities)
	assert crud.get_facility(db, "facility-invalid") is None
