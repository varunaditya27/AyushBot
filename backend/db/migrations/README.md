# Database Migrations

Run from the repository root:

```bash
.venv/bin/alembic -c backend/db/alembic.ini upgrade head
.venv/bin/alembic -c backend/db/alembic.ini current
.venv/bin/alembic -c backend/db/alembic.ini revision --autogenerate -m "change"
```

`AYUSHBOT_CONFIG` and `AYUSHBOT_DB_PATH` are honored. SQLite migrations use
Alembic batch mode so future constraint and column changes remain portable.
