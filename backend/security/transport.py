"""Production transport-security validation."""

from __future__ import annotations

from pathlib import Path

from backend.agents.pretriage_reference import (
	load_growth_reference_with_policy,
	load_ruleset_with_policy,
)
from backend.config import Settings
from backend.security.auth import validate_auth_key_configuration


_PLACEHOLDER_VALUES = {
	"",
	"changeme",
	"change-me",
	"change_me",
	"example",
	"example-password",
	"password",
	"placeholder",
	"secret",
	"todo",
	"your-password",
	"your-secret",
}


def _require_file(path: Path | None, label: str, field_name: str) -> None:
	if path is None or not path.is_file():
		raise RuntimeError(
			f"Missing required {label}; configure {field_name} with a readable file "
			f"(current value: {path or 'not configured'})"
		)


def _reject_placeholder(value: str | None, field_name: str) -> None:
	if value is None:
		return
	normalized = value.strip().lower()
	if normalized in _PLACEHOLDER_VALUES or normalized.startswith(("your-", "replace-")):
		raise RuntimeError(
			f"Production configuration contains a placeholder credential in {field_name}"
		)


def validate_production_security(settings: Settings) -> None:
	if settings.environment.lower() != "production":
		return
	if not settings.api.cors_origins or "*" in settings.api.cors_origins:
		raise RuntimeError("Production CORS must contain explicit trusted origins")
	_require_file(settings.api.tls_cert_path, "API TLS certificate", "api.tls_cert_path")
	_require_file(settings.api.tls_key_path, "API TLS private key", "api.tls_key_path")
	try:
		validate_auth_key_configuration(settings.auth)
	except Exception as exc:
		raise RuntimeError(
			"Production JWT signing keys are not ready; configure auth.keys with "
			"auth.active_kid pointing to a key that has readable public_key_path and "
			"private_key_path"
		) from exc

	if not settings.mqtt.enabled or not settings.mqtt.tls_enabled:
		raise RuntimeError("Production MQTT must be enabled with TLS")
	if settings.mqtt.port != 8883:
		raise RuntimeError("Production MQTT must use the TLS listener on port 8883")
	_require_file(settings.mqtt.ca_cert_path, "MQTT CA certificate", "mqtt.ca_cert_path")
	_require_file(
		settings.mqtt.client_cert_path,
		"MQTT client certificate",
		"mqtt.client_cert_path",
	)
	_require_file(
		settings.mqtt.client_key_path,
		"MQTT client private key",
		"mqtt.client_key_path",
	)
	_reject_placeholder(settings.mqtt.username, "mqtt.username")
	_reject_placeholder(settings.mqtt.password, "mqtt.password")

	if settings.fl.enabled or settings.fl.training_enabled:
		raise RuntimeError(
			"Production FL training is incomplete and must remain disabled "
			"(fl.enabled=false, fl.training_enabled=false)"
		)

	if settings.triage_model.enabled:
		if settings.triage_model.allow_draft_rules:
			raise RuntimeError(
				"Production medically reviewed rules require "
				"triage_model.allow_draft_rules=false"
			)
		if not settings.triage_model.require_reviewed_rules:
			raise RuntimeError(
				"Production medically reviewed rules require "
				"triage_model.require_reviewed_rules=true"
			)
		_require_file(
			settings.triage_model.rules_path,
			"medically reviewed pre-triage rules",
			"triage_model.rules_path",
		)
		_require_file(
			settings.triage_model.growth_reference_path,
			"medically reviewed WHO weight-for-age reference",
			"triage_model.growth_reference_path",
		)
		load_ruleset_with_policy(
			settings.triage_model.rules_path,
			allow_draft_rules=settings.triage_model.allow_draft_rules,
			require_reviewed_rules=True,
		)
		load_growth_reference_with_policy(
			settings.triage_model.growth_reference_path,
			allow_draft_rules=settings.triage_model.allow_draft_rules,
			require_reviewed_rules=True,
		)
