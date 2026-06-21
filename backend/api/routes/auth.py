"""Offline gateway authentication and tablet provisioning endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.db import crud
from backend.db.models import AuditOutcome, DeviceStatus, DeviceType, UserRole, now_ms
from backend.db.session import get_db
from backend.security.auth import (
	AuthUser,
	Role,
	TokenPair,
	_audit,
	authenticate,
	decode_token,
	hash_password,
	issue_token_pair,
	require_roles,
	revoke_token,
	rotate_refresh_token,
	verify_password,
)

router = APIRouter()


class LoginRequest(BaseModel):
	username: str = Field(min_length=1, max_length=128)
	password: str = Field(min_length=1, max_length=1024)
	device_id: str | None = Field(default=None, max_length=64)


class RefreshRequest(BaseModel):
	refresh_token: str = Field(min_length=1)


class TokenResponse(BaseModel):
	access_token: str
	refresh_token: str
	token_type: str


class CurrentUserResponse(BaseModel):
	user_id: str
	role: Role
	device_id: str | None


class TabletProvisionResponse(BaseModel):
	user_id: str
	username: str
	device_id: str
	role: Role


class TabletProvisionRequest(BaseModel):
	user_id: str = Field(min_length=1, max_length=64)
	username: str = Field(min_length=1, max_length=128)
	temporary_password: str = Field(min_length=12, max_length=1024)
	display_name: str | None = Field(default=None, max_length=256)
	device_id: str = Field(min_length=1, max_length=64)
	device_name: str | None = Field(default=None, max_length=128)
	public_key_fingerprint: str | None = Field(default=None, max_length=128)


def _response(pair: TokenPair) -> TokenResponse:
	return TokenResponse(
		access_token=pair.access_token,
		refresh_token=pair.refresh_token,
		token_type=pair.token_type,
	)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
	user = crud.get_user_by_username(db, payload.username)
	if user is None or not user.active or not verify_password(payload.password, user.password_hash):
		_audit(
			db,
			action="auth.login.denied",
			outcome=AuditOutcome.DENIED,
			actor_id=user.id if user else None,
			details={"reason": "invalid_credentials", "claimed_device_id": payload.device_id},
		)
		raise HTTPException(status_code=401, detail="Invalid credentials")

	role = Role(user.role.value)
	device = None
	if payload.device_id:
		device = crud.get_device(db, payload.device_id)
	if role == Role.ASHA_WORKER:
		if (
			device is None
			or device.owner_id != user.id
			or device.device_type != DeviceType.ANDROID
			or device.status != DeviceStatus.ACTIVE
		):
			_audit(
				db,
				action="auth.login.denied",
				outcome=AuditOutcome.DENIED,
				actor_id=user.id,
				details={
					"reason": "unprovisioned_device",
					"claimed_device_id": payload.device_id,
				},
			)
			raise HTTPException(status_code=401, detail="Device is not provisioned")
	elif device and device.status != DeviceStatus.ACTIVE:
		raise HTTPException(status_code=401, detail="Device unavailable")

	user.last_login_at = now_ms()
	if device:
		device.last_seen_at = now_ms()
	pair = issue_token_pair(
		db, user_id=user.id, role=role, device_id=device.id if device else None
	)
	db.commit()
	_audit(
		db,
		action="auth.login.success",
		outcome=AuditOutcome.SUCCESS,
		actor_id=user.id,
		device_id=device.id if device else None,
	)
	return _response(pair)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
	pair = rotate_refresh_token(db, payload.refresh_token)
	refresh_payload = decode_token(payload.refresh_token)
	db.commit()
	_audit(
		db,
		action="auth.refresh.success",
		outcome=AuditOutcome.SUCCESS,
		actor_id=str(refresh_payload["sub"]),
		device_id=refresh_payload.get("device_id"),
	)
	return _response(pair)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
	authorization: str | None = Header(default=None),
	_user: AuthUser = Depends(authenticate),
	db: Session = Depends(get_db),
):
	if not authorization:
		raise HTTPException(status_code=401, detail="Missing Authorization header")
	_, _, token = authorization.partition(" ")
	user_id = _user.user_id
	device_id = _user.device_id
	revoke_token(db, token)
	db.commit()
	_audit(
		db,
		action="auth.logout",
		outcome=AuditOutcome.SUCCESS,
		actor_id=user_id,
		device_id=device_id,
	)


@router.get("/me", response_model=CurrentUserResponse)
async def current_user(user: AuthUser = Depends(authenticate)):
	return CurrentUserResponse(
		user_id=user.user_id, role=user.role, device_id=user.device_id
	)


@router.post(
	"/provision/tablet",
	status_code=status.HTTP_201_CREATED,
	response_model=TabletProvisionResponse,
)
async def provision_tablet(
	payload: TabletProvisionRequest,
	db: Session = Depends(get_db),
	officer: AuthUser = Depends(require_roles([Role.MEDICAL_OFFICER])),
):
	if crud.get_user_account(db, payload.user_id) or crud.get_user_by_username(
		db, payload.username
	):
		raise HTTPException(status_code=409, detail="User already exists")
	if crud.get_device(db, payload.device_id):
		raise HTTPException(status_code=409, detail="Device already exists")

	crud.create_user_account(
		db,
		{
			"id": payload.user_id,
			"username": payload.username,
			"password_hash": hash_password(payload.temporary_password),
			"role": UserRole.ASHA_WORKER,
			"display_name": payload.display_name,
			"active": True,
		},
	)
	crud.register_device(
		db,
		{
			"id": payload.device_id,
			"device_type": DeviceType.ANDROID,
			"status": DeviceStatus.ACTIVE,
			"owner_id": payload.user_id,
			"display_name": payload.device_name,
			"public_key_fingerprint": payload.public_key_fingerprint,
		},
	)
	crud.create_audit_event(
		db,
		{
			"id": str(uuid.uuid4()),
			"actor_id": officer.user_id,
			"device_id": officer.device_id,
			"action": "device.provision",
			"resource_type": "device",
			"resource_id": payload.device_id,
			"outcome": AuditOutcome.SUCCESS,
			"details": {"assigned_user_id": payload.user_id},
		},
	)
	db.commit()
	return {
		"user_id": payload.user_id,
		"username": payload.username,
		"device_id": payload.device_id,
		"role": Role.ASHA_WORKER,
	}
