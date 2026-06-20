from __future__ import annotations

import sqlite3
from typing import Dict

import pytest

from backend.agents.schemas.patient_assessment import PatientAssessment
from backend.agents.state import PatientState, state_from_assessment
from backend.config import clear_settings_cache


@pytest.fixture(autouse=True)
def _clear_config_cache():
	clear_settings_cache()
	yield
	clear_settings_cache()


@pytest.fixture()
def sample_patient_state() -> PatientState:
	assessment = PatientAssessment(
		patient_id="patient-1",
		patient_name="Demo",
		age_months=18,
		sex="female",
		weight_kg=8.2,
		village_id="village-1",
		asha_id="asha-1",
		symptom_text="fever and cough",
	)
	state = state_from_assessment(assessment)
	state["raw_vitals"] = {
		"spo2": 92,
		"heart_rate": 140,
		"temperature_celsius": 38.5,
	}
	state["translated_symptoms"] = ["fever", "cough", "fast_breathing"]
	return state


@pytest.fixture()
def sample_facility_db(tmp_path) -> Dict[str, str]:
	db_path = tmp_path / "facilities.db"
	conn = sqlite3.connect(db_path)
	try:
		conn.execute(
			"CREATE TABLE facilities (id TEXT, name TEXT, type TEXT, latitude REAL, "
			"longitude REAL, address TEXT, phone TEXT)"
		)
		conn.execute(
			"INSERT INTO facilities VALUES (?, ?, ?, ?, ?, ?, ?)",
			("fac-1", "District Hospital", "DH", 12.0, 77.0, "Main Road", "123"),
		)
		conn.execute(
			"INSERT INTO facilities VALUES (?, ?, ?, ?, ?, ?, ?)",
			("fac-2", "Community Health Centre", "CHC", 12.1, 77.1, "Town", "456"),
		)
		conn.commit()
	finally:
		conn.close()
	return {"db_path": str(db_path)}
