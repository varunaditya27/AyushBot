from __future__ import annotations

import json
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

pytest.importorskip("alembic")

from backend.db import crud
from backend.db.migrate import upgrade
from backend.db.seed import seed_reference_data
from backend.db.session import get_engine, reset_engine


def _url(path: Path) -> str:
	return f"sqlite:///{path}"


def test_session_engine_is_lazy_and_follows_db_path_override(tmp_path, monkeypatch):
	reset_engine()
	first = tmp_path / "first.db"
	second = tmp_path / "second.db"

	monkeypatch.setenv("AYUSHBOT_DB_PATH", str(first))
	assert str(get_engine().url) == _url(first)

	monkeypatch.setenv("AYUSHBOT_DB_PATH", str(second))
	assert str(get_engine().url) == _url(second)
	assert not first.exists()

	reset_engine()


def test_migration_upgrade_path_creates_core_tables(tmp_path):
	database = tmp_path / "migrated.db"
	url = _url(database)

	upgrade(url)

	engine = sa.create_engine(url)
	tables = set(sa.inspect(engine).get_table_names())
	assert {
		"alembic_version",
		"patients",
		"cases",
		"recommendations",
		"facilities",
		"villages",
	} <= tables


def test_seed_reference_data_is_idempotent_after_migrations(tmp_path):
	database = tmp_path / "seed.db"
	url = _url(database)
	upgrade(url)
	engine = sa.create_engine(url)
	villages = tmp_path / "villages.json"
	facilities = tmp_path / "facilities.csv"
	villages.write_text(
		json.dumps(
			[
				{
					"id": "village-synthetic-1",
					"name": "Synthetic Village",
					"district": "Synthetic District",
					"state": "Synthetic State",
				}
			]
		),
		encoding="utf-8",
	)
	facilities.write_text(
		"\n".join(
			[
				"id,name,type,village_id,latitude,longitude,address,phone,active,metadata_json",
				(
					"facility-synthetic-1,Synthetic PHC,PHC,village-synthetic-1,"
					"12.34,56.78,Synthetic address,,true,{}"
				),
			]
		),
		encoding="utf-8",
	)

	with Session(engine, expire_on_commit=False) as db:
		first = seed_reference_data(db, villages=villages, facilities=facilities)
		second = seed_reference_data(db, villages=villages, facilities=facilities)
		assert first == second == {"villages": 1, "facilities": 1}
		assert len(crud.list_villages(db)) == 1
		assert len(crud.list_facilities(db)) == 1


def test_basic_crud_path_after_migrations(tmp_path):
	database = tmp_path / "crud.db"
	url = _url(database)
	upgrade(url)
	engine = sa.create_engine(url)

	with Session(engine, expire_on_commit=False) as db:
		crud.create_patient(
			db,
			{
				"id": "patient-synthetic-1",
				"name": "Synthetic Patient",
				"age_months": 24,
				"sex": "female",
				"village": "Synthetic Village",
				"asha_id": "asha-synthetic-1",
			},
		)
		crud.create_case(
			db,
			{
				"id": "case-synthetic-1",
				"patient_id": "patient-synthetic-1",
				"timestamp": 1,
				"symptoms": '["fever"]',
				"risk_tier": "LOW",
				"sync_status": "PENDING",
			},
		)
		crud.create_recommendation(
			db,
			{
				"id": "recommendation-synthetic-1",
				"case_id": "case-synthetic-1",
				"primary_diagnosis": "Synthetic",
				"confidence": "Low",
				"differential_json": "[]",
				"action_plan": '{"urgency": "ROUTINE"}',
			},
		)
		db.commit()

		case = crud.get_case(db, "case-synthetic-1")
		recommendation = crud.get_recommendation_by_case(db, "case-synthetic-1")
		assert case is not None and case.symptoms == ["fever"]
		assert recommendation is not None
		assert recommendation.action_plan == {"urgency": "ROUTINE"}
