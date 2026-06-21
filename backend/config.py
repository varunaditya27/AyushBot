"""Typed configuration loading for the AyushBot backend."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "backend" / "config.yaml"


def _resolve_path(value: str | Path | None) -> Path | None:
	if value is None or str(value).strip() == "":
		return None
	path = Path(value).expanduser()
	return path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()


class SettingsModel(BaseModel):
	model_config = ConfigDict(extra="ignore")


class ApiSettings(SettingsModel):
	host: str = "127.0.0.1"
	port: int = Field(default=8000, ge=1, le=65535)
	cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost"])
	rate_limit_max_tokens: int = Field(default=20, ge=1)
	rate_limit_refill_rate: float = Field(default=5.0, gt=0)
	tls_cert_path: Path | None = None
	tls_key_path: Path | None = None

	_paths = field_validator("tls_cert_path", "tls_key_path", mode="before")(_resolve_path)


class DatabaseSettings(SettingsModel):
	path: Path = PROJECT_ROOT / "var" / "ayushbot.db"
	wal_mode: bool = True
	journal_size_limit_mb: int = Field(default=50, ge=1)

	_path = field_validator("path", mode="before")(_resolve_path)


class RedisSettings(SettingsModel):
	enabled: bool = False
	url: str = "redis://127.0.0.1:6379/0"


class MqttSettings(SettingsModel):
	enabled: bool = False
	host: str = "127.0.0.1"
	port: int = Field(default=1883, ge=1, le=65535)
	topic: str = "ayushbot/telemetry/#"
	username: str | None = None
	password: str | None = None
	tls_enabled: bool = False
	ca_cert_path: Path | None = None
	client_cert_path: Path | None = None
	client_key_path: Path | None = None

	_paths = field_validator(
		"ca_cert_path", "client_cert_path", "client_key_path", mode="before"
	)(_resolve_path)


class TriageModelSettings(SettingsModel):
	enabled: bool = True
	path: Path = PROJECT_ROOT / "models" / "triage_xgb.json"
	metadata_path: Path = PROJECT_ROOT / "models" / "triage_xgb.metadata.json"
	rules_path: Path = PROJECT_ROOT / "data" / "reference" / "pretriage_rules.json"
	growth_reference_path: Path = (
		PROJECT_ROOT / "data" / "reference" / "who_weight_for_age_lms.json"
	)
	allow_draft_rules: bool = True
	require_reviewed_rules: bool = False

	_paths = field_validator(
		"path",
		"metadata_path",
		"rules_path",
		"growth_reference_path",
		mode="before",
	)(_resolve_path)


class RagSettings(SettingsModel):
	enabled: bool = False
	corpus_dir: Path = PROJECT_ROOT / "data" / "corpus" / "cleaned_text"
	index_dir: Path = PROJECT_ROOT / "backend" / "rag" / "index"
	model_dir: Path = PROJECT_ROOT / "models" / "rag" / "biencoder"
	embedding_model_id: str = "local-onnx-biencoder"
	chunk_size: int = Field(default=300, ge=1)
	chunk_overlap: int = Field(default=50, ge=0)
	dense_top_k: int = Field(default=100, ge=1)
	sparse_top_k: int = Field(default=100, ge=1)
	retriever_top_k_fused: int = Field(default=20, ge=1)
	reranker_min_score: float = 0.3
	rrf_k: int = Field(default=60, ge=1)
	faiss_use_hnsw: bool = True
	faiss_hnsw_m: int = Field(default=32, ge=1)
	faiss_ef_construction: int = Field(default=200, ge=1)
	faiss_ef_search: int = Field(default=128, ge=1)
	max_length: int = Field(default=256, ge=1)
	intra_op_threads: int = Field(default=1, ge=1)
	inter_op_threads: int = Field(default=1, ge=1)

	_paths = field_validator("corpus_dir", "index_dir", "model_dir", mode="before")(_resolve_path)


class ReferralSettings(SettingsModel):
	max_search_radius_km: float = Field(default=50.0, gt=0)
	allow_out_of_radius_for_emergency: bool = True


class LanguageSettings(SettingsModel):
	provider: Literal["noop"] = "noop"
	enabled_languages: list[str] = Field(default_factory=lambda: ["en"])
	default_language: str = "en"
	require_human_review_below_confidence: float = Field(default=0.9, ge=0, le=1)


class LlmSettings(SettingsModel):
	model_path: Path = PROJECT_ROOT / "models" / "llm" / "model.gguf"
	context_length: int = Field(default=2048, ge=128, le=2048)
	max_tokens: int = Field(default=300, ge=1)
	temperature: float = Field(default=0.1, ge=0)
	top_p: float = Field(default=0.9, gt=0, le=1)
	n_threads: int = Field(default=2, ge=1)
	n_gpu_layers: int = Field(default=0, ge=0)

	_path = field_validator("model_path", mode="before")(_resolve_path)


class FlSettings(SettingsModel):
	enabled: bool = False
	training_enabled: bool = False
	update_representation: Literal["not_implemented"] = "not_implemented"
	server_address: str = "127.0.0.1:8080"
	model_path: Path = PROJECT_ROOT / "models" / "triage_xgb.json"
	train_data_path: Path = PROJECT_ROOT / "var" / "fl_train.npz"
	eval_data_path: Path = PROJECT_ROOT / "var" / "fl_eval.npz"
	queue_dir: Path = PROJECT_ROOT / "var" / "fl_queue"
	local_epochs: int = Field(default=3, ge=1)
	learning_rate: float = Field(default=0.01, gt=0)
	min_batch_size: int = Field(default=10, ge=1)
	dp_epsilon: float = Field(default=1.0, gt=0)
	dp_delta: float = Field(default=1e-6, gt=0, lt=1)
	dp_max_grad_norm: float = Field(default=1.0, gt=0)

	_paths = field_validator(
		"model_path", "train_data_path", "eval_data_path", "queue_dir", mode="before"
	)(_resolve_path)


class JwtKeySettings(SettingsModel):
	kid: str
	public_key_path: Path
	private_key_path: Path | None = None
	active: bool = True

	_paths = field_validator(
		"public_key_path", "private_key_path", mode="before"
	)(_resolve_path)


class AuthSettings(SettingsModel):
	issuer: str = "ayushbot-phc-gateway"
	audience: str = "ayushbot-tablet"
	access_token_minutes: int = Field(default=15, ge=1, le=1440)
	refresh_token_days: int = Field(default=7, ge=1, le=90)
	active_kid: str = "gateway-1"
	keys: list[JwtKeySettings] = Field(default_factory=list)
	jwt_private_key_path: Path | None = None
	jwt_public_key_path: Path | None = None

	_paths = field_validator(
		"jwt_private_key_path", "jwt_public_key_path", mode="before"
	)(_resolve_path)


class SyncSettings(SettingsModel):
	resource_dir: Path = PROJECT_ROOT / "var" / "sync_resources"
	idempotency_ttl_hours: int = Field(default=72, ge=1, le=720)
	manifest_ttl_minutes: int = Field(default=15, ge=1, le=1440)

	_path = field_validator("resource_dir", mode="before")(_resolve_path)


class Settings(SettingsModel):
	environment: Literal["development", "test", "production"] = "development"
	api: ApiSettings = Field(default_factory=ApiSettings)
	database: DatabaseSettings = Field(default_factory=DatabaseSettings)
	redis: RedisSettings = Field(default_factory=RedisSettings)
	mqtt: MqttSettings = Field(default_factory=MqttSettings)
	triage_model: TriageModelSettings = Field(default_factory=TriageModelSettings)
	rag: RagSettings = Field(default_factory=RagSettings)
	referral: ReferralSettings = Field(default_factory=ReferralSettings)
	language: LanguageSettings = Field(default_factory=LanguageSettings)
	llm: LlmSettings = Field(default_factory=LlmSettings)
	fl: FlSettings = Field(default_factory=FlSettings)
	auth: AuthSettings = Field(default_factory=AuthSettings)
	sync: SyncSettings = Field(default_factory=SyncSettings)
	road_graph_path: Path | None = None

	_road_graph_path = field_validator("road_graph_path", mode="before")(_resolve_path)

	def ensure_directories(self) -> None:
		for directory in (
			self.database.path.parent,
			self.rag.index_dir,
			self.fl.queue_dir,
			self.fl.train_data_path.parent,
			self.sync.resource_dir,
		):
			directory.mkdir(parents=True, exist_ok=True)


ENV_ALIASES: dict[str, tuple[str, ...]] = {
	"AYUSHBOT_ENVIRONMENT": ("environment",),
	"AYUSHBOT_API_HOST": ("api", "host"),
	"AYUSHBOT_API_PORT": ("api", "port"),
	"AYUSHBOT_DB_PATH": ("database", "path"),
	"AYUSHBOT_DB_WAL_MODE": ("database", "wal_mode"),
	"AYUSHBOT_DB_JOURNAL_LIMIT_MB": ("database", "journal_size_limit_mb"),
	"AYUSHBOT_REDIS_ENABLED": ("redis", "enabled"),
	"AYUSHBOT_REDIS_URL": ("redis", "url"),
	"AYUSHBOT_MQTT_ENABLED": ("mqtt", "enabled"),
	"AYUSHBOT_MQTT_HOST": ("mqtt", "host"),
	"AYUSHBOT_MQTT_PORT": ("mqtt", "port"),
	"AYUSHBOT_MQTT_TOPIC": ("mqtt", "topic"),
	"AYUSHBOT_MQTT_USERNAME": ("mqtt", "username"),
	"AYUSHBOT_MQTT_PASSWORD": ("mqtt", "password"),
	"AYUSHBOT_MQTT_TLS_ENABLED": ("mqtt", "tls_enabled"),
	"AYUSHBOT_MQTT_CA_CERT_PATH": ("mqtt", "ca_cert_path"),
	"AYUSHBOT_MQTT_CLIENT_CERT_PATH": ("mqtt", "client_cert_path"),
	"AYUSHBOT_MQTT_CLIENT_KEY_PATH": ("mqtt", "client_key_path"),
	"AYUSHBOT_SYNC_RESOURCE_DIR": ("sync", "resource_dir"),
	"AYUSHBOT_XGB_MODEL_PATH": ("triage_model", "path"),
	"AYUSHBOT_XGB_METADATA_PATH": ("triage_model", "metadata_path"),
	"AYUSHBOT_PRETRIAGE_RULES_PATH": ("triage_model", "rules_path"),
	"AYUSHBOT_PRETRIAGE_ENABLED": ("triage_model", "enabled"),
	"AYUSHBOT_ALLOW_DRAFT_RULES": ("triage_model", "allow_draft_rules"),
	"AYUSHBOT_REQUIRE_REVIEWED_RULES": ("triage_model", "require_reviewed_rules"),
	"AYUSHBOT_WHO_WAZ_REFERENCE_PATH": (
		"triage_model",
		"growth_reference_path",
	),
	"AYUSHBOT_RAG_INDEX_DIR": ("rag", "index_dir"),
	"AYUSHBOT_RAG_MODEL_DIR": ("rag", "model_dir"),
	"AYUSHBOT_RAG_ENABLED": ("rag", "enabled"),
	"AYUSHBOT_RAG_EMBEDDING_MODEL_ID": ("rag", "embedding_model_id"),
	"AYUSHBOT_RAG_DENSE_TOP_K": ("rag", "dense_top_k"),
	"AYUSHBOT_RAG_SPARSE_TOP_K": ("rag", "sparse_top_k"),
	"AYUSHBOT_RAG_TOP_K": ("rag", "retriever_top_k_fused"),
	"AYUSHBOT_RAG_MIN_SCORE": ("rag", "reranker_min_score"),
	"AYUSHBOT_RAG_RRF_K": ("rag", "rrf_k"),
	"AYUSHBOT_RAG_FAISS_USE_HNSW": ("rag", "faiss_use_hnsw"),
	"AYUSHBOT_RAG_FAISS_HNSW_M": ("rag", "faiss_hnsw_m"),
	"AYUSHBOT_RAG_FAISS_EF_CONSTRUCTION": ("rag", "faiss_ef_construction"),
	"AYUSHBOT_RAG_FAISS_EF_SEARCH": ("rag", "faiss_ef_search"),
	"AYUSHBOT_REFERRAL_MAX_RADIUS_KM": ("referral", "max_search_radius_km"),
	"AYUSHBOT_REFERRAL_ALLOW_OUT_OF_RADIUS_EMERGENCY": (
		"referral",
		"allow_out_of_radius_for_emergency",
	),
	"AYUSHBOT_LANGUAGE_PROVIDER": ("language", "provider"),
	"AYUSHBOT_LANGUAGE_ENABLED_LANGUAGES": ("language", "enabled_languages"),
	"AYUSHBOT_LANGUAGE_DEFAULT": ("language", "default_language"),
	"AYUSHBOT_LANGUAGE_REVIEW_CONFIDENCE": (
		"language",
		"require_human_review_below_confidence",
	),
	"AYUSHBOT_LLM_MODEL_PATH": ("llm", "model_path"),
	"AYUSHBOT_LLM_CONTEXT": ("llm", "context_length"),
	"AYUSHBOT_LLM_MAX_TOKENS": ("llm", "max_tokens"),
	"AYUSHBOT_LLM_TEMPERATURE": ("llm", "temperature"),
	"AYUSHBOT_LLM_TOP_P": ("llm", "top_p"),
	"AYUSHBOT_LLM_THREADS": ("llm", "n_threads"),
	"AYUSHBOT_LLM_GPU_LAYERS": ("llm", "n_gpu_layers"),
	"AYUSHBOT_FL_SERVER": ("fl", "server_address"),
	"AYUSHBOT_FL_ENABLED": ("fl", "enabled"),
	"AYUSHBOT_FL_TRAINING_ENABLED": ("fl", "training_enabled"),
	"AYUSHBOT_FL_UPDATE_REPRESENTATION": ("fl", "update_representation"),
	"AYUSHBOT_FL_TRAIN_DATA": ("fl", "train_data_path"),
	"AYUSHBOT_FL_EVAL_DATA": ("fl", "eval_data_path"),
	"AYUSHBOT_ROAD_GRAPH": ("road_graph_path",),
	"AYUSHBOT_JWT_PRIVATE_KEY_PATH": ("auth", "jwt_private_key_path"),
	"AYUSHBOT_JWT_PUBLIC_KEY_PATH": ("auth", "jwt_public_key_path"),
	"AYUSHBOT_JWT_ISSUER": ("auth", "issuer"),
	"AYUSHBOT_JWT_AUDIENCE": ("auth", "audience"),
	"AYUSHBOT_JWT_ACTIVE_KID": ("auth", "active_kid"),
	"AYUSHBOT_API_TLS_CERT_PATH": ("api", "tls_cert_path"),
	"AYUSHBOT_API_TLS_KEY_PATH": ("api", "tls_key_path"),
}


def _parse_env_value(value: str) -> Any:
	text = value.strip()
	if text == "":
		return None
	try:
		return json.loads(text)
	except json.JSONDecodeError:
		return text


def _set_nested(data: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
	target = data
	for key in path[:-1]:
		child = target.setdefault(key, {})
		if not isinstance(child, dict):
			child = {}
			target[key] = child
		target = child
	target[path[-1]] = value


def _apply_environment(data: dict[str, Any]) -> None:
	for name, path in ENV_ALIASES.items():
		if name in os.environ:
			_set_nested(data, path, _parse_env_value(os.environ[name]))

	prefix = "AYUSHBOT_"
	for name, value in os.environ.items():
		if not name.startswith(prefix) or "__" not in name:
			continue
		path = tuple(part.lower() for part in name[len(prefix) :].split("__") if part)
		if path:
			_set_nested(data, path, _parse_env_value(value))


def load_settings(config_path: str | Path | None = None, *, create_dirs: bool = True) -> Settings:
	path_value = config_path or os.getenv("AYUSHBOT_CONFIG") or DEFAULT_CONFIG_PATH
	path = _resolve_path(path_value)
	data: dict[str, Any] = {}
	if path and path.exists():
		loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
		if loaded is not None and not isinstance(loaded, dict):
			raise ValueError(f"Configuration root must be a mapping: {path}")
		data = loaded or {}
	elif config_path or os.getenv("AYUSHBOT_CONFIG"):
		raise FileNotFoundError(f"Configuration file not found: {path}")

	_apply_environment(data)
	try:
		settings = Settings.model_validate(data)
	except ValidationError as exc:
		raise ValueError(f"Invalid AyushBot configuration: {exc}") from exc
	if create_dirs:
		settings.ensure_directories()
	return settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
	return load_settings()


def clear_settings_cache() -> None:
	get_settings.cache_clear()
