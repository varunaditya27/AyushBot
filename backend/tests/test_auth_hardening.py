from __future__ import annotations

import asyncio

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.api.routes.auth import LoginRequest, RefreshRequest, login, refresh
from backend.config import clear_settings_cache, load_settings
from backend.db import crud
from backend.db.models import Base, DeviceStatus, DeviceType, UserRole
from backend.security.auth import (
	Role,
	authenticate,
	decode_token,
	hash_password,
	validate_auth_key_configuration,
)


def _write_ec_keypair(tmp_path, name: str):
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
	return private_path, public_path


@pytest.fixture()
def auth_context(tmp_path, monkeypatch):
	private_path, public_path = _write_ec_keypair(tmp_path, "jwt")
	database = tmp_path / "auth.db"
	config = tmp_path / "config.yaml"
	config.write_text(
		f"""
database:
  path: {database}
auth:
  issuer: hardening-test-issuer
  audience: hardening-test-audience
  active_kid: test-key
  keys:
    - kid: test-key
      public_key_path: {public_path}
      private_key_path: {private_path}
      active: true
""",
		encoding="utf-8",
	)
	monkeypatch.setenv("AYUSHBOT_CONFIG", str(config))
	clear_settings_cache()
	engine = create_engine(f"sqlite:///{database}")
	Base.metadata.create_all(engine)
	with Session(engine, expire_on_commit=False) as db:
		yield db
	clear_settings_cache()


def _create_asha(
	db: Session,
	*,
	user_id: str = "asha-hardening-1",
	device_id: str = "tablet-hardening-1",
	device_status: DeviceStatus = DeviceStatus.ACTIVE,
) -> None:
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
			"id": device_id,
			"device_type": DeviceType.ANDROID,
			"status": device_status,
			"owner_id": user_id,
		},
	)
	db.commit()


def test_successful_login_refresh_and_authenticated_request(auth_context):
	db = auth_context
	_create_asha(db)

	pair = asyncio.run(
		login(
			LoginRequest(
				username="asha-hardening-1",
				password="synthetic-password-123",
				device_id="tablet-hardening-1",
			),
			db=db,
		)
	)
	access_payload = decode_token(pair.access_token)
	assert access_payload["sub"] == "asha-hardening-1"
	assert access_payload["role"] == Role.ASHA_WORKER.value

	user = asyncio.run(authenticate(authorization=f"Bearer {pair.access_token}", db=db))
	assert user.user_id == "asha-hardening-1"

	rotated = asyncio.run(refresh(RefreshRequest(refresh_token=pair.refresh_token), db=db))
	assert rotated.access_token != pair.access_token


def test_bad_password_returns_safe_error(auth_context):
	db = auth_context
	_create_asha(db)

	with pytest.raises(HTTPException) as exc:
		asyncio.run(
			login(
				LoginRequest(
					username="asha-hardening-1",
					password="wrong-password",
					device_id="tablet-hardening-1",
				),
				db=db,
			)
		)
	assert exc.value.status_code == 401
	assert exc.value.detail == "Invalid credentials"


def test_bad_access_and_refresh_tokens_return_safe_errors(auth_context):
	db = auth_context

	for call in (
		lambda: authenticate(authorization="Bearer not-a-jwt", db=db),
		lambda: refresh(RefreshRequest(refresh_token="not-a-jwt"), db=db),
	):
		with pytest.raises(HTTPException) as exc:
			asyncio.run(call())
		assert exc.value.status_code == 401
		assert exc.value.detail == "Invalid token"


def test_unknown_and_disabled_devices_are_rejected(auth_context):
	db = auth_context
	_create_asha(db, device_status=DeviceStatus.REVOKED)

	with pytest.raises(HTTPException) as unknown:
		asyncio.run(
			login(
				LoginRequest(
					username="asha-hardening-1",
					password="synthetic-password-123",
					device_id="unknown-tablet",
				),
				db=db,
			)
		)
	assert unknown.value.status_code == 401
	assert unknown.value.detail == "Device is not provisioned"

	with pytest.raises(HTTPException) as disabled:
		asyncio.run(
			login(
				LoginRequest(
					username="asha-hardening-1",
					password="synthetic-password-123",
					device_id="tablet-hardening-1",
				),
				db=db,
			)
		)
	assert disabled.value.status_code == 401
	assert disabled.value.detail == "Device is not provisioned"


def test_production_jwt_key_validation_rejects_non_es256_key(tmp_path):
	private_path, _public_path = _write_ec_keypair(tmp_path, "jwt")
	rsa_public_path = tmp_path / "rsa-public.pem"
	rsa_public_path.write_bytes(
		rsa.generate_private_key(public_exponent=65537, key_size=2048)
		.public_key()
		.public_bytes(
			serialization.Encoding.PEM,
			serialization.PublicFormat.SubjectPublicKeyInfo,
		)
	)
	config = tmp_path / "production.yaml"
	config.write_text(
		f"""
environment: production
auth:
  active_kid: weak-key
  keys:
    - kid: weak-key
      public_key_path: {rsa_public_path}
      private_key_path: {private_path}
      active: true
""",
		encoding="utf-8",
	)
	settings = load_settings(config, create_dirs=False)

	with pytest.raises(RuntimeError, match="ES256 P-256 public key"):
		validate_auth_key_configuration(settings.auth)
