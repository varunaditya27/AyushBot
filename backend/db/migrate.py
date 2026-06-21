"""Programmatic and command-line Alembic migration helpers."""

from __future__ import annotations

import argparse

from alembic import command
from alembic.config import Config

from backend.config import PROJECT_ROOT

ALEMBIC_INI = PROJECT_ROOT / "backend" / "db" / "alembic.ini"


def alembic_config(database_url: str | None = None) -> Config:
	config = Config(str(ALEMBIC_INI))
	if database_url:
		config.set_main_option("sqlalchemy.url", database_url)
	return config


def upgrade(database_url: str | None = None, revision: str = "head") -> None:
	command.upgrade(alembic_config(database_url), revision)


def downgrade(database_url: str | None = None, revision: str = "base") -> None:
	command.downgrade(alembic_config(database_url), revision)


def current(database_url: str | None = None) -> None:
	command.current(alembic_config(database_url))


def main() -> int:
	parser = argparse.ArgumentParser(description="Manage the AyushBot database schema")
	parser.add_argument("command", choices=("upgrade", "downgrade", "current"))
	parser.add_argument("--database-url")
	parser.add_argument("--revision")
	args = parser.parse_args()

	if args.command == "upgrade":
		upgrade(args.database_url, args.revision or "head")
	elif args.command == "downgrade":
		downgrade(args.database_url, args.revision or "base")
	else:
		current(args.database_url)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
