"""Database-backed ES256 authentication and authorization."""

from __future__ import annotations

import hashlib
import logging
import secrets
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from backend.config import AuthSettings, get_settings
from backend.db import crud
from backend.db.models import AuditEvent, AuditOutcome, DeviceStatus, TokenType, now_ms
from backend.db.session import get_db

logger = logging.getLogger(__name__)


class Role(str, Enum):
	ASHA_WORKER = "AshaWorker"
	MEDICAL_OFFICER = "MedicalOfficer"


@dataclass(frozen=True)
class AuthUser:
	user_id: str
	role: Role
	device_id: str | None = None
	token_jti_hash: str | None = None


@dataclass(frozen=True)
class TokenPair:
	access_token: str
	refresh_token: str
	token_type: str = "bearer"


@dataclass(frozen=True)
class KeyMaterial:
	kid: str
	public_key: str
	private_key: str | None


_hasher = PasswordHasher()


def hash_password(password: str) -> str:
	if len(password) < 12:
		raise ValueError("Password must contain at least 12 characters")
	return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
	try:
		return _hasher.verify(password_hash, password)
	except (VerifyMismatchError, InvalidHashError):
		return False


def _read_key(path: Path) -> str:
	return path.read_text(encoding="utf-8")


def _key_ring(settings: AuthSettings | None = None) -> dict[str, KeyMaterial]:
	config = settings or get_settings().auth
	keys: dict[str, KeyMaterial] = {}
	for item in config.keys:
		if not item.active:
			continue
		keys[item.kid] = KeyMaterial(
			kid=item.kid,
			public_key=_read_key(item.public_key_path),
			private_key=_read_key(item.private_key_path) if item.private_key_path else None,
		)
	if not keys and config.jwt_public_key_path:
		keys[config.active_kid] = KeyMaterial(
			kid=config.active_kid,
			public_key=_read_key(config.jwt_public_key_path),
			private_key=(
				_read_key(config.jwt_private_key_path)
				if config.jwt_private_key_path
				else None
			),
		)
	return keys


def validate_auth_key_configuration(settings: AuthSettings | None = None) -> None:
	config = settings or get_settings().auth
	keys = _key_ring(config)
	active = keys.get(config.active_kid)
	if not keys:
		raise RuntimeError("No JWT verification keys are configured")
	if active is None or active.private_key is None:
		raise RuntimeError("The active JWT key must include a readable private key")
	for key in keys.values():
		_validate_es256_public_key(key.public_key, key.kid)
		if key.private_key is not None:
			_validate_es256_private_key(key.private_key, key.public_key, key.kid)


def _validate_es256_public_key(raw_key: str, kid: str) -> ec.EllipticCurvePublicKey:
	try:
		key = serialization.load_pem_public_key(raw_key.encode("utf-8"))
	except ValueError as exc:
		raise RuntimeError(f"JWT key {kid!r} is not a readable PEM public key") from exc
	if not isinstance(key, ec.EllipticCurvePublicKey) or not isinstance(
		key.curve, ec.SECP256R1
	):
		raise RuntimeError(f"JWT key {kid!r} must be an ES256 P-256 public key")
	return key


def _validate_es256_private_key(
	raw_private_key: str, raw_public_key: str, kid: str
) -> None:
	try:
		private_key = serialization.load_pem_private_key(
			raw_private_key.encode("utf-8"),
			password=None,
		)
	except (TypeError, ValueError) as exc:
		raise RuntimeError(f"JWT key {kid!r} is not a readable PEM private key") from exc
	if not isinstance(private_key, ec.EllipticCurvePrivateKey) or not isinstance(
		private_key.curve, ec.SECP256R1
	):
		raise RuntimeError(f"JWT key {kid!r} must be an ES256 P-256 private key")
	public_key = _validate_es256_public_key(raw_public_key, kid)
	if private_key.public_key().public_numbers() != public_key.public_numbers():
		raise RuntimeError(
			f"JWT key {kid!r} private_key_path does not match public_key_path"
		)


def _jti_hash(jti: str) -> str:
	return hashlib.sha256(jti.encode("utf-8")).hexdigest()


def _encode_token(
	*,
	subject: str,
	role: Role,
	device_id: str | None,
	token_type: TokenType,
	expires_delta: timedelta,
	jti: str,
) -> tuple[str, dict[str, Any]]:
	settings = get_settings().auth
	keys = _key_ring(settings)
	active = keys.get(settings.active_kid)
	if active is None or active.private_key is None:
		raise RuntimeError("Active JWT signing key is unavailable")
	now = datetime.now(timezone.utc)
	payload = {
		"sub": subject,
		"role": role.value,
		"device_id": device_id,
		"type": token_type.value,
		"jti": jti,
		"iss": settings.issuer,
		"aud": settings.audience,
		"iat": int(now.timestamp()),
		"nbf": int(now.timestamp()),
		"exp": int((now + expires_delta).timestamp()),
	}
	token = jwt.encode(
		payload,
		active.private_key,
		algorithm="ES256",
		headers={"kid": active.kid, "typ": "JWT"},
	)
	return token, payload


def decode_token(token: str, expected_type: TokenType | None = None) -> dict[str, Any]:
	settings = get_settings().auth
	try:
		header = jwt.get_unverified_header(token)
		kid = header.get("kid")
		key = _key_ring(settings).get(str(kid))
		if key is None:
			raise jwt.InvalidKeyError("Unknown signing key")
		payload = jwt.decode(
			token,
			key.public_key,
			algorithms=["ES256"],
			issuer=settings.issuer,
			audience=settings.audience,
			options={"require": ["sub", "jti", "iss", "aud", "iat", "nbf", "exp", "type"]},
		)
		if expected_type and payload.get("type") != expected_type.value:
			raise jwt.InvalidTokenError("Unexpected token type")
		return payload
	except jwt.ExpiredSignatureError as exc:
		raise HTTPException(status_code=401, detail="Token expired") from exc
	except jwt.InvalidTokenError as exc:
		raise HTTPException(status_code=401, detail="Invalid token") from exc


def _record_token(
	db: Session,
	*,
	payload: dict[str, Any],
	family_id: str,
) -> None:
	crud.create_token_record(
		db,
		{
			"id": str(uuid.uuid4()),
			"jti_hash": _jti_hash(str(payload["jti"])),
			"family_id": family_id,
			"user_id": str(payload["sub"]),
			"device_id": payload.get("device_id"),
			"token_type": payload["type"],
			"issued_at": int(payload["iat"]),
			"expires_at": int(payload["exp"]),
		},
	)


def issue_token_pair(
	db: Session,
	*,
	user_id: str,
	role: Role,
	device_id: str | None,
	family_id: str | None = None,
) -> TokenPair:
	settings = get_settings().auth
	family = family_id or secrets.token_urlsafe(24)
	access, access_payload = _encode_token(
		subject=user_id,
		role=role,
		device_id=device_id,
		token_type=TokenType.ACCESS,
		expires_delta=timedelta(minutes=settings.access_token_minutes),
		jti=secrets.token_urlsafe(32),
	)
	refresh, refresh_payload = _encode_token(
		subject=user_id,
		role=role,
		device_id=device_id,
		token_type=TokenType.REFRESH,
		expires_delta=timedelta(days=settings.refresh_token_days),
		jti=secrets.token_urlsafe(32),
	)
	_record_token(db, payload=access_payload, family_id=family)
	_record_token(db, payload=refresh_payload, family_id=family)
	return TokenPair(access_token=access, refresh_token=refresh)


def _audit(
	db: Session,
	*,
	action: str,
	outcome: AuditOutcome,
	actor_id: str | None = None,
	device_id: str | None = None,
	resource_type: str | None = None,
	resource_id: str | None = None,
	details: dict[str, Any] | None = None,
) -> None:
	separate = Session(bind=db.get_bind())
	try:
		separate.add(
			AuditEvent(
				id=str(uuid.uuid4()),
				actor_id=actor_id,
				device_id=device_id,
				action=action,
				outcome=outcome,
				resource_type=resource_type,
				resource_id=resource_id,
				details=details or {},
			)
		)
		separate.commit()
	except Exception:
		separate.rollback()
		logger.exception("Failed to persist security audit event")
	finally:
		separate.close()


def revoke_family(db: Session, family_id: str, replaced_by_hash: str | None = None) -> None:
	when = now_ms() // 1000
	for record in crud.list_token_family(db, family_id):
		if record.revoked_at is None:
			record.revoked_at = when
		if replaced_by_hash and record.token_type == TokenType.REFRESH:
			record.replaced_by_hash = replaced_by_hash
	db.flush()


def rotate_refresh_token(db: Session, refresh_token: str) -> TokenPair:
	payload = decode_token(refresh_token, TokenType.REFRESH)
	jti_hash = _jti_hash(str(payload["jti"]))
	record = crud.get_token_record_by_hash(db, jti_hash)
	if record is None or record.revoked_at is not None:
		_audit(
			db,
			action="auth.refresh.denied",
			outcome=AuditOutcome.DENIED,
			actor_id=str(payload["sub"]),
			device_id=payload.get("device_id"),
			details={"reason": "revoked_or_unknown"},
		)
		raise HTTPException(status_code=401, detail="Refresh token revoked")
	if record.used_at is not None:
		revoke_family(db, record.family_id)
		db.commit()
		_audit(
			db,
			action="auth.refresh.replay",
			outcome=AuditOutcome.DENIED,
			actor_id=record.user_id,
			device_id=record.device_id,
			details={"family_revoked": True},
		)
		raise HTTPException(status_code=401, detail="Refresh token replay detected")

	user = crud.get_user_account(db, record.user_id)
	if user is None or not user.active:
		revoke_family(db, record.family_id)
		db.commit()
		raise HTTPException(status_code=401, detail="Account unavailable")
	if record.device_id:
		device = crud.get_device(db, record.device_id)
		if device is None or device.status != DeviceStatus.ACTIVE:
			revoke_family(db, record.family_id)
			db.commit()
			raise HTTPException(status_code=401, detail="Device unavailable")

	record.used_at = now_ms() // 1000
	pair = issue_token_pair(
		db,
		user_id=user.id,
		role=Role(user.role.value),
		device_id=record.device_id,
		family_id=record.family_id,
	)
	new_payload = decode_token(pair.refresh_token, TokenType.REFRESH)
	record.replaced_by_hash = _jti_hash(str(new_payload["jti"]))
	db.flush()
	return pair


def revoke_token(db: Session, token: str) -> None:
	payload = decode_token(token)
	record = crud.get_token_record_by_hash(db, _jti_hash(str(payload["jti"])))
	if record:
		revoke_family(db, record.family_id)


def _extract_bearer_token(authorization: str | None) -> str:
	if not authorization:
		raise HTTPException(status_code=401, detail="Missing Authorization header")
	scheme, _, token = authorization.partition(" ")
	if scheme.lower() != "bearer" or not token:
		raise HTTPException(status_code=401, detail="Invalid Authorization header")
	return token


async def authenticate(
	authorization: str | None = Header(default=None),
	db: Session = Depends(get_db),
) -> AuthUser:
	token = _extract_bearer_token(authorization)
	payload = decode_token(token, TokenType.ACCESS)
	jti_hash = _jti_hash(str(payload["jti"]))
	record = crud.get_token_record_by_hash(db, jti_hash)
	if record is None or record.revoked_at is not None:
		raise HTTPException(status_code=401, detail="Token revoked")
	user = crud.get_user_account(db, str(payload["sub"]))
	if user is None or not user.active:
		raise HTTPException(status_code=401, detail="Account unavailable")
	if record.device_id:
		device = crud.get_device(db, record.device_id)
		if device is None or device.status != DeviceStatus.ACTIVE:
			raise HTTPException(status_code=401, detail="Device unavailable")
	return AuthUser(
		user_id=user.id,
		role=Role(user.role.value),
		device_id=record.device_id,
		token_jti_hash=jti_hash,
	)


def require_roles(allowed: Iterable[Role]):
	allowed_set = set(allowed)

	async def _dependency(user: AuthUser = Depends(authenticate)) -> AuthUser:
		if user.role not in allowed_set:
			raise HTTPException(status_code=403, detail="Insufficient privileges")
		return user

	return _dependency


def require_patient_access(db: Session, user: AuthUser, patient_id: str) -> None:
	if user.role == Role.MEDICAL_OFFICER:
		return
	patient = crud.get_patient(db, patient_id)
	if patient is None:
		raise HTTPException(status_code=404, detail="Not found")
	if patient.asha_id != user.user_id:
		_audit(
			db,
			action="authorization.patient.denied",
			outcome=AuditOutcome.DENIED,
			actor_id=user.user_id,
			device_id=user.device_id,
			resource_type="patient",
			resource_id=patient_id,
		)
		raise HTTPException(status_code=403, detail="Access denied")


def require_case_access(db: Session, user: AuthUser, case_id: str) -> None:
	if user.role == Role.MEDICAL_OFFICER:
		return
	case = crud.get_case(db, case_id)
	if case is None:
		raise HTTPException(status_code=404, detail="Not found")
	require_patient_access(db, user, case.patient_id)
