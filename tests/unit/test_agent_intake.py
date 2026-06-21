from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np
import pytest

from backend.agents import agent_intake
from backend.agents.agent_intake import LoadedModel, ModelMetadata, run_intake
from backend.agents.pretriage_reference import (
	PreTriageRuleset,
	clear_reference_caches,
	load_growth_reference,
)
from backend.config import clear_settings_cache


@pytest.fixture(autouse=True)
def _clear_intake_state():
	clear_settings_cache()
	clear_reference_caches()
	agent_intake.clear_intake_caches()
	yield
	clear_settings_cache()
	clear_reference_caches()
	agent_intake.clear_intake_caches()


def _run(state, **updates):
	copy = dict(state)
	copy.update(updates)
	return run_intake(copy)


def test_spo2_emergency_boundary(sample_patient_state):
	at_boundary = _run(
		sample_patient_state,
		raw_vitals={"spo2": 90, "heart_rate": 100, "temperature_celsius": 37},
	)
	assert at_boundary["risk_level"] == "MEDIUM"

	below_boundary = _run(
		sample_patient_state,
		raw_vitals={"spo2": 89.9, "heart_rate": 100, "temperature_celsius": 37},
	)
	assert below_boundary["risk_level"] == "CRITICAL"
	assert below_boundary["emergency_escalate"] is True


def test_temperature_emergency_boundary(sample_patient_state):
	at_boundary = _run(
		sample_patient_state, raw_vitals={"temperature_celsius": 40}
	)
	assert at_boundary["risk_level"] == "MEDIUM"
	above_boundary = _run(
		sample_patient_state, raw_vitals={"temperature_celsius": 40.1}
	)
	assert above_boundary["risk_level"] == "CRITICAL"


@pytest.mark.parametrize(
	"checklist_key",
	["convulsions", "lethargic", "unconscious", "unable_drink", "vomiting"],
)
def test_general_danger_signs_override_model(sample_patient_state, checklist_key):
	result = _run(
		sample_patient_state,
		raw_vitals={},
		asha_checklist={checklist_key: True},
	)
	assert result["risk_level"] == "CRITICAL"
	assert result["risk_confidence"] == 1.0


@pytest.mark.parametrize(
	"checklist_key",
	["chest_indrawing", "edema", "wasting"],
)
def test_severe_checklist_rules(sample_patient_state, checklist_key):
	result = _run(
		sample_patient_state,
		raw_vitals={},
		asha_checklist={checklist_key: True},
	)
	assert result["risk_level"] == "HIGH"


@pytest.mark.parametrize(
	("age_months", "rate", "expected"),
	[
		(2, 50, "MEDIUM"),
		(2, 51, "HIGH"),
		(11, 51, "HIGH"),
		(12, 40, "MEDIUM"),
		(12, 41, "HIGH"),
		(59, 41, "HIGH"),
		(60, 100, "MEDIUM"),
	],
)
def test_age_dependent_respiratory_boundaries(
	sample_patient_state, age_months, rate, expected
):
	result = _run(
		sample_patient_state,
		age_months=age_months,
		raw_vitals={"respiratory_rate": rate},
	)
	assert result["risk_level"] == expected


def test_configurable_age_heart_rate_and_diarrhea_rules():
	ruleset = PreTriageRuleset.model_validate(
		{
			"schema_version": 1,
			"ruleset_version": "synthetic-rules",
			"status": "DRAFT",
			"sources": ["synthetic test fixture only"],
			"signal_quality": {
				"window_readings": 2,
				"window_seconds": 30,
				"spo2_cv_max": 0.03,
				"bounds": {},
			},
			"rules": [
				{
					"id": "synthetic-age-hr",
					"label": "synthetic",
					"risk": "HIGH",
					"conditions": [
						{"field": "age_months", "operator": "lte", "value": 12},
						{"field": "heart_rate", "operator": "gt", "value": 123},
					],
					"source": "synthetic test fixture only",
				},
				{
					"id": "synthetic-diarrhea",
					"label": "synthetic",
					"risk": "MEDIUM",
					"conditions": [
						{
							"field": "diarrhea_duration_days",
							"operator": "gte",
							"value": 4,
						}
					],
					"source": "synthetic test fixture only",
				},
			],
		}
	)
	matched = agent_intake._matched_rules(
		ruleset,
		{"age_months": 12, "heart_rate": 124, "diarrhea_duration_days": 4},
		{},
	)
	assert {rule.id for rule in matched} == {
		"synthetic-age-hr",
		"synthetic-diarrhea",
	}


def test_missing_sensors_are_not_replaced_with_zero(sample_patient_state):
	result = _run(sample_patient_state, raw_vitals={})
	assert result["risk_level"] == "MEDIUM"
	assert result["validated_vitals"]["spo2"] is None
	assert result["validated_vitals"]["heart_rate"] is None
	assert result["validated_vitals"]["temperature"] is None
	assert result["validated_vitals"]["respiratory_rate"] is None
	assert result["validated_vitals"]["weight_kg"] == 8.2
	assert result["derived_features"]["spo2"] is None
	assert result["derived_features"]["spo2_deficit"] is None
	assert result["signal_quality"]["spo2"]["status"] == "MISSING"


def test_unreliable_spo2_window_is_excluded(sample_patient_state):
	history = [
		{"timestamp_ms": index * 1000, "spo2": value}
		for index, value in enumerate([80, 99, 81, 100, 82, 99, 80, 100, 81, 99])
	]
	result = _run(
		sample_patient_state,
		raw_vitals={"spo2": 85, "history": history},
	)
	assert result["validated_vitals"]["spo2"] is None
	assert result["signal_quality"]["spo2"]["status"] == "UNRELIABLE"
	assert result["risk_level"] == "MEDIUM"


def test_short_window_delta_features(sample_patient_state):
	result = _run(
		sample_patient_state,
		raw_vitals={
			"spo2": 96,
			"heart_rate": 120,
			"history": [
				{"timestamp_ms": 0, "spo2": 99, "heart_rate": 100},
				{"timestamp_ms": 20_000, "spo2": 97, "heart_rate": 110},
				{"timestamp_ms": 35_000, "spo2": 96, "heart_rate": 120},
			],
		},
	)
	assert result["derived_features"]["delta_spo2"] == -1
	assert result["derived_features"]["delta_heart_rate"] == 10


def test_lms_weight_for_age_calculation_and_interpolation(tmp_path):
	path = tmp_path / "growth.json"
	path.write_text(
		json.dumps(
			{
				"schema_version": 1,
				"reference_version": "synthetic-lms-test",
				"source": "synthetic test fixture only",
				"status": "TEMPLATE",
				"rows": [
					{"sex": "female", "age_months": 0, "l": 1, "m": 4, "s": 0.25},
					{"sex": "female", "age_months": 2, "l": 1, "m": 6, "s": 0.25},
				],
			}
		),
		encoding="utf-8",
	)
	reference = load_growth_reference(path)
	assert reference.weight_for_age_zscore(
		sex="female", age_months=1, weight_kg=5
	) == pytest.approx(0)
	assert reference.weight_for_age_zscore(
		sex="male", age_months=1, weight_kg=5
	) is None


class _FakeBooster:
	def predict(self, _matrix, pred_contribs=False):
		if pred_contribs:
			return np.array([[0.1, -0.8, 0.3, 0.0]])
		return np.array([[0.1, 0.2, 0.3, 0.4]])


def test_calibrated_probabilities_and_shap_top_three(monkeypatch):
	monkeypatch.setattr(
		agent_intake,
		"xgb",
		SimpleNamespace(DMatrix=lambda values, feature_names: (values, feature_names)),
	)
	model = LoadedModel(
		booster=_FakeBooster(),
		metadata=ModelMetadata(
			model_version="synthetic-model",
			feature_order=["age_months", "spo2", "heart_rate"],
			classes=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
			calibration_temperature=2.0,
		),
	)
	risk, confidence, explanations, probabilities = agent_intake._model_prediction(
		model, {"age_months": 12, "spo2": None, "heart_rate": 100}
	)
	assert risk == "CRITICAL"
	assert 0 < confidence < 0.4
	assert len(explanations) == 3
	assert explanations[0]["feature"] == "spo2"
	assert sum(probabilities.values()) == pytest.approx(1)


def test_deterministic_emergency_overrides_lower_model(
	sample_patient_state, monkeypatch
):
	model = LoadedModel(
		booster=_FakeBooster(),
		metadata=ModelMetadata(
			model_version="synthetic-model",
			feature_order=["age_months", "spo2", "heart_rate"],
			classes=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
		),
	)
	monkeypatch.setattr(agent_intake, "_load_model", lambda: model)
	monkeypatch.setattr(
		agent_intake,
		"_model_prediction",
		lambda _model, _features: (
			"LOW",
			0.99,
			[{"feature": "spo2", "contribution": -1, "value": 85}],
			{"LOW": 0.99, "MEDIUM": 0.01, "HIGH": 0.0, "CRITICAL": 0.0},
		),
	)
	result = _run(sample_patient_state, raw_vitals={"spo2": 85})
	assert result["risk_level"] == "CRITICAL"


def test_model_failure_returns_medium_without_danger_rule(
	sample_patient_state, monkeypatch
):
	def _failure():
		raise ValueError("malformed model")

	monkeypatch.setattr(agent_intake, "_load_model", _failure)
	result = _run(sample_patient_state, raw_vitals={"spo2": 98})
	assert result["risk_level"] == "MEDIUM"
	assert result["classifier_status"] == "MODEL_FAILURE"
	assert result["errors"][-1]["stage"] == "pretriage_model"


def test_model_failure_does_not_suppress_danger_rule(
	sample_patient_state, monkeypatch
):
	monkeypatch.setattr(
		agent_intake, "_load_model", lambda: (_ for _ in ()).throw(ValueError())
	)
	result = _run(
		sample_patient_state,
		raw_vitals={"spo2": 98},
		asha_checklist={"convulsions": True},
	)
	assert result["risk_level"] == "CRITICAL"


def test_malformed_model_feature_count_is_rejected(tmp_path, monkeypatch):
	model_path = tmp_path / "model.json"
	metadata_path = tmp_path / "metadata.json"
	model_path.write_text("{}", encoding="utf-8")
	metadata_path.write_text(
		json.dumps(
			{
				"model_version": "synthetic",
				"feature_order": ["age_months", "spo2"],
				"classes": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
			}
		),
		encoding="utf-8",
	)
	config_path = tmp_path / "config.yaml"
	config_path.write_text(
		f"""
triage_model:
  path: {model_path}
  metadata_path: {metadata_path}
  rules_path: data/reference/pretriage_rules.json
  growth_reference_path: data/reference/who_weight_for_age_lms.json
""",
		encoding="utf-8",
	)

	class BadBooster:
		feature_names = None

		def load_model(self, _path):
			return None

		def num_features(self):
			return 3

	monkeypatch.setenv("AYUSHBOT_CONFIG", str(config_path))
	monkeypatch.setattr(agent_intake, "xgb", SimpleNamespace(Booster=BadBooster))
	clear_settings_cache()
	agent_intake.clear_intake_caches()
	with pytest.raises(ValueError, match="feature count"):
		agent_intake._load_model()


def test_ruleset_and_reference_versions_are_recorded(sample_patient_state):
	result = _run(sample_patient_state, raw_vitals={"spo2": 98})
	assert result["ruleset_version"] == "ayushbot-pretriage-draft-2026-06-15"
	assert result["growth_reference_version"] == "WHO-WFA-LMS-PENDING"
	assert result["model_version"] is None
	assert result["medical_review_required"] is True
