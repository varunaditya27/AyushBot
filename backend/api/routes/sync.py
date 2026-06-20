"""Offline synchronization, resource manifests, and clinical feedback."""

from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import re
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import (
	APIRouter,
	Depends,
	Header,
	HTTPException,
	Query,
	Request,
	Response,
	status,
)
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from backend.config import get_settings
from backend.db import crud
from backend.db.models import (
	FeedbackDisposition,
	RiskTier,
	SyncOperation,
	SyncStatus,
	now_ms,
)
from backend.db.session import get_db
from backend.security.auth import AuthUser, Role, require_case_access, require_roles

router = APIRouter()
RANGE_PATTERN = re.compile(r"bytes=(\d*)-(\d*)$")


class ContractModel(BaseModel):
	model_config = ConfigDict(extra="forbid")


class PatientPayload(ContractModel):
	id: str = Field(min_length=1, max_length=64)
	abha_id: str | None = Field(default=None, max_length=64)
	name: str | None = Field(default=None, max_length=256)
	age_months: int = Field(ge=0)
	sex: str = Field(min_length=1, max_length=16)
	village: str | None = Field(default=None, max_length=128)
	asha_id: str = Field(min_length=1, max_length=64)
	version: int = Field(default=1, ge=1)
	updated_at: int = Field(default_factory=now_ms, ge=0)


class CasePayload(ContractModel):
	id: str = Field(min_length=1, max_length=64)
	patient_id: str = Field(min_length=1, max_length=64)
	timestamp: int = Field(default_factory=now_ms, ge=0)
	spo2: float | None = None
	heart_rate: float | None = None
	temperature: float | None = None
	weight: float | None = None
	symptoms: list[Any] | dict[str, Any] = Field(default_factory=list)
	risk_tier: RiskTier = RiskTier.LOW
	risk_explanation: dict[str, Any] | list[Any] = Field(default_factory=dict)
	errors: list[Any] | dict[str, Any] = Field(default_factory=list)
	sync_status: SyncStatus = SyncStatus.PENDING
	version: int = Field(default=1, ge=1)
	updated_at: int = Field(default_factory=now_ms, ge=0)
	ruleset_version: str | None = Field(default=None, max_length=128)
	growth_reference_version: str | None = Field(default=None, max_length=128)
	triage_model_version: str | None = Field(default=None, max_length=128)


class RecommendationPayload(ContractModel):
	id: str = Field(min_length=1, max_length=64)
	case_id: str = Field(min_length=1, max_length=64)
	primary_diagnosis: str = Field(min_length=1, max_length=256)
	confidence: str = Field(default="Low", max_length=16)
	differential_diagnosis: list[Any] | dict[str, Any] = Field(default_factory=list)
	action_plan: list[Any] | dict[str, Any] | str = Field(default_factory=dict)
	citations: list[Any] | dict[str, Any] = Field(default_factory=list)
	referral_facility: str | None = Field(default=None, max_length=128)
	drug_dosage: str | None = Field(default=None, max_length=256)
	counseling: str | None = None
	citation_source: str | None = Field(default=None, max_length=256)
	citation_text: str | None = None
	version: int = Field(default=1, ge=1)
	updated_at: int = Field(default_factory=now_ms, ge=0)


class SyncRecord(ContractModel):
	client_record_id: str = Field(default_factory=lambda: str(uuid.uuid4()), max_length=64)
	patient: PatientPayload
	case: CasePayload
	recommendation: RecommendationPayload | None = None


class SyncBatchRequest(ContractModel):
	idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)
	records: list[SyncRecord] = Field(min_length=1, max_length=500)


class RecordStatus(str, Enum):
	CREATED = "CREATED"
	UPDATED = "UPDATED"
	UNCHANGED = "UNCHANGED"
	CONFLICT = "CONFLICT"
	REJECTED = "REJECTED"


class SyncRecordResult(ContractModel):
	client_record_id: str
	patient_id: str
	case_id: str
	status: RecordStatus
	server_version: int | None = None
	server_updated_at: int | None = None
	reason_code: str | None = None
	message: str | None = None


class SyncBatchResponse(ContractModel):
	idempotency_key: str
	replayed: bool = False
	accepted: int
	rejected: int
	results: list[SyncRecordResult]


class ManifestResource(ContractModel):
	id: str
	resource_type: str
	resource_id: str
	version: int
	download_url: str
	sha256: str
	size_bytes: int
	media_type: str
	etag: str
	published_at: int | None


class ResourcePublishRequest(ContractModel):
	resource_type: Literal["model", "reference_data"]
	resource_id: str = Field(min_length=1, max_length=64)
	version: int = Field(ge=1)
	artifact_path: str = Field(min_length=1)
	media_type: str | None = Field(default=None, max_length=128)
	metadata: dict[str, Any] = Field(default_factory=dict)


class ManifestSignature(ContractModel):
	algorithm: Literal["ES256"] = "ES256"
	kid: str
	value: str


class DownloadManifest(ContractModel):
	generated_at: int
	expires_at: int
	resources: list[ManifestResource]
	signature: ManifestSignature


class FeedbackRequest(ContractModel):
	disposition: FeedbackDisposition
	confirmed_diagnosis: str | None = Field(default=None, max_length=256)
	notes: str | None = None
	structured_feedback: dict[str, Any] = Field(default_factory=dict)


class FeedbackResponse(ContractModel):
	id: str
	case_id: str
	recommendation_id: str | None
	reviewer_id: str
	disposition: FeedbackDisposition
	confirmed_diagnosis: str | None
	notes: str | None
	structured_feedback: dict[str, Any]
	created_at: int
	updated_at: int


def _payload_hash(batch: SyncBatchRequest) -> str:
	canonical = batch.model_dump_json(exclude={"idempotency_key"}, by_alias=True)
	return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _incoming_wins(existing: Any, version: int, updated_at: int) -> bool:
	return (version, updated_at) > (existing.version, existing.updated_at)


def _same_revision(existing: Any, version: int, updated_at: int) -> bool:
	return (version, updated_at) == (existing.version, existing.updated_at)


def _patient_data(payload: PatientPayload) -> dict[str, Any]:
	return payload.model_dump()


def _case_data(payload: CasePayload) -> dict[str, Any]:
	return payload.model_dump()


def _recommendation_data(payload: RecommendationPayload) -> dict[str, Any]:
	data = payload.model_dump()
	data["differential_json"] = data.pop("differential_diagnosis")
	return data


def _process_record(db: Session, record: SyncRecord, user: AuthUser) -> SyncRecordResult:
	if user.role == Role.ASHA_WORKER and record.patient.asha_id != user.user_id:
		raise PermissionError("OWNERSHIP_DENIED")
	if record.case.patient_id != record.patient.id:
		raise ValueError("PATIENT_CASE_MISMATCH")
	if record.recommendation and record.recommendation.case_id != record.case.id:
		raise ValueError("CASE_RECOMMENDATION_MISMATCH")

	patient = crud.get_patient(db, record.patient.id)
	case = crud.get_case(db, record.case.id)
	if patient and user.role == Role.ASHA_WORKER and patient.asha_id != user.user_id:
		raise PermissionError("OWNERSHIP_DENIED")
	if case and case.patient_id != record.patient.id:
		raise PermissionError("CASE_PATIENT_IMMUTABLE")

	recommendation = (
		crud.get_recommendation_by_case(db, record.case.id)
		if record.recommendation
		else None
	)
	conflicts = [
		existing
		for existing, version, updated_at in (
			(patient, record.patient.version, record.patient.updated_at),
			(case, record.case.version, record.case.updated_at),
			(
				recommendation,
				record.recommendation.version if record.recommendation else 0,
				record.recommendation.updated_at if record.recommendation else 0,
			),
		)
		if existing is not None
		and not _incoming_wins(existing, version, updated_at)
		and not _same_revision(existing, version, updated_at)
	]
	if conflicts:
		latest = max(conflicts, key=lambda item: (item.version, item.updated_at))
		return SyncRecordResult(
			client_record_id=record.client_record_id,
			patient_id=record.patient.id,
			case_id=record.case.id,
			status=RecordStatus.CONFLICT,
			server_version=latest.version,
			server_updated_at=latest.updated_at,
			reason_code="SERVER_REVISION_NEWER",
			message="The gateway retained its newer record revision.",
		)

	created = patient is None or case is None or (
		record.recommendation is not None and recommendation is None
	)
	updated = False

	if patient is None:
		patient = crud.create_patient(db, _patient_data(record.patient))
	elif _incoming_wins(patient, record.patient.version, record.patient.updated_at):
		crud.update_patient(db, patient.id, _patient_data(record.patient))
		updated = True

	if case is None:
		case = crud.create_case(db, _case_data(record.case))
	elif _incoming_wins(case, record.case.version, record.case.updated_at):
		crud.update_case(db, case.id, _case_data(record.case))
		updated = True

	if record.recommendation:
		if recommendation is None:
			crud.create_recommendation(db, _recommendation_data(record.recommendation))
		elif _incoming_wins(
			recommendation,
			record.recommendation.version,
			record.recommendation.updated_at,
		):
			crud.update_recommendation(
				db, recommendation.id, _recommendation_data(record.recommendation)
			)
			updated = True
	return SyncRecordResult(
		client_record_id=record.client_record_id,
		patient_id=record.patient.id,
		case_id=record.case.id,
		status=(
			RecordStatus.CREATED
			if created
			else RecordStatus.UPDATED
			if updated
			else RecordStatus.UNCHANGED
		),
		server_version=case.version,
		server_updated_at=case.updated_at,
	)


@router.post("/upload", response_model=SyncBatchResponse)
@router.post("", response_model=SyncBatchResponse, include_in_schema=False)
async def sync_batch(
	batch: SyncBatchRequest,
	idempotency_header: str | None = Header(
		default=None, alias="Idempotency-Key", min_length=8, max_length=128
	),
	db: Session = Depends(get_db),
	user: AuthUser = Depends(require_roles([Role.ASHA_WORKER, Role.MEDICAL_OFFICER])),
):
	request_hash = _payload_hash(batch)
	header_key = idempotency_header if isinstance(idempotency_header, str) else None
	key = header_key or batch.idempotency_key or f"sha256:{request_hash}"
	existing_request = crud.get_idempotency_record(db, user.user_id, "sync.upload", key)
	if existing_request:
		if existing_request.request_hash != request_hash:
			raise HTTPException(
				status_code=status.HTTP_409_CONFLICT,
				detail="Idempotency key was already used with a different request",
			)
		replayed_payload = dict(existing_request.response_payload)
		replayed_payload["replayed"] = True
		return SyncBatchResponse(**replayed_payload)

	results: list[SyncRecordResult] = []
	for record in batch.records:
		try:
			with db.begin_nested():
				results.append(_process_record(db, record, user))
		except (PermissionError, ValueError) as exc:
			results.append(
				SyncRecordResult(
					client_record_id=record.client_record_id,
					patient_id=record.patient.id,
					case_id=record.case.id,
					status=RecordStatus.REJECTED,
					reason_code=str(exc),
					message="Record rejected.",
				)
			)
		except Exception:
			results.append(
				SyncRecordResult(
					client_record_id=record.client_record_id,
					patient_id=record.patient.id,
					case_id=record.case.id,
					status=RecordStatus.REJECTED,
					reason_code="INVALID_RECORD",
					message="Record rejected.",
				)
			)

	response = SyncBatchResponse(
		idempotency_key=key,
		accepted=sum(
			result.status
			in {RecordStatus.CREATED, RecordStatus.UPDATED, RecordStatus.UNCHANGED}
			for result in results
		),
		rejected=sum(
			result.status in {RecordStatus.REJECTED, RecordStatus.CONFLICT}
			for result in results
		),
		results=results,
	)
	settings = get_settings()
	crud.create_idempotency_record(
		db,
		{
			"id": str(uuid.uuid4()),
			"user_id": user.user_id,
			"endpoint": "sync.upload",
			"idempotency_key": key,
			"request_hash": request_hash,
			"response_payload": response.model_dump(mode="json"),
			"status_code": 200,
			"expires_at": now_ms() + settings.sync.idempotency_ttl_hours * 3_600_000,
		},
	)
	db.commit()
	return response


def _resource_path(artifact_path: str) -> Path:
	settings = get_settings()
	root = settings.sync.resource_dir.resolve()
	path = Path(artifact_path)
	resolved = path.resolve() if path.is_absolute() else (root / path).resolve()
	if resolved != root and root not in resolved.parents:
		raise HTTPException(status_code=404, detail="Resource not found")
	if not resolved.is_file():
		raise HTTPException(status_code=404, detail="Resource not found")
	return resolved


def _resource_checksum(path: Path) -> str:
	digest = hashlib.sha256()
	with path.open("rb") as source:
		for chunk in iter(lambda: source.read(1024 * 1024), b""):
			digest.update(chunk)
	return digest.hexdigest()


def _sign_manifest(payload: dict[str, Any]) -> ManifestSignature:
	settings = get_settings()
	key = next(
		(
			item
			for item in settings.auth.keys
			if item.kid == settings.auth.active_kid and item.private_key_path
		),
		None,
	)
	if key is None or key.private_key_path is None:
		raise HTTPException(status_code=503, detail="Manifest signing unavailable")
	private_key = serialization.load_pem_private_key(
		key.private_key_path.read_bytes(), password=None
	)
	if not isinstance(private_key, ec.EllipticCurvePrivateKey):
		raise HTTPException(status_code=503, detail="Manifest signing unavailable")
	canonical = json.dumps(
		payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
	).encode("utf-8")
	signature = private_key.sign(canonical, ec.ECDSA(hashes.SHA256()))
	value = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
	return ManifestSignature(kid=key.kid, value=value)


@router.post(
	"/resources",
	response_model=ManifestResource,
	status_code=status.HTTP_201_CREATED,
)
async def publish_resource(
	payload: ResourcePublishRequest,
	request: Request,
	db: Session = Depends(get_db),
	_officer: AuthUser = Depends(require_roles([Role.MEDICAL_OFFICER])),
):
	path = _resource_path(payload.artifact_path)
	checksum = _resource_checksum(path)
	published_at = now_ms()
	resource = crud.create_sync_resource(
		db,
		{
			"id": str(uuid.uuid4()),
			"resource_type": payload.resource_type,
			"resource_id": payload.resource_id,
			"operation": SyncOperation.UPSERT,
			"version": payload.version,
			"payload": payload.metadata,
			"checksum_sha256": checksum,
			"sync_status": SyncStatus.SYNCED,
			"synced_at": published_at,
			"artifact_path": payload.artifact_path,
			"media_type": payload.media_type
			or mimetypes.guess_type(path.name)[0]
			or "application/octet-stream",
			"size_bytes": path.stat().st_size,
			"published_at": published_at,
			"active": True,
		},
	)
	db.commit()
	return ManifestResource(
		id=resource.id,
		resource_type=resource.resource_type,
		resource_id=resource.resource_id,
		version=resource.version,
		download_url=str(
			request.url_for("download_resource", resource_id=resource.id)
		),
		sha256=checksum,
		size_bytes=path.stat().st_size,
		media_type=resource.media_type,
		etag=f'"sha256-{checksum}"',
		published_at=published_at,
	)


@router.get("/manifest", response_model=DownloadManifest)
@router.get("/download", response_model=DownloadManifest, include_in_schema=False)
async def download_manifest(
	request: Request,
	resource_type: str | None = Query(default=None, max_length=64),
	db: Session = Depends(get_db),
	_user: AuthUser = Depends(
		require_roles([Role.ASHA_WORKER, Role.MEDICAL_OFFICER])
	),
):
	resources: list[ManifestResource] = []
	seen_resources: set[tuple[str, str]] = set()
	for resource in crud.list_active_sync_resources(db, resource_type):
		logical_key = (resource.resource_type, resource.resource_id)
		if logical_key in seen_resources:
			continue
		seen_resources.add(logical_key)
		if not resource.artifact_path:
			continue
		path = _resource_path(resource.artifact_path)
		checksum = _resource_checksum(path)
		if resource.checksum_sha256 != checksum or resource.size_bytes != path.stat().st_size:
			resource.checksum_sha256 = checksum
			resource.size_bytes = path.stat().st_size
		resources.append(
			ManifestResource(
				id=resource.id,
				resource_type=resource.resource_type,
				resource_id=resource.resource_id,
				version=resource.version,
				download_url=str(request.url_for("download_resource", resource_id=resource.id)),
				sha256=checksum,
				size_bytes=path.stat().st_size,
				media_type=resource.media_type,
				etag=f'"sha256-{checksum}"',
				published_at=resource.published_at,
			)
		)
	generated_at = now_ms()
	payload = {
		"generated_at": generated_at,
		"expires_at": generated_at
		+ get_settings().sync.manifest_ttl_minutes * 60_000,
		"resources": [item.model_dump(mode="json") for item in resources],
	}
	signature = _sign_manifest(payload)
	db.commit()
	return DownloadManifest(**payload, signature=signature)


def _range_bounds(range_header: str, size: int) -> tuple[int, int]:
	match = RANGE_PATTERN.fullmatch(range_header.strip())
	if not match:
		raise HTTPException(status_code=416, detail="Invalid range")
	start_text, end_text = match.groups()
	if not start_text:
		length = int(end_text)
		if length <= 0:
			raise HTTPException(status_code=416, detail="Invalid range")
		return max(size - length, 0), size - 1
	start = int(start_text)
	end = int(end_text) if end_text else size - 1
	if start >= size or end < start:
		raise HTTPException(
			status_code=416,
			detail="Range not satisfiable",
			headers={"Content-Range": f"bytes */{size}"},
		)
	return start, min(end, size - 1)


def _file_chunks(path: Path, start: int, end: int):
	with path.open("rb") as source:
		source.seek(start)
		remaining = end - start + 1
		while remaining:
			chunk = source.read(min(1024 * 1024, remaining))
			if not chunk:
				break
			remaining -= len(chunk)
			yield chunk


@router.get("/resources/{resource_id}", name="download_resource")
@router.get("/download/{resource_id}", include_in_schema=False)
async def download_resource(
	resource_id: str,
	request: Request,
	db: Session = Depends(get_db),
	_user: AuthUser = Depends(
		require_roles([Role.ASHA_WORKER, Role.MEDICAL_OFFICER])
	),
):
	resource = crud.get_sync_resource(db, resource_id)
	if not resource or not resource.active or not resource.artifact_path:
		raise HTTPException(status_code=404, detail="Resource not found")
	path = _resource_path(resource.artifact_path)
	checksum = resource.checksum_sha256 or _resource_checksum(path)
	etag = f'"sha256-{checksum}"'
	if request.headers.get("if-none-match") == etag:
		return Response(status_code=304, headers={"ETag": etag})
	size = path.stat().st_size
	headers = {
		"Accept-Ranges": "bytes",
		"ETag": etag,
		"X-Checksum-SHA256": checksum,
		"Content-Disposition": f'attachment; filename="{path.name}"',
	}
	range_header = request.headers.get("range")
	if range_header:
		start, end = _range_bounds(range_header, size)
		headers["Content-Range"] = f"bytes {start}-{end}/{size}"
		headers["Content-Length"] = str(end - start + 1)
		return StreamingResponse(
			_file_chunks(path, start, end),
			status_code=206,
			media_type=resource.media_type,
			headers=headers,
		)
	headers["Content-Length"] = str(size)
	return StreamingResponse(
		_file_chunks(path, 0, size - 1),
		media_type=resource.media_type
		or mimetypes.guess_type(path.name)[0]
		or "application/octet-stream",
		headers=headers,
	)


def _feedback_response(feedback: Any) -> FeedbackResponse:
	return FeedbackResponse(
		id=feedback.id,
		case_id=feedback.case_id,
		recommendation_id=feedback.recommendation_id,
		reviewer_id=feedback.reviewer_id,
		disposition=feedback.disposition,
		confirmed_diagnosis=feedback.confirmed_diagnosis,
		notes=feedback.notes,
		structured_feedback=feedback.structured_feedback,
		created_at=feedback.created_at,
		updated_at=feedback.updated_at,
	)


@router.put("/feedback/{case_id}", response_model=FeedbackResponse)
async def upsert_feedback(
	case_id: str,
	payload: FeedbackRequest,
	db: Session = Depends(get_db),
	officer: AuthUser = Depends(require_roles([Role.MEDICAL_OFFICER])),
):
	require_case_access(db, officer, case_id)
	recommendation = crud.get_recommendation_by_case(db, case_id)
	feedback = crud.get_clinical_feedback(db, case_id, officer.user_id)
	data = payload.model_dump()
	data.update(
		{
			"case_id": case_id,
			"recommendation_id": recommendation.id if recommendation else None,
			"reviewer_id": officer.user_id,
		}
	)
	if feedback:
		for key, value in data.items():
			setattr(feedback, key, value)
		feedback.updated_at = now_ms()
	else:
		data["id"] = str(uuid.uuid4())
		feedback = crud.create_clinical_feedback(db, data)
	db.commit()
	db.refresh(feedback)
	return _feedback_response(feedback)


@router.get("/feedback/{case_id}", response_model=FeedbackResponse)
async def get_feedback(
	case_id: str,
	db: Session = Depends(get_db),
	officer: AuthUser = Depends(require_roles([Role.MEDICAL_OFFICER])),
):
	feedback = crud.get_clinical_feedback(db, case_id, officer.user_id)
	if not feedback:
		raise HTTPException(status_code=404, detail="Feedback not found")
	return _feedback_response(feedback)
