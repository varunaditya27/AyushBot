# Android Offline Sync Contracts

Base URL for the local gateway:

```text
Development: http://<gateway-host>:8000/api/v1
Production-style TLS: https://<gateway-host>:8443/api/v1
```

Android must remain offline-first. Creating a visit, computing deterministic
triage, showing a recommendation, and storing history must work without this
backend. These endpoints are for authentication, sync, resource updates, and
optional heavier backend workflows once connectivity exists.

All endpoints except health checks require:

```http
Authorization: Bearer <ES256 access token>
Content-Type: application/json
```

Timestamps are Unix epoch milliseconds. Android must retain the same UUID,
`version`, and `updated_at` while retrying a record.

## Auth

```http
POST /auth/login
```

```json
{
  "username": "asha-001",
  "password": "development-password",
  "device_id": "android-tablet-001"
}
```

Successful response:

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer"
}
```

Bad credentials, disabled users, and unknown/unassigned ASHA devices return
HTTP `401` with a safe generic detail.

```http
POST /auth/refresh
```

```json
{
  "refresh_token": "<jwt>"
}
```

Response shape matches `/auth/login`. Refresh token rotation is enabled; Android
must replace both locally stored tokens after a successful refresh.

```http
GET /auth/me
```

```json
{
  "user_id": "asha-001",
  "role": "AshaWorker",
  "device_id": "android-tablet-001"
}
```

## Health Checks

```http
GET /health/live
GET /health/ping
GET /health/ready
```

`/health/live` is the lightweight liveness endpoint. `/health/ping` is a
backward-compatible alias.

```json
{"status": "ok"}
```

`/health/ready` checks the database and reports optional Redis/MQTT components
without requiring them when disabled:

```json
{
  "status": "ready",
  "checks": {
    "database": {"status": "ready", "required": true},
    "redis": {"status": "disabled", "required": false},
    "mqtt": {"status": "disabled", "required": false}
  }
}
```

## Upload Offline Records

```http
POST /sync/upload
Idempotency-Key: <8-128 stable characters>
```

The idempotency key identifies the complete request body. Repeating the same
key and body returns the original response with `replayed: true`. Reusing a key
with a different body returns HTTP `409`.

```json
{
  "records": [
    {
      "client_record_id": "android-queue-0001",
      "patient": {
        "id": "patient-synthetic-001",
        "abha_id": null,
        "name": null,
        "age_months": 24,
        "sex": "female",
        "village": "village-synthetic",
        "asha_id": "asha-001",
        "version": 3,
        "updated_at": 1781450100000
      },
      "case": {
        "id": "case-synthetic-001",
        "patient_id": "patient-synthetic-001",
        "timestamp": 1781450000000,
        "spo2": 97,
        "heart_rate": 104,
        "temperature": 37.2,
        "weight": 11.5,
        "symptoms": [{"code": "fever", "present": true}],
        "risk_tier": "LOW",
        "risk_explanation": {"score": 0.12, "factors": ["synthetic"]},
        "errors": [],
        "sync_status": "PENDING",
        "version": 3,
        "updated_at": 1781450100000
      },
      "recommendation": {
        "id": "recommendation-synthetic-001",
        "case_id": "case-synthetic-001",
        "primary_diagnosis": "Synthetic diagnosis",
        "confidence": "Low",
        "differential_diagnosis": [{"condition": "Synthetic condition"}],
        "action_plan": {"urgency": "ROUTINE", "steps": []},
        "citations": [{"source": "approved-reference", "section": "example"}],
        "version": 3,
        "updated_at": 1781450100000
      }
    }
  ]
}
```

Response:

```json
{
  "idempotency_key": "android-batch-20260614-0001",
  "replayed": false,
  "accepted": 1,
  "rejected": 0,
  "results": [
    {
      "client_record_id": "android-queue-0001",
      "patient_id": "patient-synthetic-001",
      "case_id": "case-synthetic-001",
      "status": "UPDATED",
      "server_version": 3,
      "server_updated_at": 1781450100000,
      "reason_code": null,
      "message": null
    }
  ]
}
```

Record statuses:

| Status | Android action |
|---|---|
| `CREATED` | Mark the local record synchronized. |
| `UPDATED` | Mark the local record synchronized. |
| `UNCHANGED` | Mark the local record synchronized. |
| `CONFLICT` | Keep the local record and request/review the server revision. |
| `REJECTED` | Keep the local record and show/log `reason_code`. |

Conflict ordering compares `(version, updated_at)`. The greater tuple wins.
Equal tuples are idempotent and return `UNCHANGED`. A conflict does not apply
any portion of that patient/case/recommendation record.

## Optional Backend Triage

Android should compute the primary offline recommendation locally. It may call
the backend triage endpoint only as an enhancement when the gateway is reachable:

```http
POST /triage/assess
```

If the request fails, times out, or returns a server error, Android must keep and
display its local recommendation. Backend triage responses should be saved
locally as an enhancement and synced like any other recommendation revision.

## Download Manifest

```http
GET /sync/manifest
GET /sync/manifest?resource_type=model
GET /sync/manifest?resource_type=reference_data
```

```json
{
  "generated_at": 1781450200000,
  "expires_at": 1781451100000,
  "resources": [
    {
      "id": "resource-facilities-v2",
      "resource_type": "reference_data",
      "resource_id": "facilities",
      "version": 2,
      "download_url": "https://gateway:8443/api/v1/sync/resources/resource-facilities-v2",
      "sha256": "64-lowercase-hex-characters",
      "size_bytes": 1024,
      "media_type": "application/json",
      "etag": "\"sha256-64-lowercase-hex-characters\"",
      "published_at": 1781450000000
    }
  ],
  "signature": {
    "algorithm": "ES256",
    "kid": "gateway-2026-01",
    "value": "<base64url DER ECDSA signature without padding>"
  }
}
```

To verify the manifest:

1. Remove the top-level `signature` object.
2. Serialize the remaining object as UTF-8 JSON with keys sorted, no
   whitespace, ASCII escaping enabled, and separators `,` and `:`.
3. Base64url-decode `signature.value`, adding `=` padding as required.
4. Verify the DER-encoded ECDSA/SHA-256 signature using the public ES256 key
   identified by `kid`.
5. Reject an expired manifest.

## Resumable Resource Download

```http
GET /sync/resources/{manifest-resource-id}
Range: bytes=1048576-
If-None-Match: "<previous-etag>"
```

The gateway returns:

- HTTP `200` for the complete file.
- HTTP `206` with `Content-Range` for a valid range.
- HTTP `304` when `If-None-Match` matches.
- HTTP `416` for an invalid/unsatisfiable range.
- `Accept-Ranges: bytes`
- `ETag: "sha256-<checksum>"`
- `X-Checksum-SHA256: <checksum>`
- `Content-Length`

Android must compute SHA-256 after the final byte is assembled and compare it
with both the manifest and `X-Checksum-SHA256` before activating the resource.

Gateway operators place an artifact under `var/sync_resources` and a
MedicalOfficer registers it with:

```http
POST /sync/resources
```

```json
{
  "resource_type": "reference_data",
  "resource_id": "facilities",
  "version": 2,
  "artifact_path": "facilities-v2.json",
  "media_type": "application/json",
  "metadata": {"schema_version": 1}
}
```

The gateway computes the checksum and size; clients must never supply trusted
checksum values.

## Triage History

```http
GET /triage/history/{patient_id}?page=1&page_size=20
```

```json
{
  "items": [
    {
      "id": "case-synthetic-001",
      "patient_id": "patient-synthetic-001",
      "timestamp": 1781450000000,
      "risk_tier": "LOW",
      "risk_explanation": {},
      "symptoms": [],
      "spo2": 97,
      "heart_rate": 104,
      "temperature": 37.2,
      "version": 3,
      "updated_at": 1781450100000,
      "ruleset_version": "ayushbot-pretriage-demo",
      "growth_reference_version": "who-waz-demo",
      "triage_model_version": "stub-demo"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1,
  "total_pages": 1
}
```

ASHA credentials can retrieve only assigned patients. MedicalOfficer
credentials retain administrative access.

## Telemetry

```http
POST /telemetry
```

```json
{
  "event_id": "telemetry-synthetic-001",
  "device_id": "tablet-asha-001",
  "case_id": "case-synthetic-001",
  "event_type": "vitals",
  "timestamp": 1781450000000,
  "readings": {"spo2": 97}
}
```

HTTP `202` means the event is already durable in the gateway database:

```json
{
  "event_id": "telemetry-synthetic-001",
  "status": "accepted",
  "persisted": true
}
```

Retrying an existing `event_id` returns `status: "duplicate"` without creating
another row.

## Medical Officer Feedback

Only a MedicalOfficer token may call:

```http
PUT /sync/feedback/{case_id}
GET /sync/feedback/{case_id}
```

```json
{
  "disposition": "CONFIRMED",
  "confirmed_diagnosis": "Synthetic diagnosis",
  "notes": "No real patient data.",
  "structured_feedback": {
    "follow_up_days": 2
  }
}
```

`disposition` is one of `CONFIRMED`, `MODIFIED`, `REJECTED`, or `UNSURE`.
Repeated `PUT` requests update the same reviewer/case feedback record.
