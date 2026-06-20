from __future__ import annotations

import json

import pytest

from backend.agents.pretriage_reference import (
	clear_reference_caches,
	load_growth_reference_with_policy,
	load_ruleset_with_policy,
)
from backend.config import load_settings
from backend.security.transport import validate_production_security


@pytest.fixture(autouse=True)
def _clear_reference_cache():
	clear_reference_caches()
	yield
	clear_reference_caches()


def _rules(path, *, status: str, review_required: bool = True):
	path.write_text(
		json.dumps(
			{
				"schema_version": 1,
				"ruleset_version": f"synthetic-{status.lower()}",
				"status": status,
				"sources": ["synthetic test fixture only"],
				"signal_quality": {
					"window_readings": 2,
					"window_seconds": 30,
					"spo2_cv_max": 0.03,
					"bounds": {},
				},
				"rules": [
					{
						"id": "synthetic-rule",
						"label": "Synthetic rule",
						"risk": "MEDIUM",
						"enabled": True,
						"conditions": [
							{
								"field": "checklist.synthetic",
								"operator": "truthy",
								"value": None,
							}
						],
						"source": "synthetic test fixture only",
						"medical_review_required": review_required,
					}
				],
			}
		),
		encoding="utf-8",
	)


def _growth(path, *, status: str, rows: bool = True):
	path.write_text(
		json.dumps(
			{
				"schema_version": 1,
				"reference_version": f"synthetic-{status.lower()}",
				"source": "synthetic test fixture only",
				"status": status,
				"rows": (
					[
						{
							"sex": "female",
							"age_months": 0,
							"l": 1.0,
							"m": 3.2,
							"s": 0.1,
						}
					]
					if rows
					else []
				),
			}
		),
		encoding="utf-8",
	)


def test_draft_rules_allowed_in_development_policy(tmp_path):
	rules = tmp_path / "rules.json"
	growth = tmp_path / "growth.json"
	_rules(rules, status="DRAFT")
	_growth(growth, status="TEMPLATE", rows=False)

	assert (
		load_ruleset_with_policy(
			rules,
			allow_draft_rules=True,
			require_reviewed_rules=False,
		).status
		== "DRAFT"
	)
	assert (
		load_growth_reference_with_policy(
			growth,
			allow_draft_rules=True,
			require_reviewed_rules=False,
		).status
		== "TEMPLATE"
	)


def test_reviewed_rules_required_in_production_policy(tmp_path):
	rules = tmp_path / "rules.json"
	growth = tmp_path / "growth.json"
	_rules(rules, status="DRAFT")
	_growth(growth, status="TEMPLATE")

	with pytest.raises(RuntimeError, match="medically reviewed"):
		load_ruleset_with_policy(
			rules,
			allow_draft_rules=False,
			require_reviewed_rules=True,
		)
	with pytest.raises(RuntimeError, match="medically reviewed"):
		load_growth_reference_with_policy(
			growth,
			allow_draft_rules=False,
			require_reviewed_rules=True,
		)


def test_missing_and_invalid_rule_files_are_clear(tmp_path):
	missing = tmp_path / "missing.json"
	invalid = tmp_path / "invalid.json"
	invalid.write_text("[]", encoding="utf-8")

	with pytest.raises(FileNotFoundError, match="Reference file not found"):
		load_ruleset_with_policy(
			missing,
			allow_draft_rules=True,
			require_reviewed_rules=False,
		)
	with pytest.raises(ValueError, match="Reference root must be an object"):
		load_ruleset_with_policy(
			invalid,
			allow_draft_rules=True,
			require_reviewed_rules=False,
		)


def test_production_requires_review_flags_when_triage_enabled(tmp_path, monkeypatch):
	from backend.security import transport

	monkeypatch.setattr(
		transport, "validate_auth_key_configuration", lambda _settings: None
	)
	cert = tmp_path / "cert.pem"
	cert.write_text("synthetic certificate placeholder", encoding="utf-8")
	rules = tmp_path / "rules.json"
	growth = tmp_path / "growth.json"
	_rules(rules, status="DRAFT")
	_growth(growth, status="TEMPLATE")
	config = tmp_path / "production.yaml"
	config.write_text(
		f"""
environment: production
api:
  cors_origins: ["https://demo.local"]
  tls_cert_path: {cert}
  tls_key_path: {cert}
mqtt:
  enabled: true
  tls_enabled: true
  port: 8883
  ca_cert_path: {cert}
  client_cert_path: {cert}
  client_key_path: {cert}
triage_model:
  enabled: true
  rules_path: {rules}
  growth_reference_path: {growth}
  allow_draft_rules: true
  require_reviewed_rules: false
""",
		encoding="utf-8",
	)
	settings = load_settings(config, create_dirs=False)

	with pytest.raises(RuntimeError, match="allow_draft_rules=false"):
		validate_production_security(settings)
