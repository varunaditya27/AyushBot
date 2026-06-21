from __future__ import annotations

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.api import main as api_main
from backend.api.routes import auth as auth_routes
from backend.api.routes import health, sync, triage
from backend.config import clear_settings_cache
from backend.db import crud
from backend.db.models import Base, DeviceStatus, DeviceType, UserRole
from backend.db.session import get_db, reset_engine
from backend.security import auth
from backend.security.auth import AuthUser, Role, hash_password

pytest.importorskip("fastapi")


def _write_keypair(tmp_path):
	private = ec.generate_private_key(ec.SECP256R1())
	private_path = tmp_path / "jwt-private.pem"
	public_path = tmp_path / "jwt-public.pem"
	private_path.write_bytes(
		private.private_bytes(
			serialization.Encoding.PEM,
			serialization.PrivateFormat.PKCS8,
			serialization.NoEncryption(),
		)
	)
	public_path.write_bytes(
		private.public_key().public_bytes(
			serialization.Encoding.PEM,
			serialization.PublicFormat.SubjectPublicKeyInfo,
		)
	)
	return private_path, public_path


@pytest.fixture()
def api_context(tmp_path, monkeypatch):
	private_path, public_path = _write_keypair(tmp_path)
	database = tmp_path / "api.db"
	config = tmp_path / "config.yaml"
	config.write_text(
		f"""
environment: development
database:
  path: {database}
redis:
  enabled: false
mqtt:
  enabled: false
auth:
  issuer: api-test-issuer
  audience: api-test-audience
  active_kid: api-test-key
  keys:
    - kid: api-test-key
      public_key_path: {public_path}
      private_key_path: {private_path}
      active: true
""",
		encoding="utf-8",
	)
	monkeypatch.setenv("AYUSHBOT_CONFIG", str(config))
	clear_settings_cache()
	reset_engine()
	engine = create_engine(f"sqlite:///{database}")
	Base.metadata.create_all(engine)
	current_user = {"value": AuthUser("asha-api", Role.ASHA_WORKER)}

	def _db_override():
		with Session(engine, expire_on_commit=False) as db:
			yield db

	async def _auth_override():
		return current_user["value"]

	app = FastAPI()
	app.include_router(health.router, prefix="/api/v1/health")
	app.include_router(auth_routes.router, prefix="/api/v1/auth")
	app.include_router(sync.router, prefix="/api/v1/sync")
	app.include_router(triage.router, prefix="/api/v1/triage")
	app.dependency_overrides[get_db] = _db_override
	app.dependency_overrides[auth.authenticate] = _auth_override
	app.state.redis_client = api_main.RedisClient(settings=api_main.get_settings().redis)
	app.state.mqtt_listener = api_main.MqttListener(
		api_main.get_settings().mqtt,
		app.state.redis_client,
	)

	with TestClient(app) as client:
		yield {"client": client, "engine": engine, "user": current_user}

	clear_settings_cache()
	reset_engine()


def test_health_liveness_and_readiness(api_context):
	client = api_context["client"]

	assert client.get("/api/v1/health/live").json() == {"status": "ok"}
	assert client.get("/api/v1/health/ping").json() == {"status": "ok"}
	ready = client.get("/api/v1/health/ready")

	assert ready.status_code == 200
	body = ready.json()
	assert body["status"] == "ready"
	assert body["checks"]["database"]["status"] == "ready"
	assert body["checks"]["redis"]["status"] == "disabled"
	assert body["checks"]["mqtt"]["status"] == "disabled"


def test_auth_login_route_success_and_bad_password(api_context):
	with Session(api_context["engine"], expire_on_commit=False) as db:
		crud.create_user_account(
			db,
			{
				"id": "asha-api",
				"username": "asha-api",
				"password_hash": hash_password("synthetic-password-123"),
				"role": UserRole.ASHA_WORKER,
				"active": True,
			},
		)
		crud.register_device(
			db,
			{
				"id": "tablet-api",
				"device_type": DeviceType.ANDROID,
				"status": DeviceStatus.ACTIVE,
				"owner_id": "asha-api",
			},
		)
		db.commit()

	ok = api_context["client"].post(
		"/api/v1/auth/login",
		json={
			"username": "asha-api",
			"password": "synthetic-password-123",
			"device_id": "tablet-api",
		},
	)
	assert ok.status_code == 200
	assert ok.json()["token_type"] == "bearer"
	assert ok.json()["access_token"]

	bad = api_context["client"].post(
		"/api/v1/auth/login",
		json={
			"username": "asha-api",
			"password": "wrong-password",
			"device_id": "tablet-api",
		},
	)
	assert bad.status_code == 401
	assert bad.json() == {"detail": "Invalid credentials"}


def test_sync_upload_contract_shape(api_context):
	response = api_context["client"].post(
		"/api/v1/sync/upload",
		headers={"Idempotency-Key": "api-surface-0001"},
		json={
			"records": [
				{
					"client_record_id": "android-record-api",
					"patient": {
						"id": "patient-api",
						"age_months": 24,
						"sex": "female",
						"asha_id": "asha-api",
						"version": 1,
						"updated_at": 1000,
					},
					"case": {
						"id": "case-api",
						"patient_id": "patient-api",
						"timestamp": 1000,
						"symptoms": [{"code": "fever"}],
						"risk_tier": "LOW",
						"risk_explanation": {},
						"errors": [],
						"sync_status": "PENDING",
						"version": 1,
						"updated_at": 1000,
					},
				}
			]
		},
	)

	assert response.status_code == 200
	body = response.json()
	assert body["accepted"] == 1
	assert body["rejected"] == 0
	assert body["results"][0]["status"] == "CREATED"


def test_triage_basic_request_response(api_context, monkeypatch):
	def _stub(state):
		state["risk_level"] = "LOW"
		state["risk_confidence"] = 0.42
		state["action_plan"] = {"urgency": "ROUTINE"}
		state["asha_output_text"] = "Synthetic demo response"
		return state

	monkeypatch.setattr(triage, "run_pipeline", _stub)
	response = api_context["client"].post(
		"/api/v1/triage/assess",
		json={
			"patient_id": "patient-triage-api",
			"age_months": 18,
			"sex": "female",
			"village_id": "synthetic-village",
			"asha_id": "asha-api",
			"symptom_text": "fever",
		},
	)

	assert response.status_code == 200
	body = response.json()
	assert body["request_id"]
	assert body["risk_level"] == "LOW"
	assert body["action_plan"] == {"urgency": "ROUTINE"}
