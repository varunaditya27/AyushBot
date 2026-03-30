"""AyushBot Backend — Authentication & Authorization Module."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Iterable, Optional

import jwt
import yaml
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, Header, HTTPException, status

logger = logging.getLogger(__name__)


class Role(str, Enum):
	ASHA_WORKER = "AshaWorker"
	MEDICAL_OFFICER = "MedicalOfficer"


@dataclass(frozen=True)
class AuthUser:
	user_id: str
	role: Role


_hasher = PasswordHasher()


def _load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
	path = (
		config_path
		or os.getenv("AYUSHBOT_CONFIG")
		or os.path.join(os.path.dirname(__file__), "..", "config.yaml")
	)
	path = os.path.abspath(path)
	if not os.path.exists(path):
		return {}
	try:
		with open(path, "r", encoding="utf-8") as handle:
			return yaml.safe_load(handle) or {}
	except Exception as exc:  # pragma: no cover
		logger.error("Failed to load config from %s: %s", path, exc)
		return {}


def hash_password(password: str) -> str:
	return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
	try:
		return _hasher.verify(password_hash, password)
	except VerifyMismatchError:
		return False


def _get_auth_config() -> Dict[str, Any]:
	config = _load_config()
	return config.get("auth", {}) if isinstance(config, dict) else {}


def _load_key_from_path(path: str) -> str:
	with open(path, "r", encoding="utf-8") as handle:
		return handle.read()


def _load_jwt_keys() -> tuple[str, str]:
	auth_config = _get_auth_config()
	private_key = os.getenv("AYUSHBOT_JWT_PRIVATE_KEY")
	public_key = os.getenv("AYUSHBOT_JWT_PUBLIC_KEY")

	private_path = os.getenv(
		"AYUSHBOT_JWT_PRIVATE_KEY_PATH",
		auth_config.get("jwt_private_key_path"),
	)
	public_path = os.getenv(
		"AYUSHBOT_JWT_PUBLIC_KEY_PATH",
		auth_config.get("jwt_public_key_path"),
	)

	if not private_key and private_path and os.path.exists(private_path):
		private_key = _load_key_from_path(private_path)
	if not public_key and public_path and os.path.exists(public_path):
		public_key = _load_key_from_path(public_path)

	if not private_key or not public_key:
		raise RuntimeError("JWT key material missing; set key paths or env vars")

	return private_key, public_key


def create_access_token(
	subject: str,
	role: Role,
	expires_in_minutes: int = 60 * 24,
) -> str:
	private_key, _ = _load_jwt_keys()
	now = datetime.now(timezone.utc)
	payload = {
		"sub": subject,
		"role": role.value,
		"iat": int(now.timestamp()),
		"exp": int((now + timedelta(minutes=expires_in_minutes)).timestamp()),
	}
	return jwt.encode(payload, private_key, algorithm="ES256")


def decode_token(token: str) -> Dict[str, Any]:
	_, public_key = _load_jwt_keys()
	try:
		return jwt.decode(token, public_key, algorithms=["ES256"])
	except jwt.ExpiredSignatureError as exc:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
		) from exc
	except jwt.InvalidTokenError as exc:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
		) from exc


def _extract_bearer_token(authorization: Optional[str]) -> str:
	if not authorization:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Missing Authorization header",
		)
	scheme, _, token = authorization.partition(" ")
	if scheme.lower() != "bearer" or not token:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid Authorization header",
		)
	return token


def _parse_role(role_value: str) -> Role:
	try:
		return Role(role_value)
	except ValueError as exc:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN, detail="Invalid role"
		) from exc


async def authenticate(authorization: Optional[str] = Header(default=None)) -> AuthUser:
	token = _extract_bearer_token(authorization)
	payload = decode_token(token)
	subject = payload.get("sub")
	role_value = payload.get("role")
	if not subject or not role_value:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Token missing claims",
		)
	return AuthUser(user_id=str(subject), role=_parse_role(str(role_value)))


def require_roles(allowed: Iterable[Role]):
	allowed_set = set(allowed)

	async def _dependency(user: AuthUser = Depends(authenticate)) -> AuthUser:
		if user.role not in allowed_set:
			raise HTTPException(
				status_code=status.HTTP_403_FORBIDDEN,
				detail="Insufficient privileges",
			)
		return user

	return _dependency


def list_provisioned_users() -> Dict[str, Dict[str, Any]]:
	auth_config = _get_auth_config()
	users = auth_config.get("users", []) if isinstance(auth_config, dict) else []
	result: Dict[str, Dict[str, Any]] = {}
	for user in users:
		if not isinstance(user, dict):
			continue
		user_id = str(user.get("user_id") or user.get("username") or "")
		role = user.get("role")
		if user_id and role:
			result[user_id] = user
	return result


def verify_user_password(user_id: str, password: str) -> bool:
	users = list_provisioned_users()
	record = users.get(user_id)
	if not record:
		return False
	password_hash = record.get("password_hash")
	if not password_hash:
		return False
	return verify_password(password, password_hash)
