# =============================================================================
# AyushBot Backend — Database Session Manager
# =============================================================================
#
# PURPOSE:
#   Manages SQLAlchemy engine and session lifecycle for the local SQLite
#   database. Provides a session factory and dependency injection for
#   FastAPI route handlers.
#
# SQLite CONFIGURATION:
#   - Database file: stored at a configurable path (default: /opt/ayushbot/data/ayushbot.db)
#   - WAL mode enabled: Write-Ahead Logging allows concurrent readers
#     during a write, which is important when Agent 4 (FL) writes training
#     logs while Agent 1-3 are reading encounter data.
#   - Journal size limit: 50 MB (prevents unbounded WAL growth on the
#     RPi 4's limited SD card storage)
#   - Foreign keys enforced: PRAGMA foreign_keys = ON
#
# SESSION MANAGEMENT:
#   Uses SQLAlchemy's sessionmaker to create scoped sessions:
#     - Each FastAPI request gets its own session (via Depends())
#     - Sessions are committed on success, rolled back on exception
#     - Sessions are closed after each request (no connection leaks)
#
# INITIALIZATION:
#   On first startup, if the database file does not exist:
#     1. Create all tables from the ORM models (db/models.py)
#     2. Seed static reference data (villages, facilities) from bundled
#        JSON/CSV files in data/
#     3. Log the database creation and seed status
#
# MIGRATION STRATEGY:
#   Alembic is used for schema migrations. Migration scripts are stored
#   in db/migrations/. On gateway software updates:
#     1. Run pending Alembic migrations automatically at startup
#     2. Migrations are forward-only (no downgrades in production)
#     3. Each migration is tested in CI before deployment
#
# BACKUP:
#   The database file is backed up daily to a secondary location on the
#   RPi 4's SD card. The backup script is triggered by a systemd timer
#   (see infra/ for deployment details).
#
# INPUTS:
#   - config.yaml "database" section: db_path, wal_mode, journal_size_limit
#
# EXPORTS:
#   - get_db(): FastAPI dependency that yields a SQLAlchemy session
#   - engine: SQLAlchemy engine instance (for direct use by migrations)
# =============================================================================
