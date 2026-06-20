"""Validate and seed village and facility reference data."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from sqlalchemy.orm import Session

from backend.db import crud
from backend.db.models import FacilityType
from backend.db.session import SessionLocal, get_engine


class SeedModel(BaseModel):
	model_config = ConfigDict(extra="forbid")


class VillageSeed(SeedModel):
	id: str = Field(min_length=1, max_length=64)
	name: str = Field(min_length=1, max_length=256)
	district: str | None = None
	state: str | None = None
	pincode: str | None = Field(default=None, max_length=12)
	latitude: float | None = Field(default=None, ge=-90, le=90)
	longitude: float | None = Field(default=None, ge=-180, le=180)
	active: bool = True
	metadata_json: dict[str, Any] = Field(default_factory=dict)


class FacilitySeed(SeedModel):
	id: str = Field(min_length=1, max_length=64)
	name: str = Field(min_length=1, max_length=256)
	type: FacilityType
	village_id: str | None = Field(default=None, max_length=64)
	latitude: float = Field(ge=-90, le=90)
	longitude: float = Field(ge=-180, le=180)
	address: str | None = None
	phone: str | None = Field(default=None, max_length=32)
	active: bool = True
	metadata_json: dict[str, Any] = Field(default_factory=dict)

	@field_validator("village_id", "address", "phone", mode="before")
	@classmethod
	def blank_to_none(cls, value: Any) -> Any:
		if value == "":
			return None
		return value

	@field_validator("metadata_json", mode="before")
	@classmethod
	def parse_metadata(cls, value: Any) -> Any:
		if value in (None, ""):
			return {}
		if isinstance(value, str):
			return json.loads(value)
		return value


def _read_json_records(path: Path) -> list[dict[str, Any]]:
	data = json.loads(path.read_text(encoding="utf-8"))
	if isinstance(data, dict):
		data = data.get("records")
	if not isinstance(data, list):
		raise ValueError(f"{path} must contain a JSON array or a records array")
	if not all(isinstance(item, dict) for item in data):
		raise ValueError(f"Every record in {path} must be a JSON object")
	return data


def _read_csv_records(path: Path) -> list[dict[str, Any]]:
	with path.open(newline="", encoding="utf-8") as handle:
		return list(csv.DictReader(handle))


def _load(path: Path) -> list[dict[str, Any]]:
	if not path.is_file():
		raise FileNotFoundError(f"Seed file not found: {path}")
	if path.suffix.lower() == ".json":
		return _read_json_records(path)
	if path.suffix.lower() == ".csv":
		return _read_csv_records(path)
	raise ValueError(f"Unsupported seed format for {path}; use .csv or .json")


def _validate(model: type[SeedModel], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
	validated: list[dict[str, Any]] = []
	errors: list[str] = []
	for index, record in enumerate(records, start=1):
		try:
			validated.append(model.model_validate(record).model_dump())
		except (ValidationError, ValueError, json.JSONDecodeError) as exc:
			errors.append(f"record {index}: {exc}")
	if errors:
		raise ValueError("Seed validation failed:\n" + "\n".join(errors))
	return validated


def seed_villages(db: Session, path: str | Path) -> int:
	records = _validate(VillageSeed, _load(Path(path)))
	for record in records:
		crud.upsert_village(db, record)
	return len(records)


def seed_facilities(db: Session, path: str | Path) -> int:
	records = _validate(FacilitySeed, _load(Path(path)))
	for record in records:
		if record.get("village_id") and crud.get_village(db, record["village_id"]) is None:
			raise ValueError(
				f"Facility {record['id']} references unknown village {record['village_id']}"
			)
		crud.upsert_facility(db, record)
	return len(records)


def seed_reference_data(
	db: Session,
	*,
	villages: str | Path | None = None,
	facilities: str | Path | None = None,
) -> dict[str, int]:
	counts = {"villages": 0, "facilities": 0}
	with db.begin():
		if villages:
			counts["villages"] = seed_villages(db, villages)
		if facilities:
			counts["facilities"] = seed_facilities(db, facilities)
	return counts


def main() -> int:
	parser = argparse.ArgumentParser(description="Seed AyushBot reference data")
	parser.add_argument("--villages", type=Path)
	parser.add_argument("--facilities", type=Path)
	args = parser.parse_args()
	if not args.villages and not args.facilities:
		parser.error("provide --villages and/or --facilities")

	get_engine()
	with SessionLocal() as db:
		counts = seed_reference_data(
			db, villages=args.villages, facilities=args.facilities
		)
	print(
		f"Seeded {counts['villages']} villages and {counts['facilities']} facilities"
	)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
