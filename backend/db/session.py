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

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Generator, Optional

import yaml
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.db.models import Base

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = "/opt/ayushbot/data/ayushbot.db"
DEFAULT_WAL_MODE = True
DEFAULT_JOURNAL_LIMIT_MB = 50


def _load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
	path = (
		config_path
		or os.getenv("AYUSHBOT_CONFIG")
		or os.path.join(os.path.dirname(__file__), "..", "config.yaml")
	)
	path = os.path.abspath(path)
	if not os.path.exists(path):
		logger.warning("Config file not found at %s; using defaults", path)
		return {}
	try:
		with open(path, "r", encoding="utf-8") as handle:
			return yaml.safe_load(handle) or {}
	except Exception as exc:  # pragma: no cover - defensive logging
		logger.error("Failed to load config from %s: %s", path, exc)
		return {}


def _database_settings(config: Dict[str, Any]) -> Dict[str, Any]:
	db_config = config.get("database", {}) if isinstance(config, dict) else {}
	return {
		"path": os.getenv("AYUSHBOT_DB_PATH", db_config.get("path", DEFAULT_DB_PATH)),
		"wal_mode": str(
			os.getenv("AYUSHBOT_DB_WAL_MODE", db_config.get("wal_mode", DEFAULT_WAL_MODE))
		).lower()
		in {"1", "true", "yes", "y"},
		"journal_size_limit_mb": int(
			os.getenv(
				"AYUSHBOT_DB_JOURNAL_LIMIT_MB",
				db_config.get("journal_size_limit_mb", DEFAULT_JOURNAL_LIMIT_MB),
			)
		),
	}


def _sqlite_url(path: str) -> str:
	path = os.path.abspath(path)
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
				cursor.execute(
					"PRAGMA journal_size_limit=?",
					(max(1, int(journal_limit_mb) * 1024 * 1024),),
				)
		finally:
			cursor.close()


def create_engine_from_config(config_path: Optional[str] = None) -> Engine:
	config = _load_config(config_path)
	settings = _database_settings(config)
	db_url = _sqlite_url(settings["path"])
	engine = create_engine(
		db_url,
		connect_args={"check_same_thread": False, "timeout": 30},
		pool_pre_ping=True,
	)
	_configure_sqlite(engine, settings["wal_mode"], settings["journal_size_limit_mb"])
	return engine


engine = create_engine_from_config()
SessionLocal = sessionmaker(
	bind=engine,
	autocommit=False,
	autoflush=False,
	expire_on_commit=False,
)


def init_db() -> None:
	Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
	db = SessionLocal()
	try:
		yield db
		db.commit()
	except Exception:
		db.rollback()
		raise
	finally:
		db.close()
