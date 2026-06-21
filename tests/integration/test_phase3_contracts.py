from __future__ import annotations

import base64
import json

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.api.routes import sync, telemetry, triage
from backend.config import clear_settings_cache
from backend.db import crud
from backend.db.models import (
	Base,
	DeviceStatus,
	DeviceType,
	FeedbackDisposition,
)
from backend.db.session import get_db
from backend.security import auth
from backend.security.auth import AuthUser, Role


@pytest.fixture()
def phase3_context(tmp_path, monkeypatch):
	private_key = ec.generate_private_key(ec.SECP256R1())
	private_path = tmp_path / "manifest-private.pem"
	public_path = tmp_path / "manifest-public.pem"
	private_path.write_bytes(
		private_key.private_bytes(
			serialization.Encoding.PEM,
			serialization.PrivateFormat.PKCS8,
			serialization.NoEncryption(),
		)
	)
	public_path.write_bytes(
		private_key.public_key().public_bytes(
			serialization.Encoding.PEM,
			serialization.PublicFormat.SubjectPublicKeyInfo,
		)
	)
	resource_dir = tmp_path / "resources"
	resource_dir.mkdir()
	config = tmp_path / "config.yaml"
	config.write_text(
		f"""
environment: development
database:
  path: {tmp_path / "phase3.db"}
sync:
  resource_dir: {resource_dir}
auth:
  active_kid: phase3-key
  keys:
    - kid: phase3-key
      public_key_path: {public_path}
      private_key_path: {private_path}
      active: true
""",
		encoding="utf-8",
	)
	monkeypatch.setenv("AYUSHBOT_CONFIG", str(config))
	clear_settings_cache()

	engine = create_engine(f"sqlite:///{tmp_path / 'phase3.db'}")
	Base.metadata.create_all(engine)
	current_user = {"value": AuthUser("asha-phase3", Role.ASHA_WORKER)}

	def _db_override():
		with Session(engine, expire_on_commit=False) as db:
			yield db

	async def _auth_override():
		return current_user["value"]

	app = FastAPI()
	app.include_router(sync.router, prefix="/api/v1/sync")
	app.include_router(telemetry.router, prefix="/api/v1/telemetry")
	app.include_router(triage.router, prefix="/api/v1/triage")
	app.dependency_overrides[get_db] = _db_override
	app.dependency_overrides[auth.authenticate] = _auth_override

	with TestClient(app) as client:
		yield {
			"client": client,
			"engine": engine,
			"user": current_user,
			"private_key": private_key,
			"resource_dir": resource_dir,
		}
	clear_settings_cache()


def _sync_payload(*, version: int = 1, updated_at: int = 1000) -> dict:
	return {
		"records": [
			{
				"client_record_id": "android-record-1",
				"patient": {
					"id": "patient-phase3",
					"age_months": 24,
					"sex": "female",
					"village": "synthetic-village",
					"asha_id": "asha-phase3",
					"version": version,
					"updated_at": updated_at,
				},
				"case": {
					"id": "case-phase3",
					"patient_id": "patient-phase3",
					"timestamp": 900,
					"symptoms": [{"code": "fever", "present": True}],
					"risk_tier": "LOW",
					"risk_explanation": {"rule": "deterministic-test"},
					"errors": [],
					"sync_status": "PENDING",
					"version": version,
					"updated_at": updated_at,
				},
				"recommendation": {
					"id": "recommendation-phase3",
					"case_id": "case-phase3",
					"primary_diagnosis": "Synthetic diagnosis",
					"differential_diagnosis": [{"condition": "Synthetic"}],
					"action_plan": {"urgency": "ROUTINE"},
					"citations": [{"source": "test-fixture", "section": "1"}],
					"version": version,
					"updated_at": updated_at,
				},
			}
		]
	}


def test_upload_idempotency_and_version_conflict(phase3_context):
	client = phase3_context["client"]
	payload = _sync_payload(version=2, updated_at=2000)
	response = client.post(
		"/api/v1/sync/upload",
		headers={"Idempotency-Key": "phase3-upload-0001"},
		json=payload,
	)
	assert response.status_code == 200
	assert response.json()["results"][0]["status"] == "CREATED"

	replay = client.post(
		"/api/v1/sync/upload",
		headers={"Idempotency-Key": "phase3-upload-0001"},
		json=payload,
	)
	assert replay.status_code == 200
	assert replay.json()["replayed"] is True

	changed = _sync_payload(version=3, updated_at=3000)
	assert (
		client.post(
			"/api/v1/sync/upload",
			headers={"Idempotency-Key": "phase3-upload-0001"},
			json=changed,
		).status_code
		== 409
	)

	conflict = client.post(
		"/api/v1/sync/upload",
		headers={"Idempotency-Key": "phase3-upload-0002"},
		json=_sync_payload(version=1, updated_at=1000),
	)
	assert conflict.status_code == 200
	assert conflict.json()["results"][0]["status"] == "CONFLICT"
	with Session(phase3_context["engine"]) as db:
		assert crud.get_case(db, "case-phase3").version == 2
		assert crud.get_recommendation_by_case(db, "case-phase3").citations == [
			{"source": "test-fixture", "section": "1"}
		]


def test_signed_manifest_etag_and_resumable_download(phase3_context):
	content = b"deterministic-reference-payload"
	path = phase3_context["resource_dir"] / "facilities-v2.json"
	path.write_bytes(content)
	phase3_context["user"]["value"] = AuthUser("officer-phase3", Role.MEDICAL_OFFICER)
	published = phase3_context["client"].post(
		"/api/v1/sync/resources",
		json={
			"resource_type": "reference_data",
			"resource_id": "facilities",
			"version": 2,
			"artifact_path": path.name,
			"media_type": "application/json",
			"metadata": {"schema": "facilities-v1"},
		},
	)
	assert published.status_code == 201
	phase3_context["user"]["value"] = AuthUser("asha-phase3", Role.ASHA_WORKER)

	manifest_response = phase3_context["client"].get("/api/v1/sync/manifest")
	assert manifest_response.status_code == 200
	manifest = manifest_response.json()
	assert manifest["resources"][0]["sha256"]
	signature = manifest.pop("signature")
	canonical = json.dumps(
		manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True
	).encode()
	padding = "=" * (-len(signature["value"]) % 4)
	der_signature = base64.urlsafe_b64decode(signature["value"] + padding)
	r, s = decode_dss_signature(der_signature)
	assert r > 0 and s > 0
	phase3_context["private_key"].public_key().verify(
		der_signature, canonical, ec.ECDSA(hashes.SHA256())
	)

	url = manifest["resources"][0]["download_url"]
	full = phase3_context["client"].get(url)
	assert full.status_code == 200
	assert full.content == content
	assert full.headers["x-checksum-sha256"] == manifest["resources"][0]["sha256"]
	assert phase3_context["client"].get(
		url, headers={"If-None-Match": full.headers["etag"]}
	).status_code == 304
	partial = phase3_context["client"].get(url, headers={"Range": "bytes=0-4"})
	assert partial.status_code == 206
	assert partial.content == content[:5]
	assert partial.headers["content-range"] == f"bytes 0-4/{len(content)}"


def test_feedback_history_and_durable_telemetry(phase3_context):
	with Session(phase3_context["engine"]) as db:
		crud.create_patient(
			db,
			{
				"id": "patient-feedback",
				"age_months": 36,
				"sex": "male",
				"asha_id": "asha-phase3",
			},
		)
		for index in range(3):
			crud.create_case(
				db,
				{
					"id": f"case-feedback-{index}",
					"patient_id": "patient-feedback",
					"timestamp": 1000 + index,
					"symptoms": [{"code": "synthetic"}],
					"risk_explanation": {"score": index},
					"errors": [],
				},
			)
		crud.register_device(
			db,
			{
				"id": "tablet-phase3",
				"device_type": DeviceType.ANDROID,
				"status": DeviceStatus.ACTIVE,
				"owner_id": "asha-phase3",
			},
		)
		db.commit()

	history = phase3_context["client"].get(
		"/api/v1/triage/history/patient-feedback?page=2&page_size=2"
	)
	assert history.status_code == 200
	assert history.json()["total"] == 3
	assert history.json()["total_pages"] == 2
	assert len(history.json()["items"]) == 1

	telemetry_response = phase3_context["client"].post(
		"/api/v1/telemetry",
		json={
			"event_id": "telemetry-phase3-1",
			"device_id": "tablet-phase3",
			"case_id": "case-feedback-0",
			"readings": {"spo2": 97},
		},
	)
	assert telemetry_response.status_code == 202
	assert telemetry_response.json()["persisted"] is True
	assert phase3_context["client"].post(
		"/api/v1/telemetry",
		json={
			"event_id": "telemetry-phase3-1",
			"device_id": "tablet-phase3",
			"case_id": "case-feedback-0",
			"readings": {"spo2": 97},
		},
	).json()["status"] == "duplicate"

	phase3_context["user"]["value"] = AuthUser("officer-phase3", Role.MEDICAL_OFFICER)
	feedback = phase3_context["client"].put(
		"/api/v1/sync/feedback/case-feedback-0",
		json={
			"disposition": FeedbackDisposition.CONFIRMED.value,
			"confirmed_diagnosis": "Synthetic diagnosis",
			"notes": "No real patient data.",
			"structured_feedback": {"follow_up_days": 2},
		},
	)
	assert feedback.status_code == 200
	assert feedback.json()["reviewer_id"] == "officer-phase3"
	assert (
		phase3_context["client"]
		.get("/api/v1/sync/feedback/case-feedback-0")
		.json()["structured_feedback"]["follow_up_days"]
		== 2
	)

	with Session(phase3_context["engine"]) as db:
		assert crud.get_telemetry_event(db, "telemetry-phase3-1").readings == {
			"spo2": 97
		}


def test_stub_pipeline_persists_structured_clinical_output(
	phase3_context, monkeypatch
):
	def _stub(state):
		state["risk_level"] = "HIGH"
		state["risk_confidence"] = 0.8
		state["translated_symptoms"] = [{"code": "fever"}]
		state["risk_explanation"] = {"reason": "deterministic fixture"}
		state["differential_diagnosis"] = {
			"diagnoses": [{"condition_name": "Synthetic condition"}]
		}
		state["action_plan"] = {"urgency": "URGENT"}
		state["citations"] = [{"source": "fixture", "section": "A"}]
		state["errors"] = [{"stage": "stub", "code": "EXPECTED_TEST_ERROR"}]
		state["asha_output_text"] = "Deterministic test output"
		return state

	monkeypatch.setattr(triage, "run_pipeline", _stub)
	response = phase3_context["client"].post(
		"/api/v1/triage/assess",
		json={
			"patient_id": "patient-triage-phase3",
			"age_months": 18,
			"sex": "female",
			"village_id": "synthetic-village",
			"asha_id": "asha-phase3",
			"symptom_text": "synthetic fever",
		},
	)
	assert response.status_code == 200
	encounter = phase3_context["client"].get(
		f"/api/v1/triage/encounter/{response.json()['request_id']}"
	)
	assert encounter.status_code == 200
	body = encounter.json()
	assert body["case"]["symptoms"] == [{"code": "fever"}]
	assert body["case"]["risk_explanation"]["reason"] == "deterministic fixture"
	assert body["recommendation"]["citations"][0]["source"] == "fixture"
	assert body["recommendation"]["action_plan"]["urgency"] == "URGENT"
	assert body["errors"][0]["code"] == "EXPECTED_TEST_ERROR"
