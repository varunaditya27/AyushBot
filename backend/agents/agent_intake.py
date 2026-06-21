"""Agent 1: deterministic rules plus validated XGBoost pre-triage."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

try:
	import xgboost as xgb
except ImportError:  # Optional model-backed classifier.
	xgb = None  # type: ignore[assignment]

from backend.agents.pretriage_reference import (
	ClinicalRule,
	PreTriageRuleset,
	load_growth_reference_with_policy,
	load_ruleset_with_policy,
)
from backend.agents.state import PatientState, add_pipeline_error
from backend.config import get_settings

logger = logging.getLogger(__name__)
RISK_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


class ModelMetadata(BaseModel):
	model_config = ConfigDict(extra="forbid")

	model_version: str
	feature_order: list[str] = Field(min_length=1)
	classes: list[str] = Field(min_length=4, max_length=4)
	output_type: str = "probabilities"
	calibration_temperature: float = Field(default=1.0, gt=0)


@dataclass(frozen=True)
class LoadedModel:
	booster: Any
	metadata: ModelMetadata


def _load_metadata(path: Path) -> ModelMetadata:
	if not path.is_file():
		raise FileNotFoundError(f"Model metadata not found: {path}")
	return ModelMetadata.model_validate_json(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_model() -> LoadedModel | None:
	settings = get_settings().triage_model
	if xgb is None:
		return None
	if not settings.path.is_file() or not settings.metadata_path.is_file():
		return None
	metadata = _load_metadata(settings.metadata_path)
	booster = xgb.Booster()
	booster.load_model(settings.path)
	if booster.num_features() != len(metadata.feature_order):
		raise ValueError("Model feature count does not match metadata feature_order")
	if booster.feature_names and booster.feature_names != metadata.feature_order:
		raise ValueError("Model feature names do not match metadata feature_order")
	if metadata.classes != ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
		raise ValueError("Model classes must be LOW, MEDIUM, HIGH, CRITICAL")
	return LoadedModel(booster=booster, metadata=metadata)


def clear_intake_caches() -> None:
	_load_model.cache_clear()


def _extract_vitals(state: PatientState) -> dict[str, float | None]:
	raw = state.get("raw_vitals", {})
	weight = state.get("weight_kg")
	if weight is None and raw.get("weight_grams") is not None:
		weight = float(raw["weight_grams"]) / 1000
	return {
		"spo2": raw.get("spo2"),
		"heart_rate": raw.get("heart_rate"),
		"temperature": raw.get("temperature_celsius"),
		"respiratory_rate": raw.get("respiratory_rate"),
		"weight_kg": weight,
	}


def _history(state: PatientState) -> list[dict[str, Any]]:
	raw = state.get("raw_vitals", {})
	history = raw.get("history") or []
	return [item for item in history if isinstance(item, dict)]


def _coefficient_of_variation(values: list[float]) -> float | None:
	if len(values) < 2:
		return None
	mean = float(np.mean(values))
	if mean == 0:
		return None
	return float(np.std(values, ddof=0) / abs(mean))


def _validate_vitals(
	vitals: dict[str, float | None],
	state: PatientState,
	ruleset: PreTriageRuleset,
) -> tuple[dict[str, float | None], dict[str, Any], dict[str, float | None]]:
	validated: dict[str, float | None] = {}
	flags: dict[str, Any] = {}
	for name, value in vitals.items():
		bounds = ruleset.signal_quality.bounds.get(name)
		if value is None:
			validated[name] = None
			flags[name] = {"status": "MISSING", "reason": "not_provided"}
			continue
		numeric = float(value)
		if (
			not math.isfinite(numeric)
			or (bounds and bounds.minimum is not None and numeric < bounds.minimum)
			or (bounds and bounds.maximum is not None and numeric > bounds.maximum)
		):
			validated[name] = None
			flags[name] = {"status": "INVALID", "reason": "outside_configured_bounds"}
		else:
			validated[name] = numeric
			flags[name] = {"status": "VALID"}

	history = _history(state)
	window = history[-ruleset.signal_quality.window_readings :]
	spo2_values = [
		float(item["spo2"])
		for item in window
		if item.get("spo2") is not None
	]
	spo2_cv = _coefficient_of_variation(spo2_values)
	if spo2_cv is not None and spo2_cv > ruleset.signal_quality.spo2_cv_max:
		validated["spo2"] = None
		flags["spo2"] = {
			"status": "UNRELIABLE",
			"reason": "coefficient_of_variation",
			"value": spo2_cv,
		}

	reported_quality = state.get("raw_vitals", {}).get("signal_quality", {})
	for sensor, score in reported_quality.items():
		if (
			ruleset.signal_quality.min_quality_score is not None
			and isinstance(score, (int, float))
			and score < ruleset.signal_quality.min_quality_score
			and sensor in validated
		):
			validated[sensor] = None
			flags[sensor] = {
				"status": "UNRELIABLE",
				"reason": "reported_quality",
				"value": float(score),
			}

	deltas: dict[str, float | None] = {"delta_spo2": None, "delta_heart_rate": None}
	for field, output in (("spo2", "delta_spo2"), ("heart_rate", "delta_heart_rate")):
		points = [
			(float(item["timestamp_ms"]), float(item[field]))
			for item in history
			if item.get("timestamp_ms") is not None and item.get(field) is not None
		]
		if len(points) >= 2:
			last_time, last_value = points[-1]
			cutoff = last_time - ruleset.signal_quality.window_seconds * 1000
			first = next((point for point in points if point[0] >= cutoff), points[-2])
			deltas[output] = last_value - first[1]
	deltas["spo2_cv"] = spo2_cv
	return validated, flags, deltas


def _checklist_value(checklist: dict[str, Any], field: str) -> Any:
	aliases = {
		"unable_to_feed": ("unable_to_feed", "unable_drink", "unable_to_drink"),
		"altered_consciousness": (
			"altered_consciousness",
			"lethargic",
			"unconscious",
		),
		"vomiting_everything": ("vomiting_everything", "vomiting"),
		"bilateral_oedema": ("bilateral_oedema", "bilateral_edema", "edema"),
		"severe_wasting": ("severe_wasting", "wasting"),
	}
	for key in aliases.get(field, (field,)):
		if key in checklist:
			return checklist[key]
	return None


def _condition_value(
	field: str, features: dict[str, Any], checklist: dict[str, Any]
) -> Any:
	if field.startswith("checklist."):
		return _checklist_value(checklist, field.removeprefix("checklist."))
	return features.get(field)


def _condition_matches(value: Any, operator: str, expected: Any) -> bool:
	if value is None:
		return False
	if operator == "truthy":
		return value is True
	if operator == "eq":
		return value == expected
	if not isinstance(value, (int, float)) or not isinstance(expected, (int, float)):
		return False
	return {
		"lt": value < expected,
		"lte": value <= expected,
		"gt": value > expected,
		"gte": value >= expected,
	}[operator]


def _matched_rules(
	ruleset: PreTriageRuleset,
	features: dict[str, Any],
	checklist: dict[str, Any],
) -> list[ClinicalRule]:
	return [
		rule
		for rule in ruleset.rules
		if rule.enabled
		and all(
			_condition_matches(
				_condition_value(condition.field, features, checklist),
				condition.operator,
				condition.value,
			)
			for condition in rule.conditions
		)
	]


def _calibrate_probabilities(values: np.ndarray, temperature: float) -> np.ndarray:
	probabilities = np.asarray(values, dtype=np.float64)
	probabilities = np.clip(probabilities, 1e-12, 1)
	logits = np.log(probabilities) / temperature
	logits -= np.max(logits)
	exp_values = np.exp(logits)
	return exp_values / np.sum(exp_values)


def _model_prediction(
	model: LoadedModel, features: dict[str, Any]
) -> tuple[str, float, list[dict[str, Any]], dict[str, float]]:
	vector = np.array(
		[
			np.nan if features.get(name) is None else float(features[name])
			for name in model.metadata.feature_order
		],
		dtype=np.float32,
	).reshape(1, -1)
	dmatrix = xgb.DMatrix(vector, feature_names=model.metadata.feature_order)
	raw = np.asarray(model.booster.predict(dmatrix))
	row = raw if raw.ndim == 1 else raw[0]
	if model.metadata.output_type == "logits":
		row = np.exp(row - np.max(row))
		row = row / np.sum(row)
	if len(row) != len(model.metadata.classes) or not np.all(np.isfinite(row)):
		raise ValueError("Model returned malformed probabilities")
	probabilities = _calibrate_probabilities(
		row, model.metadata.calibration_temperature
	)
	index = int(np.argmax(probabilities))
	probability_map = {
		label: float(probabilities[position])
		for position, label in enumerate(model.metadata.classes)
	}

	explanations: list[dict[str, Any]] = []
	try:
		contributions = np.asarray(
			model.booster.predict(dmatrix, pred_contribs=True)
		)
		if contributions.ndim == 3:
			class_values = contributions[0, index, :-1]
		elif contributions.ndim == 2:
			class_values = contributions[0, :-1]
		else:
			raise ValueError("Unsupported SHAP contribution shape")
		ranked = np.argsort(np.abs(class_values))[::-1][:3]
		explanations = [
			{
				"feature": model.metadata.feature_order[position],
				"contribution": float(class_values[position]),
				"value": features.get(model.metadata.feature_order[position]),
			}
			for position in ranked
		]
	except Exception:
		logger.warning("SHAP contributions unavailable", exc_info=True)
	return (
		model.metadata.classes[index],
		float(probabilities[index]),
		explanations,
		probability_map,
	)


def run_intake(state: PatientState) -> PatientState:
	app_settings = get_settings()
	settings = app_settings.triage_model
	errors = list(state.get("errors") or [])
	if not settings.enabled:
		state.update(
			risk_level="MEDIUM",
			risk_confidence=0.0,
			risk_explanation={"reason": "pretriage_disabled"},
			validated_vitals={},
			derived_features={},
			signal_quality={},
			ruleset_version=None,
			growth_reference_version=None,
			model_version=None,
			classifier_status="DISABLED",
			emergency_escalate=False,
			errors=errors,
		)
		return state
	try:
		ruleset = load_ruleset_with_policy(
			settings.rules_path,
			allow_draft_rules=settings.allow_draft_rules,
			require_reviewed_rules=settings.require_reviewed_rules
			or app_settings.environment == "production",
		)
	except Exception as exc:
		logger.exception("Pre-triage ruleset unavailable")
		add_pipeline_error(
			state,
			stage="pretriage_rules",
			code=type(exc).__name__,
			message="Pre-triage rules unavailable; fail-safe medium risk used.",
		)
		state.update(
			risk_level="MEDIUM",
			risk_confidence=0.0,
			risk_explanation={"reason": "ruleset_failure"},
			validated_vitals={},
			derived_features={},
			signal_quality={},
			ruleset_version=None,
			model_version=None,
			classifier_status="RULESET_FAILURE",
		)
		return state

	vitals = _extract_vitals(state)
	validated, quality, deltas = _validate_vitals(vitals, state, ruleset)
	state["validated_vitals"] = validated
	state["signal_quality"] = quality

	waz = None
	growth_version = None
	try:
		growth = load_growth_reference_with_policy(
			settings.growth_reference_path,
			allow_draft_rules=settings.allow_draft_rules,
			require_reviewed_rules=settings.require_reviewed_rules
			or app_settings.environment == "production",
		)
		growth_version = growth.reference_version
		if validated.get("weight_kg") is not None:
			waz = growth.weight_for_age_zscore(
				sex=state.get("sex", ""),
				age_months=state.get("age_months", 0),
				weight_kg=validated["weight_kg"],
			)
	except Exception as exc:
		errors.append(
			{
				"stage": "growth_reference",
				"code": type(exc).__name__,
				"recoverable": True,
			}
		)

	features: dict[str, Any] = {
		"age_months": state.get("age_months"),
		"sex_male": 1.0 if state.get("sex") == "male" else 0.0,
		**validated,
		**deltas,
		"weight_for_age_zscore": waz,
		"spo2_deficit": (
			100 - validated["spo2"] if validated.get("spo2") is not None else None
		),
		"diarrhea_duration_days": state.get("diarrhea_duration_days"),
	}
	checklist = state.get("asha_checklist") or {}
	for key, value in checklist.items():
		features[f"checklist_{key}"] = (
			1.0 if value is True else 0.0 if value is False else None
		)
	state["derived_features"] = features

	matched = _matched_rules(ruleset, features, checklist)
	deterministic_risk = max(
		(rule.risk for rule in matched),
		key=lambda risk: RISK_ORDER[risk],
		default=None,
	)
	model_risk = None
	confidence = 0.0
	shap_explanations: list[dict[str, Any]] = []
	probabilities: dict[str, float] = {}
	model_version = None
	classifier_status = "MODEL_UNAVAILABLE"
	try:
		model = _load_model()
		if model is not None:
			model_version = model.metadata.model_version
			model_risk, confidence, shap_explanations, probabilities = _model_prediction(
				model, features
			)
			classifier_status = "MODEL_OK"
	except Exception as exc:
		logger.exception("Pre-triage model failed")
		classifier_status = "MODEL_FAILURE"
		errors.append(
			{
				"stage": "pretriage_model",
				"code": type(exc).__name__,
				"recoverable": True,
			}
		)

	if model_risk is None:
		final_risk = deterministic_risk or "MEDIUM"
	elif deterministic_risk and RISK_ORDER[deterministic_risk] > RISK_ORDER[model_risk]:
		final_risk = deterministic_risk
	else:
		final_risk = model_risk

	if deterministic_risk:
		confidence = max(confidence, 1.0)
	state["risk_level"] = final_risk
	state["risk_confidence"] = confidence
	state["risk_explanation"] = {
		"deterministic_rules": [
			{
				"id": rule.id,
				"label": rule.label,
				"risk": rule.risk,
				"source": rule.source,
			}
			for rule in matched
		],
		"model_top_features": shap_explanations,
		"probabilities": probabilities,
	}
	state["ruleset_version"] = ruleset.ruleset_version
	state["growth_reference_version"] = growth_version
	state["model_version"] = model_version
	state["classifier_status"] = classifier_status
	state["medical_review_required"] = ruleset.status != "MEDICALLY_REVIEWED"
	state["emergency_escalate"] = final_risk == "CRITICAL"
	state["errors"] = errors
	return state
