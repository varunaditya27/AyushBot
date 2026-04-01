# =============================================================================
# AyushBot Tests — Shared Fixtures (conftest.py)
# =============================================================================
#
# PURPOSE:
#   Pytest shared fixtures used across all unit and integration tests.
#   This file is automatically discovered by pytest and its fixtures are
#   available to all test files in the tests/ directory and subdirectories.
#
# FIXTURES TO DEFINE:
#
#   1. sample_patient_state
#      Returns a populated PatientState object (backend/agents/state.py)
#      with realistic sample data for a pediatric patient:
#        - SpO2: 92%, HR: 140 bpm, Temp: 38.5°C, RR: 35
#        - Age: 18 months, Weight: 8.2 kg, Sex: Female
#        - Symptoms: ["fever", "cough", "fast_breathing"]
#        - IMCI danger signs: ["chest_indrawing"]
#
#   2. mock_llm_client
#      Returns a mock LLM inference client that returns deterministic
#      responses without loading the actual Phi-3 model (which is 2+ GB
#      and too slow for unit tests). Configurable response text.
#
#   3. mock_faiss_index
#      Returns a mock FAISS index with a small set of pre-embedded test
#      chunks. Allows testing RAG retrieval logic without building the
#      full index from PDF corpus.
#
#   4. mock_xgboost_model
#      Returns a mock XGBoost model that returns deterministic risk
#      predictions. Used for testing the Intake Agent without loading
#      the trained model file.
#
#   5. sample_sensor_payload
#      Returns a sample MQTT sensor data payload as received from the
#      Arduino sensor pack via the Android bridge:
#        {"device_id": "sensor_001", "timestamp": "...",
#         "spo2": 92, "hr": 140, "temp": 38.5, "status": "ok"}
#
#   6. db_session (integration)
#      Creates a temporary in-memory SQLite database with all tables
#      from backend/db/models.py. Yielded and automatically cleaned up
#      after each test (transaction rollback).
#
#   7. test_config
#      Returns a test-specific configuration dict that overrides
#      backend/config.yaml with test-appropriate values (e.g., reduced
#      DP noise, disabled TLS, mock model paths).
#
# MARKERS:
#   Register custom pytest markers for test categorization:
#     @pytest.mark.slow — Tests taking > 5 seconds (LLM, FL rounds)
#     @pytest.mark.integration — Tests requiring multiple components
#     @pytest.mark.hardware — Tests requiring physical hardware (skip in CI)
# =============================================================================

from __future__ import annotations

import sqlite3
from typing import Dict

import pytest

from backend.agents.schemas.patient_assessment import PatientAssessment
from backend.agents.state import PatientState, state_from_assessment


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
			"CREATE TABLE facilities (id TEXT, name TEXT, type TEXT, latitude REAL, longitude REAL, address TEXT, phone TEXT)"
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

from __future__ import annotations

import sqlite3
from typing import Dict

import pytest

from backend.agents.schemas.patient_assessment import PatientAssessment
from backend.agents.state import PatientState, state_from_assessment


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
			"CREATE TABLE facilities (id TEXT, name TEXT, type TEXT, latitude REAL, longitude REAL, address TEXT, phone TEXT)"
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

from __future__ import annotations

import sqlite3
from typing import Dict

import pytest

from backend.agents.schemas.patient_assessment import PatientAssessment
from backend.agents.state import PatientState, state_from_assessment


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
			"CREATE TABLE facilities (id TEXT, name TEXT, type TEXT, latitude REAL, longitude REAL, address TEXT, phone TEXT)"
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
