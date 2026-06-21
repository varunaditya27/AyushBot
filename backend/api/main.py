# =============================================================================
# AyushBot Backend — FastAPI Application Entry Point
# =============================================================================
#
# PURPOSE:
#   Creates and configures the FastAPI application instance that serves as
#   the HTTP interface on the PHC gateway host. This Python process runs on
#   a laptop/desktop/server-class local host for development and showcase
#   deployments; ESP32 boards act as sensor clients and publish telemetry
#   into this service, they do not run the backend itself.
#
# APPLICATION LIFECYCLE:
#   Startup validates production security settings, runs Alembic migrations, and
#   starts optional Redis/MQTT telemetry workers only when enabled in config.
#   AI/RAG/FL dependencies are loaded lazily by their feature paths so the
#   showcase backend can start without optional model artifacts.
#
# ROUTE REGISTRATION:
#   The app registers the following routers:
#     - /api/v1/auth — Login, refresh, logout, and tablet provisioning
#     - /api/v1/triage — Patient assessment endpoints
#     - /api/v1/sync — Offline sync, manifests, downloads, and feedback
#     - /api/v1/telemetry — Durable telemetry ingestion
#     - /api/v1/health — Liveness/readiness/status endpoints
#
# MIDDLEWARE STACK:
#   Applied in order (outermost first):
#     1. CORS middleware — Allow requests from the local Android app
#     2. Rate limiter — Prevent abuse (routes/middleware/rate_limiter.py)
#     3. Route-level exception handling — Returns safe client-facing details
#
# SECURITY:
#   The API runs on the PHC's LOCAL network only (not exposed to the internet).
#   Security layers:
#     - HTTPS for production/showcase demos that enable TLS
#     - ES256 JWT authentication for protected endpoints
#     - Rate limiting to prevent accidental request floods from app bugs
#     - Input validation via Pydantic schemas on all request bodies
#
# DEPLOYMENT:
#   Run via Uvicorn ASGI server:
#     uvicorn backend.api.main:app --host 0.0.0.0 --port 8443 --ssl-keyfile ...
#   Or via the Docker container (see backend/Dockerfile).
#
# CONFIGURATION:
#   All API settings (host, port, cors_origins, rate_limit, etc.) are loaded
#   from the "api" section of config.yaml.
# =============================================================================

from __future__ import annotations

import json
import logging
import ssl
import threading
import uuid
from typing import Any, Dict, Optional, TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.middleware.rate_limiter import RateLimiterMiddleware
from backend.api.routes import auth, health, sync, telemetry, triage
from backend.config import MqttSettings, RedisSettings, get_settings
from backend.db import crud
from backend.db.models import DeviceStatus, DeviceType, now_ms
from backend.db.session import SessionLocal, init_db
from backend.security.transport import validate_production_security

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
	import redis


def _load_redis_module():
	try:
		import redis
	except ImportError as exc:
		raise RuntimeError(
			"Redis support is enabled but the 'redis' package is not installed. "
			"Install backend optional runtime dependencies or set redis.enabled=false."
		) from exc
	return redis


def _load_mqtt_module():
	try:
		import paho.mqtt.client as mqtt
	except ImportError as exc:
		raise RuntimeError(
			"MQTT support is enabled but the 'paho-mqtt' package is not installed. "
			"Install backend optional runtime dependencies or set mqtt.enabled=false."
		) from exc
	return mqtt


class RedisClient:
	def __init__(self, settings: RedisSettings) -> None:
		self.settings = settings
		self._client: Optional["redis.Redis"] = None
		self._consumer_thread: Optional[threading.Thread] = None
		self._stop_event = threading.Event()
		if settings.enabled:
			try:
				redis_module = _load_redis_module()
				self._client = redis_module.Redis.from_url(
					settings.url, decode_responses=True
				)
				self._client.ping()
				logger.info("Connected to Redis at %s", settings.url)
			except RuntimeError:
				raise
			except Exception as exc:
				raise RuntimeError(f"Redis is enabled but unavailable: {exc}") from exc

	def push_telemetry(self, payload: Dict[str, Any]) -> bool:
		if not self._client:
			logger.warning("Skipping telemetry push; Redis not available")
			return False
		try:
			self._client.rpush("ayushbot:telemetry", json.dumps(payload))
			return True
		except Exception as exc:
			logger.error("Failed to push telemetry to Redis: %s", exc)
			return False

	def health_check(self) -> tuple[bool, str]:
		if not self.settings.enabled:
			return True, "disabled"
		if not self._client:
			return False, "unavailable"
		try:
			self._client.ping()
		except Exception:
			logger.exception("Redis readiness check failed")
			return False, "unavailable"
		return True, "ready"

	def start_consumer(self) -> None:
		if not self._client or self._consumer_thread:
			return
		self._stop_event.clear()
		self._consumer_thread = threading.Thread(
			target=self._consume_telemetry, daemon=True
		)
		self._consumer_thread.start()

	def stop_consumer(self) -> None:
		self._stop_event.set()
		if self._consumer_thread and self._consumer_thread.is_alive():
			self._consumer_thread.join(timeout=5)

	def _consume_telemetry(self) -> None:
		while not self._stop_event.is_set() and self._client:
			try:
				item = self._client.blpop("ayushbot:telemetry", timeout=1)
				if item:
					_persist_telemetry(json.loads(item[1]))
			except Exception:
				logger.exception("Telemetry queue consumer failed")


class MqttListener:
	def __init__(self, settings: MqttSettings, redis_client: RedisClient) -> None:
		self.settings = settings
		self.redis_client = redis_client
		self._client: Any | None = None
		self._thread: Optional[threading.Thread] = None
		self._stop_event = threading.Event()
		self._connected = False

		if not settings.enabled:
			return

		mqtt = _load_mqtt_module()
		self._client = mqtt.Client()

		if settings.username:
			self._client.username_pw_set(settings.username, settings.password)
		if settings.tls_enabled:
			self._client.tls_set(
				ca_certs=str(settings.ca_cert_path),
				certfile=str(settings.client_cert_path),
				keyfile=str(settings.client_key_path),
				cert_reqs=ssl.CERT_REQUIRED,
				tls_version=ssl.PROTOCOL_TLS_CLIENT,
			)
		self._client.on_connect = self._on_connect
		self._client.on_message = self._on_message
		self._client.on_disconnect = self._on_disconnect

	def start(self) -> None:
		if not self.settings.enabled:
			logger.info("MQTT listener disabled")
			return
		self._stop_event.clear()
		self._thread = threading.Thread(target=self._run, daemon=True)
		self._thread.start()

	def stop(self) -> None:
		self._stop_event.set()
		try:
			if self._client is not None:
				self._client.disconnect()
		except Exception as exc:
			logger.debug("MQTT disconnect failed: %s", exc)
		if self._thread and self._thread.is_alive():
			self._thread.join(timeout=5)

	def _run(self) -> None:
		if self._client is None:
			return
		try:
			self._client.connect(self.settings.host, self.settings.port, keepalive=30)
			self._client.loop_start()
			while not self._stop_event.is_set():
				self._stop_event.wait(1.0)
		except Exception as exc:
			logger.error("MQTT listener error: %s", exc)
		finally:
			try:
				self._client.loop_stop()
			except Exception as exc:
				logger.debug("MQTT loop stop failed: %s", exc)

	def _on_connect(self, client, _userdata, _flags, rc) -> None:  # type: ignore[no-untyped-def]
		if rc != 0:
			logger.error("MQTT connect failed with code %s", rc)
			self._connected = False
			return
		self._connected = True
		client.subscribe(self.settings.topic)
		logger.info("MQTT subscribed to %s", self.settings.topic)

	def _on_disconnect(self, _client, _userdata, rc) -> None:  # type: ignore[no-untyped-def]
		self._connected = False
		if rc != 0:
			logger.warning("MQTT disconnected unexpectedly (%s)", rc)

	def health_check(self) -> tuple[bool, str]:
		if not self.settings.enabled:
			return True, "disabled"
		if self._client is None:
			return False, "unavailable"
		if self._connected:
			return True, "ready"
		if self._thread and self._thread.is_alive():
			return False, "connecting"
		return False, "unavailable"

	def _on_message(self, _client, _userdata, msg) -> None:  # type: ignore[no-untyped-def]
		try:
			payload = msg.payload.decode("utf-8")
			data = json.loads(payload) if payload else {"raw": ""}
		except Exception:
			data = {"raw": msg.payload.decode("utf-8", errors="ignore")}
		data["topic"] = msg.topic
		data.setdefault("id", str(uuid.uuid4()))
		data.setdefault("device_id", _device_id_from_topic(msg.topic))
		data.setdefault("event_type", "mqtt")
		data.setdefault("timestamp", int(__import__("time").time() * 1000))
		if "readings" not in data:
			data["readings"] = {
				key: value
				for key, value in data.items()
				if key not in {"id", "device_id", "case_id", "event_type", "timestamp"}
			}
		if not self.redis_client.push_telemetry(data):
			_persist_telemetry(data)


def _device_id_from_topic(topic: str) -> str:
	parts = [part for part in topic.split("/") if part]
	return parts[-1][:64] if parts else "mqtt-unknown"


def _persist_telemetry(payload: Dict[str, Any]) -> None:
	required = {"id", "device_id", "timestamp", "readings"}
	if not required <= payload.keys():
		logger.warning("Discarding malformed telemetry message")
		return
	with SessionLocal() as db:
		device_id = str(payload["device_id"])
		if crud.get_telemetry_event(db, str(payload["id"])):
			return
		device = crud.get_device(db, device_id)
		if device is None:
			device = crud.register_device(
				db,
				{
					"id": device_id,
					"device_type": DeviceType.SENSOR,
					"status": DeviceStatus.ACTIVE,
					"display_name": f"ESP32 sensor {device_id}",
					"last_seen_at": now_ms(),
					"metadata_json": {"source": "mqtt", "platform": "esp32"},
				},
			)
		elif device.status != DeviceStatus.ACTIVE:
			logger.warning("Discarding telemetry from inactive device %s", device_id)
			return
		else:
			device.last_seen_at = now_ms()
		try:
			crud.create_telemetry_event(
				db,
				{
					"id": str(payload["id"]),
					"device_id": device_id,
					"case_id": payload.get("case_id"),
					"event_type": str(payload.get("event_type", "mqtt")),
					"timestamp": int(payload["timestamp"]),
					"readings": payload["readings"],
				},
			)
			db.commit()
		except Exception:
			db.rollback()
			logger.exception("Failed to persist queued telemetry")


def create_app() -> FastAPI:
	settings = get_settings()

	app = FastAPI(title="AyushBot API", version="1.0.0")
	app.add_middleware(
		CORSMiddleware,
		allow_origins=settings.api.cors_origins,
		allow_credentials=True,
		allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
		allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
	)

	app.add_middleware(RateLimiterMiddleware)
	app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
	app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
	app.include_router(sync.router, prefix="/api/v1/sync", tags=["sync"])
	app.include_router(telemetry.router, prefix="/api/v1/telemetry", tags=["telemetry"])
	app.include_router(triage.router, prefix="/api/v1/triage", tags=["triage"])

	redis_client = RedisClient(settings.redis)
	mqtt_listener = MqttListener(settings.mqtt, redis_client)
	app.state.settings = settings
	app.state.redis_client = redis_client
	app.state.mqtt_listener = mqtt_listener

	@app.on_event("startup")
	def _startup() -> None:
		validate_production_security(settings)
		init_db()
		redis_client.start_consumer()
		mqtt_listener.start()
		logger.info("AyushBot API startup complete")

	@app.on_event("shutdown")
	def _shutdown() -> None:
		mqtt_listener.stop()
		redis_client.stop_consumer()
		logger.info("AyushBot API shutdown complete")

	return app


app = create_app()
