from __future__ import annotations

import pytest

from backend.config import load_settings
from backend.security.transport import validate_production_security


def test_environment_can_be_overridden(monkeypatch):
	monkeypatch.setenv("AYUSHBOT_ENVIRONMENT", "test")

	settings = load_settings(create_dirs=False)

	assert settings.environment == "test"


def test_invalid_environment_is_rejected(tmp_path):
	config = tmp_path / "config.yaml"
	config.write_text("environment: staging\n", encoding="utf-8")

	with pytest.raises(ValueError, match="environment"):
		load_settings(config, create_dirs=False)


def test_production_validation_names_missing_tls_field(tmp_path):
	config = tmp_path / "config.yaml"
	config.write_text(
		"""
environment: production
api:
  cors_origins: ["https://phc.example.org"]
""",
		encoding="utf-8",
	)
	settings = load_settings(config, create_dirs=False)

	with pytest.raises(RuntimeError, match="api.tls_cert_path"):
		validate_production_security(settings)


def test_production_validation_names_missing_jwt_key_source(tmp_path):
	cert = tmp_path / "cert.pem"
	cert.write_text("certificate placeholder for path validation", encoding="utf-8")
	config = tmp_path / "config.yaml"
	config.write_text(
		f"""
environment: production
api:
  cors_origins: ["https://phc.example.org"]
  tls_cert_path: {cert}
  tls_key_path: {cert}
""",
		encoding="utf-8",
	)
	settings = load_settings(config, create_dirs=False)

	with pytest.raises(RuntimeError, match="auth.keys"):
		validate_production_security(settings)


def test_production_validation_rejects_placeholder_mqtt_credentials(
	tmp_path, monkeypatch
):
	from backend.security import transport

	monkeypatch.setattr(
		transport, "validate_auth_key_configuration", lambda _settings: None
	)
	cert = tmp_path / "cert.pem"
	cert.write_text("certificate placeholder for path validation", encoding="utf-8")
	rules = tmp_path / "rules.json"
	rules.write_text(
		"""
{
  "schema_version": 1,
  "ruleset_version": "reviewed-test",
  "status": "MEDICALLY_REVIEWED",
  "sources": ["synthetic-test"],
  "signal_quality": {
    "window_readings": 2,
    "window_seconds": 30,
    "spo2_cv_max": 0.03,
    "bounds": {}
  },
  "rules": []
}
""",
		encoding="utf-8",
	)
	growth = tmp_path / "growth.json"
	growth.write_text(
		"""
{
  "schema_version": 1,
  "reference_version": "reviewed-test",
  "source": "synthetic-test",
  "status": "MEDICALLY_REVIEWED",
  "rows": [
    {"sex": "male", "age_months": 0, "l": 1.0, "m": 3.3, "s": 0.1}
  ]
}
""",
		encoding="utf-8",
	)
	config = tmp_path / "config.yaml"
	config.write_text(
		f"""
environment: production
api:
  cors_origins: ["https://phc.example.org"]
  tls_cert_path: {cert}
  tls_key_path: {cert}
mqtt:
  enabled: true
  tls_enabled: true
  port: 8883
  username: gateway
  password: changeme
  ca_cert_path: {cert}
  client_cert_path: {cert}
  client_key_path: {cert}
triage_model:
  rules_path: {rules}
  growth_reference_path: {growth}
""",
		encoding="utf-8",
	)
	settings = load_settings(config, create_dirs=False)

	with pytest.raises(RuntimeError, match="mqtt.password"):
		validate_production_security(settings)
