from __future__ import annotations

import asyncio
import time

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.api.routes.auth import (
	LoginRequest,
	TabletProvisionRequest,
	login,
	provision_tablet,
)
from backend.api.routes.sync import (
	CasePayload,
	PatientPayload,
	SyncBatchRequest,
	SyncRecord,
	sync_batch,
)
from backend.config import clear_settings_cache
from backend.db import crud
from backend.db.models import (
	AuditEvent,
	Base,
	DeviceStatus,
	DeviceType,
	TokenRecord,
	UserRole,
)
from backend.security.auth import (
	AuthUser,
	Role,
	TokenType,
	authenticate,
	decode_token,
	hash_password,
	issue_token_pair,
	require_case_access,
	require_patient_access,
	require_roles,
	rotate_refresh_token,
)
from backend.security.transport import validate_production_security


@pytest.fixture()
def security_context(tmp_path, monkeypatch):
	def write_key(name: str):
		private = ec.generate_private_key(ec.SECP256R1())
		private_path = tmp_path / f"{name}-private.pem"
		public_path = tmp_path / f"{name}-public.pem"
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
		return private, private_path, public_path

	old_private, old_private_path, old_public_path = write_key("old")
	active_private, active_private_path, active_public_path = write_key("active")
	database = tmp_path / "security.db"
	config = tmp_path / "config.yaml"
	config.write_text(
		f"""
database:
  path: {database}
auth:
  issuer: test-issuer
  audience: test-audience
  access_token_minutes: 5
  refresh_token_days: 2
  active_kid: active-key
  keys:
    - kid: old-key
      public_key_path: {old_public_path}
      private_key_path: {old_private_path}
      active: true
    - kid: active-key
      public_key_path: {active_public_path}
      private_key_path: {active_private_path}
      active: true
""",
		encoding="utf-8",
	)
	monkeypatch.setenv("AYUSHBOT_CONFIG", str(config))
	clear_settings_cache()

	engine = create_engine(f"sqlite:///{database}")
	Base.metadata.create_all(engine)
	with Session(engine, expire_on_commit=False) as db:
		yield {
			"db": db,
			"old_private": old_private,
			"active_private": active_private,
		}
	clear_settings_cache()


def _create_user_and_device(db: Session, user_id: str = "asha-security-1"):
	crud.create_user_account(
		db,
		{
			"id": user_id,
			"username": user_id,
			"password_hash": hash_password("synthetic-password-123"),
			"role": UserRole.ASHA_WORKER,
			"active": True,
		},
	)
	crud.register_device(
		db,
		{
			"id": f"tablet-{user_id}",
			"device_type": DeviceType.ANDROID,
			"status": DeviceStatus.ACTIVE,
			"owner_id": user_id,
		},
	)
	db.commit()


def test_es256_claims_active_key_and_old_key_validation(security_context):
	db = security_context["db"]
	_create_user_and_device(db)
	pair = issue_token_pair(
		db,
		user_id="asha-security-1",
		role=Role.ASHA_WORKER,
		device_id="tablet-asha-security-1",
	)
	db.commit()
	assert jwt.get_unverified_header(pair.access_token)["kid"] == "active-key"
	payload = decode_token(pair.access_token, TokenType.ACCESS)
	assert payload["iss"] == "test-issuer"
	assert payload["aud"] == "test-audience"

	now = int(time.time())
	old_token = jwt.encode(
		{
			"sub": "asha-security-1",
			"role": Role.ASHA_WORKER.value,
			"device_id": "tablet-asha-security-1",
			"type": "access",
			"jti": "old-jti",
			"iss": "test-issuer",
			"aud": "test-audience",
			"iat": now,
			"nbf": now,
			"exp": now + 60,
		},
		security_context["old_private"],
		algorithm="ES256",
		headers={"kid": "old-key"},
	)
	assert decode_token(old_token)["sub"] == "asha-security-1"


def test_expired_token_rejected(security_context):
	now = int(time.time())
	token = jwt.encode(
		{
			"sub": "user",
			"role": Role.ASHA_WORKER.value,
			"type": "access",
			"jti": "expired",
			"iss": "test-issuer",
			"aud": "test-audience",
			"iat": now - 120,
			"nbf": now - 120,
			"exp": now - 60,
		},
		security_context["active_private"],
		algorithm="ES256",
		headers={"kid": "active-key"},
	)
	with pytest.raises(HTTPException, match="Token expired"):
		decode_token(token)


def test_refresh_replay_revokes_entire_family(security_context):
	db = security_context["db"]
	_create_user_and_device(db)
	original = issue_token_pair(
		db,
		user_id="asha-security-1",
		role=Role.ASHA_WORKER,
		device_id="tablet-asha-security-1",
	)
	db.commit()
	replacement = rotate_refresh_token(db, original.refresh_token)
	db.commit()

	with pytest.raises(HTTPException, match="replay"):
		rotate_refresh_token(db, original.refresh_token)

	with pytest.raises(HTTPException, match="revoked"):
		asyncio.run(
			authenticate(
				authorization=f"Bearer {replacement.access_token}",
				db=db,
			)
		)
	assert db.scalar(select(AuditEvent).where(AuditEvent.action == "auth.refresh.replay"))


def test_revoked_access_token_rejected(security_context):
	db = security_context["db"]
	_create_user_and_device(db)
	pair = issue_token_pair(
		db,
		user_id="asha-security-1",
		role=Role.ASHA_WORKER,
		device_id="tablet-asha-security-1",
	)
	db.commit()
	payload = decode_token(pair.access_token)
	record = crud.get_token_record_by_hash(
		db,
		__import__("hashlib").sha256(payload["jti"].encode()).hexdigest(),
	)
	record.revoked_at = int(time.time())
	db.commit()
	with pytest.raises(HTTPException, match="revoked"):
		asyncio.run(authenticate(authorization=f"Bearer {pair.access_token}", db=db))


def test_medical_officer_provisions_tablet_and_asha_logs_in(security_context):
	db = security_context["db"]
	crud.create_user_account(
		db,
		{
			"id": "officer-security-1",
			"username": "officer",
			"password_hash": hash_password("officer-password-123"),
			"role": UserRole.MEDICAL_OFFICER,
			"active": True,
		},
	)
	db.commit()
	officer = AuthUser("officer-security-1", Role.MEDICAL_OFFICER)
	result = asyncio.run(
		provision_tablet(
			TabletProvisionRequest(
				user_id="asha-security-2",
				username="asha-two",
				temporary_password="temporary-password-123",
				device_id="tablet-security-2",
			),
			db=db,
			officer=officer,
		)
	)
	assert result["device_id"] == "tablet-security-2"
	response = asyncio.run(
		login(
			LoginRequest(
				username="asha-two",
				password="temporary-password-123",
				device_id="tablet-security-2",
			),
			db=db,
		)
	)
	assert decode_token(response.access_token)["sub"] == "asha-security-2"


def test_ownership_enforcement_and_medical_officer_bypass(security_context):
	db = security_context["db"]
	_create_user_and_device(db, "asha-owner")
	_create_user_and_device(db, "asha-other")
	crud.create_patient(
		db,
		{
			"id": "patient-owned",
			"age_months": 12,
			"sex": "female",
			"asha_id": "asha-owner",
		},
	)
	crud.create_case(
		db,
		{
			"id": "case-owned",
			"patient_id": "patient-owned",
			"symptoms": [],
		},
	)
	db.commit()

	require_patient_access(db, AuthUser("asha-owner", Role.ASHA_WORKER), "patient-owned")
	require_case_access(db, AuthUser("asha-owner", Role.ASHA_WORKER), "case-owned")
	with pytest.raises(HTTPException, match="Access denied"):
		require_patient_access(
			db, AuthUser("asha-other", Role.ASHA_WORKER), "patient-owned"
		)
	require_patient_access(
		db, AuthUser("officer", Role.MEDICAL_OFFICER), "patient-owned"
	)

	result = asyncio.run(
		sync_batch(
			SyncBatchRequest(
				records=[
					SyncRecord(
						patient=PatientPayload(
							id="patient-owned",
							age_months=12,
							sex="female",
							asha_id="asha-other",
						),
						case=CasePayload(
							id="case-forged",
							patient_id="patient-owned",
						),
					)
				]
			),
			db=db,
			user=AuthUser("asha-other", Role.ASHA_WORKER),
		)
	)
	assert result.accepted == 0
	assert crud.get_patient(db, "patient-owned").asha_id == "asha-owner"


def test_role_authorization_rejects_asha_for_admin_dependency(security_context):
	dependency = require_roles([Role.MEDICAL_OFFICER])
	with pytest.raises(HTTPException, match="Insufficient privileges"):
		asyncio.run(dependency(user=AuthUser("asha", Role.ASHA_WORKER)))
	assert asyncio.run(
		dependency(user=AuthUser("officer", Role.MEDICAL_OFFICER))
	).role == Role.MEDICAL_OFFICER


def test_production_security_rejects_wildcard_cors(security_context, tmp_path):
	from backend.config import load_settings

	config = tmp_path / "production.yaml"
	config.write_text(
		"""
environment: production
api:
  cors_origins: ["*"]
""",
		encoding="utf-8",
	)
	settings = load_settings(config, create_dirs=False)
	with pytest.raises(RuntimeError, match="CORS"):
		validate_production_security(settings)


def test_production_security_rejects_unreviewed_clinical_rules(
	tmp_path, monkeypatch
):
	from backend.config import load_settings
	from backend.security import transport

	monkeypatch.setattr(
		transport, "validate_auth_key_configuration", lambda _settings: None
	)

	certificate = tmp_path / "certificate.pem"
	certificate.write_text("test", encoding="utf-8")
	rules = tmp_path / "rules.json"
	rules.write_text(
		"""
{
  "schema_version": 1,
  "ruleset_version": "draft",
  "status": "DRAFT",
  "sources": ["test"],
  "signal_quality": {
    "window_readings": 2,
    "window_seconds": 30,
    "spo2_cv_max": 0.03,
    "bounds": {}
  },
  "rules": []
}
""",
		encoding="utf-8",
	)
	growth = tmp_path / "growth.json"
	growth.write_text(
		"""
{
  "schema_version": 1,
  "reference_version": "test",
  "source": "test",
  "status": "TEMPLATE",
  "rows": []
}
""",
		encoding="utf-8",
	)
	config = tmp_path / "production-clinical.yaml"
	config.write_text(
		f"""
environment: production
api:
  cors_origins: ["https://localhost"]
  tls_cert_path: {certificate}
  tls_key_path: {certificate}
mqtt:
  enabled: true
  tls_enabled: true
  port: 8883
  ca_cert_path: {certificate}
  client_cert_path: {certificate}
  client_key_path: {certificate}
triage_model:
  rules_path: {rules}
  growth_reference_path: {growth}
auth:
  active_kid: unused-in-test
  keys: []
""",
		encoding="utf-8",
	)
	settings = load_settings(config, create_dirs=False)
	with pytest.raises(RuntimeError, match="medically reviewed"):
		validate_production_security(settings)


def test_token_records_store_hashes_not_raw_jtis(security_context):
	db = security_context["db"]
	_create_user_and_device(db)
	pair = issue_token_pair(
		db,
		user_id="asha-security-1",
		role=Role.ASHA_WORKER,
		device_id="tablet-asha-security-1",
	)
	db.commit()
	raw_jti = decode_token(pair.access_token)["jti"]
	records = list(db.scalars(select(TokenRecord)))
	assert records
	assert all(record.jti_hash != raw_jti for record in records)
