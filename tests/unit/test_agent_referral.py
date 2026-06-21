from __future__ import annotations

from backend.agents.agent_referral import run_referral
from backend.config import clear_settings_cache
from backend.db import crud
from backend.db.models import Base, FacilityType
from backend.db.session import SessionLocal, get_engine, reset_engine


def _configure_db(tmp_path, monkeypatch, *, radius_km: float = 50.0):
	db_path = tmp_path / "referral.db"
	config = tmp_path / "config.yaml"
	config.write_text(
		f"""
database:
  path: {db_path}
referral:
  max_search_radius_km: {radius_km}
  allow_out_of_radius_for_emergency: true
""",
		encoding="utf-8",
	)
	monkeypatch.setenv("AYUSHBOT_CONFIG", str(config))
	clear_settings_cache()
	reset_engine()
	engine = get_engine(force_reload=True)
	Base.metadata.create_all(engine)
	return engine


def _seed_facility(facility_id: str, facility_type: FacilityType, lat: float, lon: float):
	with SessionLocal() as db:
		crud.upsert_facility(
			db,
			{
				"id": facility_id,
				"name": f"Synthetic {facility_type.value}",
				"type": facility_type,
				"latitude": lat,
				"longitude": lon,
				"address": "Synthetic address",
				"phone": "000",
				"active": True,
				"metadata_json": {},
			},
		)
		db.commit()


def test_critical_case_emergency_referral_uses_project_db(
	sample_patient_state, tmp_path, monkeypatch
):
	_configure_db(tmp_path, monkeypatch)
	_seed_facility("facility-dh", FacilityType.DH, 12.0, 77.0)
	sample_patient_state["risk_level"] = "CRITICAL"
	sample_patient_state["location"] = [12.01, 77.01]

	result = run_referral(sample_patient_state)

	assert result["action_plan"]["urgency"] == "IMMEDIATE"
	assert result["action_plan"]["referral"]["facility_type"] == "DH"
	assert result["routing_result"]["location_available"] is True


def test_no_location_does_not_default_to_zero_zero(
	sample_patient_state, tmp_path, monkeypatch
):
	_configure_db(tmp_path, monkeypatch)
	_seed_facility("facility-phc", FacilityType.PHC, 12.0, 77.0)
	sample_patient_state["risk_level"] = "MEDIUM"
	sample_patient_state.pop("location", None)

	result = run_referral(sample_patient_state)

	assert result["action_plan"]["referral"]["route_description"].startswith(
		"Distance unavailable"
	)
	assert result["routing_result"]["location_available"] is False
	assert result["errors"][-1]["code"] == "LOCATION_UNAVAILABLE"


def test_no_nearby_facility_records_radius_error(
	sample_patient_state, tmp_path, monkeypatch
):
	_configure_db(tmp_path, monkeypatch, radius_km=1.0)
	_seed_facility("facility-phc", FacilityType.PHC, 30.0, 80.0)
	sample_patient_state["risk_level"] = "MEDIUM"
	sample_patient_state["location"] = [12.0, 77.0]

	result = run_referral(sample_patient_state)

	assert "action_plan" not in result
	assert any(error["code"] == "NO_FACILITY_WITHIN_RADIUS" for error in result["errors"])


def test_facility_db_unavailable_is_safe(sample_patient_state, tmp_path, monkeypatch):
	db_path = tmp_path / "missing-parent" / "referral.db"
	config = tmp_path / "config.yaml"
	config.write_text(
		f"""
database:
  path: {db_path}
""",
		encoding="utf-8",
	)
	monkeypatch.setenv("AYUSHBOT_CONFIG", str(config))
	clear_settings_cache()
	reset_engine()
	sample_patient_state["risk_level"] = "HIGH"
	sample_patient_state["location"] = [12.0, 77.0]

	result = run_referral(sample_patient_state)

	assert "action_plan" not in result
	assert result["errors"][0]["code"] in {"OperationalError", "FileNotFoundError"}
	assert result["errors"][-1]["code"] == "NO_FACILITIES_AVAILABLE"
