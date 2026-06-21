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
#     local gateway host storage)
#   - Foreign keys enforced: PRAGMA foreign_keys = ON
#
# SESSION MANAGEMENT:
#   Uses SQLAlchemy's sessionmaker to create scoped sessions:
#     - Each FastAPI request gets its own session (via Depends())
#     - Sessions are committed on success, rolled back on exception
#     - Sessions are closed after each request (no connection leaks)
#
# INITIALIZATION:
#   The SQLAlchemy engine is created lazily from the current configuration.
#   Schema changes are applied only through Alembic migrations; this module
#   does not call ORM create_all during application startup.
#
# MIGRATION STRATEGY:
#   Alembic is used for schema migrations. Migration scripts are stored
#   in db/migrations/. On gateway software updates:
#     1. Run pending Alembic migrations automatically at startup
#     2. Migrations are forward-only (no downgrades in production)
#     3. Each migration is tested in CI before deployment
#
# BACKUP:
#   The database file should be backed up by the local deployment wrapper when
#   persistent patient/case data is being retained.
#
# INPUTS:
#   - config.yaml "database" section: db_path, wal_mode, journal_size_limit
#
# EXPORTS:
#   - get_db(): FastAPI dependency that yields a SQLAlchemy session
#   - get_engine(): lazily configured SQLAlchemy engine
# =============================================================================

from __future__ import annotations

import logging
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.config import load_settings

logger = logging.getLogger(__name__)


def _sqlite_url(path: Path) -> str:
	return f"sqlite:///{path}"


def _configure_sqlite(engine: Engine, wal_mode: bool, journal_limit_mb: int) -> None:
	@event.listens_for(engine, "connect")
	def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
		cursor = dbapi_connection.cursor()
		try:
			cursor.execute("PRAGMA foreign_keys=ON")
			cursor.execute("PRAGMA busy_timeout=15000")
			if wal_mode:
				cursor.execute("PRAGMA journal_mode=WAL")
				cursor.execute("PRAGMA synchronous=NORMAL")
				journal_limit_bytes = max(1, int(journal_limit_mb) * 1024 * 1024)
				cursor.execute(f"PRAGMA journal_size_limit={journal_limit_bytes}")
		finally:
			cursor.close()


_engine: Engine | None = None
_engine_url: str | None = None
SessionLocal = sessionmaker(
	autocommit=False,
	autoflush=False,
	expire_on_commit=False,
)


def create_engine_from_config(
	config_path: str | None = None,
	*,
	database_url: str | None = None,
) -> Engine:
	settings = load_settings(config_path).database
	settings.path.parent.mkdir(parents=True, exist_ok=True)
	url = database_url or _sqlite_url(settings.path)
	engine = create_engine(
		url,
		connect_args={"check_same_thread": False, "timeout": 30},
		pool_pre_ping=True,
	)
	_configure_sqlite(engine, settings.wal_mode, settings.journal_size_limit_mb)
	return engine


def get_engine(
	config_path: str | None = None,
	*,
	database_url: str | None = None,
	force_reload: bool = False,
) -> Engine:
	global _engine, _engine_url

	settings = load_settings(config_path).database
	settings.path.parent.mkdir(parents=True, exist_ok=True)
	url = database_url or _sqlite_url(settings.path)
	if force_reload or _engine is None or _engine_url != url:
		if _engine is not None:
			_engine.dispose()
		_engine = create_engine(
			url,
			connect_args={"check_same_thread": False, "timeout": 30},
			pool_pre_ping=True,
		)
		_configure_sqlite(_engine, settings.wal_mode, settings.journal_size_limit_mb)
		_engine_url = url
		SessionLocal.configure(bind=_engine)
	return _engine


def reset_engine() -> None:
	global _engine, _engine_url
	if _engine is not None:
		_engine.dispose()
	_engine = None
	_engine_url = None
	SessionLocal.configure(bind=None)


def init_db() -> None:
	from backend.db.migrate import upgrade

	upgrade(str(get_engine().url))


def get_db() -> Generator[Session, None, None]:
	get_engine()
	db = SessionLocal()
	try:
		yield db
		db.commit()
	except Exception:
		db.rollback()
		raise
	finally:
		db.close()
