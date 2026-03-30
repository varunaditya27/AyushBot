# =============================================================================
# AyushBot Backend — FastAPI Application Entry Point
# =============================================================================
#
# PURPOSE:
#   Creates and configures the FastAPI application instance that serves as
#   the HTTP interface on the PHC gateway (Raspberry Pi 4). This is the
#   process that the Android app communicates with over the local Wi-Fi
#   network at the PHC.
#
# APPLICATION LIFECYCLE:
#
#   Startup (on_startup event):
#     1. Load configuration from config.yaml
#     2. Initialize the SQLite database connection (via db/session.py)
#     3. Load the XGBoost triage model (for Agent 1)
#     4. Load the RAG pipeline (FAISS index, BM25 index, bi-encoder, reranker)
#     5. Load the LLM model (Phi-3 Mini or Gemma-3 via llm/loader.py)
#     6. Load language models (IndicBERT, IndicTrans2 via Agent 5 dependencies)
#     7. Initialize the LangGraph orchestrator with all agents
#     8. Start the FL background scheduler (Agent 4)
#     9. Log total startup time and memory usage
#
#   Shutdown (on_shutdown event):
#     1. Flush any pending FL gradient updates to disk
#     2. Close the database connection pool
#     3. Unload models to free memory
#     4. Log shutdown confirmation
#
# ROUTE REGISTRATION:
#   The app registers the following routers:
#     - /api/v1/triage — Patient assessment endpoints (routes/triage.py)
#     - /api/v1/sync — Data sync endpoints for ASHA phones (routes/sync.py)
#     - /api/v1/health — Gateway health/status endpoints (routes/health.py)
#
# MIDDLEWARE STACK:
#   Applied in order (outermost first):
#     1. CORS middleware — Allow requests from the local Android app
#     2. Rate limiter — Prevent abuse (routes/middleware/rate_limiter.py)
#     3. Request logging — Structured JSON logging for every request
#     4. Error handler — Catch unhandled exceptions, return safe 500 responses
#
# SECURITY:
#   The API runs on the PHC's LOCAL network only (not exposed to the internet).
#   Security layers:
#     - HTTPS with self-signed certificates (generated during RPi setup)
#     - API key authentication (shared secret between Android app and gateway)
#     - Rate limiting to prevent accidental DoS from buggy app versions
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
import os
import threading
from dataclasses import dataclass
from typing import Any, Dict, Optional

import paho.mqtt.client as mqtt
import redis
import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import health, sync, telemetry, triage
from backend.api.middleware.rate_limiter import RateLimiterMiddleware
from backend.db.session import init_db

logger = logging.getLogger(__name__)


def _load_config() -> Dict[str, Any]:
	config_path = os.getenv("AYUSHBOT_CONFIG") or os.path.join(
		os.path.dirname(__file__), "..", "config.yaml"
	)
	config_path = os.path.abspath(config_path)
	if not os.path.exists(config_path):
		logger.warning("Config file not found at %s; using defaults", config_path)
		return {}
	try:
		with open(config_path, "r", encoding="utf-8") as handle:
			return yaml.safe_load(handle) or {}
	except Exception as exc:  # pragma: no cover
		logger.error("Failed to read config: %s", exc)
		return {}


@dataclass
class RedisSettings:
	url: str
	enabled: bool


def _redis_settings(config: Dict[str, Any]) -> RedisSettings:
	redis_cfg = config.get("redis", {}) if isinstance(config, dict) else {}
	url = os.getenv("AYUSHBOT_REDIS_URL", redis_cfg.get("url", "redis://localhost:6379/0"))
	enabled = str(os.getenv("AYUSHBOT_REDIS_ENABLED", redis_cfg.get("enabled", True))).lower() in {
		"1",
		"true",
		"yes",
		"y",
	}
	return RedisSettings(url=url, enabled=enabled)


@dataclass
class MqttSettings:
	host: str
	port: int
	username: Optional[str]
	password: Optional[str]
	topic: str


def _mqtt_settings(config: Dict[str, Any]) -> MqttSettings:
	mqtt_cfg = config.get("mqtt", {}) if isinstance(config, dict) else {}
	return MqttSettings(
		host=os.getenv("AYUSHBOT_MQTT_HOST", mqtt_cfg.get("host", "localhost")),
		port=int(os.getenv("AYUSHBOT_MQTT_PORT", mqtt_cfg.get("port", 1883))),
		username=os.getenv("AYUSHBOT_MQTT_USERNAME", mqtt_cfg.get("username")),
		password=os.getenv("AYUSHBOT_MQTT_PASSWORD", mqtt_cfg.get("password")),
		topic=os.getenv("AYUSHBOT_MQTT_TOPIC", mqtt_cfg.get("topic", "ayushbot/telemetry/#")),
	)


class RedisClient:
	def __init__(self, settings: RedisSettings) -> None:
		self.settings = settings
		self._client: Optional[redis.Redis] = None
		if settings.enabled:
			try:
				self._client = redis.Redis.from_url(settings.url, decode_responses=True)
				self._client.ping()
				logger.info("Connected to Redis at %s", settings.url)
			except Exception as exc:
				logger.error("Redis unavailable: %s", exc)
				self._client = None

	def push_telemetry(self, payload: Dict[str, Any]) -> None:
		if not self._client:
			logger.warning("Skipping telemetry push; Redis not available")
			return
		try:
			self._client.rpush("ayushbot:telemetry", json.dumps(payload))
		except Exception as exc:
			logger.error("Failed to push telemetry to Redis: %s", exc)


class MqttListener:
	def __init__(self, settings: MqttSettings, redis_client: RedisClient) -> None:
		self.settings = settings
		self.redis_client = redis_client
		self._client = mqtt.Client()
		self._thread: Optional[threading.Thread] = None
		self._stop_event = threading.Event()

		if settings.username:
			self._client.username_pw_set(settings.username, settings.password)
		self._client.on_connect = self._on_connect
		self._client.on_message = self._on_message
		self._client.on_disconnect = self._on_disconnect

	def start(self) -> None:
		self._stop_event.clear()
		self._thread = threading.Thread(target=self._run, daemon=True)
		self._thread.start()

	def stop(self) -> None:
		self._stop_event.set()
		try:
			self._client.disconnect()
		except Exception:
			pass
		if self._thread and self._thread.is_alive():
			self._thread.join(timeout=5)

	def _run(self) -> None:
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
			except Exception:
				pass

	def _on_connect(self, client, _userdata, _flags, rc) -> None:  # type: ignore[no-untyped-def]
		if rc != 0:
			logger.error("MQTT connect failed with code %s", rc)
			return
		client.subscribe(self.settings.topic)
		logger.info("MQTT subscribed to %s", self.settings.topic)

	def _on_disconnect(self, _client, _userdata, rc) -> None:  # type: ignore[no-untyped-def]
		if rc != 0:
			logger.warning("MQTT disconnected unexpectedly (%s)", rc)

	def _on_message(self, _client, _userdata, msg) -> None:  # type: ignore[no-untyped-def]
		try:
			payload = msg.payload.decode("utf-8")
			data = json.loads(payload) if payload else {"raw": ""}
		except Exception:
			data = {"raw": msg.payload.decode("utf-8", errors="ignore")}
		data["topic"] = msg.topic
		self.redis_client.push_telemetry(data)


def create_app() -> FastAPI:
	config = _load_config()
	api_cfg = config.get("api", {}) if isinstance(config, dict) else {}
	cors_origins = api_cfg.get("cors_origins", ["*"])

	app = FastAPI(title="AyushBot API", version="1.0.0")
	app.add_middleware(
		CORSMiddleware,
		allow_origins=cors_origins,
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	app.add_middleware(RateLimiterMiddleware)
	app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
	app.include_router(sync.router, prefix="/api/v1/sync", tags=["sync"])
	app.include_router(telemetry.router, prefix="/api/v1/telemetry", tags=["telemetry"])
	app.include_router(triage.router, prefix="/api/v1/triage", tags=["triage"])

	redis_client = RedisClient(_redis_settings(config))
	mqtt_listener = MqttListener(_mqtt_settings(config), redis_client)

	@app.on_event("startup")
	def _startup() -> None:
		init_db()
		mqtt_listener.start()
		app.state.redis_client = redis_client
		app.state.mqtt_listener = mqtt_listener
		logger.info("AyushBot API startup complete")

	@app.on_event("shutdown")
	def _shutdown() -> None:
		mqtt_listener.stop()
		logger.info("AyushBot API shutdown complete")

	return app


app = create_app()
