"""Run a deterministic AyushBot backend showcase.

This script is meant for college/demo use. It exercises the FastAPI triage
route, persistence, referral lookup, and history retrieval without requiring
production JWT keys, model downloads, or private patient data.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import warnings
from pathlib import Path
from typing import Any


def _configure_environment(db_path: Path) -> None:
	os.environ["AYUSHBOT_ENVIRONMENT"] = "development"
	os.environ["AYUSHBOT_DB_PATH"] = str(db_path)
	os.environ["AYUSHBOT_RAG_ENABLED"] = "false"
	os.environ["AYUSHBOT_FL_ENABLED"] = "false"
	os.environ["AYUSHBOT_FL_TRAINING_ENABLED"] = "false"
	os.environ["AYUSHBOT_LANGUAGE_PROVIDER"] = "noop"
	os.environ["AYUSHBOT_DEMO_SHOWCASE"] = "true"


def _seed_reference_data() -> None:
	from sqlalchemy.orm import Session

	from backend.db.seed import seed_reference_data
	from backend.db.session import get_engine

	engine = get_engine(force_reload=True)
	with Session(engine, expire_on_commit=False) as db:
		seed_reference_data(
			db,
			villages="data/reference/villages.json",
			facilities="data/reference/facilities.csv",
		)


def _auth_override():
	from backend.security.auth import AuthUser, Role

	async def _override() -> AuthUser:
		return AuthUser(user_id="asha-demo-001", role=Role.ASHA_WORKER)

	return _override


def _cases() -> list[dict[str, Any]]:
	return [
		{
			"name": "Respiratory referral",
			"expected_risk": "HIGH",
			"body": {
				"patient_id": "patient-demo-respiratory",
				"patient_name": "Demo Child Respiratory",
				"age_months": 24,
				"sex": "female",
				"village_id": "village-demo-001",
				"asha_id": "asha-demo-001",
				"symptom_text": "fever cough fast breathing",
				"input_language": "en",
				"asha_checklist": {"chest_indrawing": True},
				"vitals": {
					"spo2": 94,
					"heart_rate": 132,
					"temperature_celsius": 38.7,
					"respiratory_rate": 48,
				},
			},
		},
		{
			"name": "Critical oxygen danger sign",
			"expected_risk": "CRITICAL",
			"body": {
				"patient_id": "patient-demo-critical",
				"patient_name": "Demo Child Critical",
				"age_months": 18,
				"sex": "male",
				"village_id": "village-demo-001",
				"asha_id": "asha-demo-001",
				"symptom_text": "child has breathing difficulty",
				"input_language": "en",
				"vitals": {
					"spo2": 88,
					"heart_rate": 150,
					"temperature_celsius": 39.1,
					"respiratory_rate": 52,
				},
			},
		},
		{
			"name": "Routine fever review",
			"expected_risk": "MEDIUM",
			"body": {
				"patient_id": "patient-demo-fever",
				"patient_name": "Demo Child Fever",
				"age_months": 36,
				"sex": "female",
				"village_id": "village-demo-001",
				"asha_id": "asha-demo-001",
				"symptom_text": "fever no danger signs",
				"input_language": "en",
				"vitals": {
					"spo2": 98,
					"heart_rate": 108,
					"temperature_celsius": 38.1,
					"respiratory_rate": 28,
				},
			},
		},
	]


def _check_response(case: dict[str, Any], payload: dict[str, Any]) -> None:
	if payload["risk_level"] != case["expected_risk"]:
		raise RuntimeError(
			f"{case['name']} expected {case['expected_risk']} but got {payload['risk_level']}"
		)
	if not payload.get("action_plan"):
		raise RuntimeError(f"{case['name']} did not return an action plan")
	if not payload.get("asha_output_text"):
		raise RuntimeError(f"{case['name']} did not return ASHA output text")
	if payload["risk_level"] != "CRITICAL" and not payload.get("differential_diagnosis"):
		raise RuntimeError(f"{case['name']} did not return differential diagnosis")


def main() -> int:
	warnings.filterwarnings("ignore", message="Using `httpx` with `starlette.testclient`.*")
	warnings.filterwarnings("ignore", category=DeprecationWarning)
	logging.disable(logging.INFO)
	with tempfile.TemporaryDirectory(prefix="ayushbot-showcase-") as tmp:
		db_path = Path(tmp) / "showcase.db"
		_configure_environment(db_path)

		from fastapi.testclient import TestClient

		from backend.config import clear_settings_cache
		from backend.db.migrate import upgrade
		from backend.db.session import reset_engine
		from backend.security import auth

		clear_settings_cache()
		reset_engine()
		upgrade(f"sqlite:///{db_path}")
		_seed_reference_data()

		from backend.api import main as api_main

		api_main.app.dependency_overrides[auth.authenticate] = _auth_override()
		results: list[dict[str, Any]] = []
		try:
			with TestClient(api_main.app) as client:
				for case in _cases():
					response = client.post("/api/v1/triage/assess", json=case["body"])
					if response.status_code != 200:
						raise RuntimeError(
							f"{case['name']} returned HTTP {response.status_code}: {response.text}"
						)
					payload = response.json()
					_check_response(case, payload)

					history = client.get(
						f"/api/v1/triage/history/{case['body']['patient_id']}"
					)
					if history.status_code != 200 or history.json()["total"] < 1:
						raise RuntimeError(f"{case['name']} history retrieval failed")

					encounter = client.get(
						f"/api/v1/triage/encounter/{payload['request_id']}"
					)
					if encounter.status_code != 200:
						raise RuntimeError(f"{case['name']} encounter retrieval failed")
					if encounter.json().get("errors"):
						raise RuntimeError(
							f"{case['name']} produced pipeline errors: "
							f"{encounter.json()['errors']}"
						)

					action_plan = payload["action_plan"]
					referral = action_plan.get("referral") or {}
					diagnosis = payload.get("differential_diagnosis") or {}
					results.append(
						{
							"case": case["name"],
							"risk": payload["risk_level"],
							"primary": action_plan.get("primary_diagnosis"),
							"referral": referral.get("facility_name"),
							"output": payload["asha_output_text"],
							"conditions": diagnosis.get("possible_conditions", []),
						}
					)
		finally:
			api_main.app.dependency_overrides.clear()
			reset_engine()
			clear_settings_cache()

	logging.disable(logging.NOTSET)
	print(json.dumps({"status": "ok", "results": results}, indent=2))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
