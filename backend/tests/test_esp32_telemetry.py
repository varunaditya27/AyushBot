from __future__ import annotations

import importlib
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.config import clear_settings_cache
from backend.db import crud
from backend.db.models import Base, Device, DeviceStatus, DeviceType, TelemetryEvent
from backend.db.session import SessionLocal, reset_engine


def _load_api_main(tmp_path, monkeypatch):
	database = tmp_path / "esp32.db"
	config = tmp_path / "config.yaml"
	config.write_text(
		f"""
environment: development
database:
  path: {database}
redis:
  enabled: false
mqtt:
  enabled: false
""",
		encoding="utf-8",
	)
	monkeypatch.setenv("AYUSHBOT_CONFIG", str(config))
	clear_settings_cache()
	reset_engine()

	engine = create_engine(f"sqlite:///{database}")
	Base.metadata.create_all(engine)
	SessionLocal.configure(bind=engine)

	sys.modules.pop("backend.api.main", None)
	api_main = importlib.import_module("backend.api.main")
	return api_main, engine


def test_esp32_mqtt_telemetry_auto_registers_sensor_device(tmp_path, monkeypatch):
	api_main, engine = _load_api_main(tmp_path, monkeypatch)

	api_main._persist_telemetry(
		{
			"id": "esp32-event-001",
			"device_id": "esp32-demo-01",
			"event_type": "vitals",
			"timestamp": 1710000000000,
			"readings": {
				"spo2": 97,
				"heart_rate": 104,
				"respiratory_rate": 32,
				"temperature_c": 37.2,
				"signal_quality": {"spo2": 0.95},
			},
		}
	)

	with Session(engine, expire_on_commit=False) as db:
		device = crud.get_device(db, "esp32-demo-01")
		event = crud.get_telemetry_event(db, "esp32-event-001")

	assert device is not None
	assert device.device_type == DeviceType.SENSOR
	assert device.status == DeviceStatus.ACTIVE
	assert device.metadata_json["platform"] == "esp32"
	assert device.last_seen_at is not None
	assert event is not None
	assert event.readings["spo2"] == 97

	api_main._persist_telemetry(
		{
			"id": "esp32-event-001",
			"device_id": "esp32-demo-01",
			"timestamp": 1710000000000,
			"readings": {"spo2": 99},
		}
	)
	with Session(engine, expire_on_commit=False) as db:
		count = len(list(db.scalars(select(TelemetryEvent))))
	assert count == 1


def test_esp32_mqtt_telemetry_rejects_inactive_registered_device(tmp_path, monkeypatch):
	api_main, engine = _load_api_main(tmp_path, monkeypatch)

	with Session(engine, expire_on_commit=False) as db:
		crud.register_device(
			db,
			{
				"id": "esp32-disabled",
				"device_type": DeviceType.SENSOR,
				"status": DeviceStatus.REVOKED,
			},
		)
		db.commit()

	api_main._persist_telemetry(
		{
			"id": "esp32-revoked-event",
			"device_id": "esp32-disabled",
			"timestamp": 1710000001000,
			"readings": {"spo2": 98},
		}
	)

	with Session(engine, expire_on_commit=False) as db:
		device_count = len(list(db.scalars(select(Device))))
		event = crud.get_telemetry_event(db, "esp32-revoked-event")
	assert device_count == 1
	assert event is None
