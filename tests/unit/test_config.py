from __future__ import annotations

from pathlib import Path

from backend.config import PROJECT_ROOT, load_settings


def test_load_settings_resolves_relative_paths_without_artifacts(tmp_path, monkeypatch):
	config_path = tmp_path / "config.yaml"
	config_path.write_text(
		"""
database:
  path: var/test.db
rag:
  index_dir: var/rag-index
fl:
  queue_dir: var/fl-queue
""",
		encoding="utf-8",
	)
	monkeypatch.setenv("AYUSHBOT_API_PORT", "9001")
	monkeypatch.setenv("AYUSHBOT_REDIS_ENABLED", "true")

	settings = load_settings(config_path)

	assert settings.api.port == 9001
	assert settings.redis.enabled is True
	assert settings.database.path == PROJECT_ROOT / "var" / "test.db"
	assert settings.database.path.parent.is_dir()
	assert settings.rag.index_dir.is_dir()
	assert settings.fl.queue_dir.is_dir()


def test_nested_environment_override(monkeypatch):
	monkeypatch.setenv("AYUSHBOT_RAG__CHUNK_SIZE", "128")
	settings = load_settings(create_dirs=False)
	assert settings.rag.chunk_size == 128


def test_missing_explicit_config_is_an_error(tmp_path):
	missing = tmp_path / "missing.yaml"
	try:
		load_settings(missing, create_dirs=False)
	except FileNotFoundError as exc:
		assert str(Path(missing)) in str(exc)
	else:
		raise AssertionError("Expected an explicit missing config path to fail")
