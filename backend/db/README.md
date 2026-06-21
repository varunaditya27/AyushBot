# Backend Database

AyushBot uses SQLite with foreign-key enforcement, WAL mode, SQLAlchemy 2, and
Alembic migrations. Timestamps are UTC Unix milliseconds to preserve Android
sync compatibility.

## Schema

Core clinical records remain in `patients`, `cases`, and `recommendations`.
Symptoms, differential diagnoses, action plans, telemetry readings, sync
payloads, metrics, consent evidence, and audit details use SQLAlchemy `JSON`.
Legacy API callers may still submit serialized JSON strings; CRUD normalizes
them before storage.

Phase 1 also defines:

- `villages`, `facilities`, `road_edges`
- `clinical_feedback`, `model_versions`
- `devices`, `sync_resources`, `telemetry_events`
- `fl_rounds`, `privacy_budgets`
- `consent_records`, `audit_events`

Enums are stored as constrained strings for SQLite portability. Foreign keys
use explicit delete behavior, and operational query paths have named indexes.

## Migrations

```bash
make migrate-db
.venv/bin/alembic -c backend/db/alembic.ini current
```

The initial migration supports both a fresh database and the previous
unversioned three-table schema. Application startup runs `upgrade head`.

## Reference Data

See [data/reference/README.md](../../data/reference/README.md) for exact village
and facility CSV/JSON formats. Seed with:

```bash
make seed-db
```
