# =============================================================================
# AyushBot Backend — Agent 1: Intake & Pre-Triage Agent (The Gatekeeper)
# =============================================================================
#
# PURPOSE:
#   This agent is the first clinical gate in the triage pipeline. It performs
#   signal validation, feature engineering, and deterministic risk stratification
#   on the raw sensor data received from the ASHA's phone. No LLM reasoning
#   occurs here — this agent is purely deterministic and statistical.
#
# INPUTS (from Patient State Object):
#   - raw_vitals: dict containing SpO2, HR, Temperature, Weight from BLE
#   - patient_demographics: age (months), sex, village_id
#   - asha_checklist: structured categorical inputs from the mobile app
#     (e.g., "Is the child breastfeeding?", "Any visible chest indrawing?",
#      "Is the child lethargic or unconscious?")
#   - translated_symptoms: standardized clinical entities from Agent 5
#
# PROCESSING STEPS:
#
#   Step 1 — Signal Quality Filtering
#     Check each vital sign for validity:
#     - SpO2: If variance over the last N readings exceeds a threshold,
#       flag as motion artifact and prompt ASHA to re-attach sensor.
#     - HR: If value is outside physiological bounds (30-250 BPM), reject.
#     - Temperature: If value is outside (30°C-45°C), reject.
#     - Weight: If value is negative or above 30 kg (pediatric scale), reject.
#     Result: Each vital is marked as VALID or INVALID.
#
#   Step 2 — Feature Engineering
#     From the validated vitals + checklist, compute derived features:
#     - Weight-for-Age Z-score (using WHO growth standard lookup tables)
#     - Heart Rate deviation from age-normal range
#     - SpO2 deficit from normal (100% - measured)
#     - Composite danger score from checklist flags (each flag adds points)
#     - Delta features (ΔSpO2, ΔHR over 30-second window, if available)
#
#   Step 3 — Risk Classification
#     Feed the 10-15 feature vector into the pre-trained XGBoost classifier:
#     - Model loaded from the ONNX or pickle file at gateway startup
#     - Outputs: Risk level (LOW, MEDIUM, HIGH, CRITICAL) + confidence score
#     - Also outputs: Top-3 most influential features (SHAP values) for
#       explainability in the ASHA-facing response.
#
# OUTPUTS (written to Patient State Object):
#   - validated_vitals: dict of quality-checked, Kalman-filtered vitals
#   - derived_features: dict of engineered features (Z-scores, deltas, etc.)
#   - risk_level: enum (LOW, MEDIUM, HIGH, CRITICAL)
#   - risk_confidence: float (0.0-1.0)
#   - risk_explanation: list of top contributing features (for ASHA display)
#   - signal_quality_flags: dict indicating which sensors had valid data
#
# ARCHITECTURAL ESCALATION:
#   If risk_level == CRITICAL (e.g., SpO2 < 90%, or checklist flags indicate
#   unconsciousness or severe chest indrawing):
#     → The orchestrator BYPASSES Agent 2 (Diagnosis) entirely
#     → Routes directly to Agent 3 (Referral) with emergency evacuation mode
#     → This ensures zero delay for life-threatening situations.
#
# MODEL DEPENDENCY:
#   - XGBoost classifier: loaded once at startup from backend/models/ or
#     a configured path in config.yaml
#   - WHO Z-score lookup tables: bundled as static CSV or JSON files
#   - No external API calls. Fully offline.
#
# LATENCY TARGET: < 50 ms total (feature engineering + model inference)
# =============================================================================

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any, Dict, Tuple

import numpy as np
import xgboost as xgb
import yaml

from backend.agents.state import PatientState

logger = logging.getLogger(__name__)


def _load_config() -> Dict[str, Any]:
	config_path = os.getenv("AYUSHBOT_CONFIG") or os.path.join(
		os.path.dirname(__file__), "..", "config.yaml"
	)
	if not os.path.exists(config_path):
		return {}
	try:
		with open(config_path, "r", encoding="utf-8") as handle:
			return yaml.safe_load(handle) or {}
	except Exception as exc:  # pragma: no cover
		logger.error("Failed to load config: %s", exc)
		return {}


def _model_path(config: Dict[str, Any]) -> str:
	model_cfg = config.get("triage_model", {}) if isinstance(config, dict) else {}
	return os.getenv(
		"AYUSHBOT_XGB_MODEL_PATH", model_cfg.get("path", "/opt/ayushbot/models/triage_xgb.json")
	)


@lru_cache(maxsize=1)
def _load_model() -> xgb.Booster | None:
	config = _load_config()
	path = _model_path(config)
	if not path or not os.path.exists(path):
		logger.warning("XGBoost model not found at %s; using rule-based fallback", path)
		return None
	try:
		booster = xgb.Booster()
		booster.load_model(path)
		return booster
	except Exception as exc:
		logger.error("Failed to load XGBoost model: %s", exc)
		return None


def _extract_vitals(state: PatientState) -> Dict[str, float | None]:
	raw = state.get("raw_vitals", {})
	return {
		"spo2": raw.get("spo2"),
		"heart_rate": raw.get("heart_rate"),
		"temperature": raw.get("temperature_celsius"),
		"weight_kg": state.get("weight_kg"),
	}


def _validate_vitals(vitals: Dict[str, float | None]) -> Tuple[Dict[str, float | None], Dict[str, str]]:
	validated: Dict[str, float | None] = {}
	flags: Dict[str, str] = {}

	spo2 = vitals.get("spo2")
	if spo2 is None or spo2 < 40 or spo2 > 100:
		validated["spo2"] = None
		flags["spo2"] = "INVALID"
	else:
		validated["spo2"] = float(spo2)
		flags["spo2"] = "VALID"

	heart_rate = vitals.get("heart_rate")
	if heart_rate is None or heart_rate < 30 or heart_rate > 250:
		validated["heart_rate"] = None
		flags["heart_rate"] = "INVALID"
	else:
		validated["heart_rate"] = float(heart_rate)
		flags["heart_rate"] = "VALID"

	temperature = vitals.get("temperature")
	if temperature is None or temperature < 30 or temperature > 45:
		validated["temperature"] = None
		flags["temperature"] = "INVALID"
	else:
		validated["temperature"] = float(temperature)
		flags["temperature"] = "VALID"

	weight = vitals.get("weight_kg")
	if weight is None or weight <= 0 or weight > 60:
		validated["weight_kg"] = None
		flags["weight_kg"] = "INVALID"
	else:
		validated["weight_kg"] = float(weight)
		flags["weight_kg"] = "VALID"

	return validated, flags


def _critical_from_vitals(validated: Dict[str, float | None]) -> bool:
	spo2 = validated.get("spo2")
	heart_rate = validated.get("heart_rate")
	temperature = validated.get("temperature")
	if spo2 is not None and spo2 < 90:
		return True
	if heart_rate is not None and (heart_rate < 40 or heart_rate > 180):
		return True
	if temperature is not None and temperature >= 41.0:
		return True
	return False


def _rule_based_risk(validated: Dict[str, float | None]) -> Tuple[str, float, list[str]]:
	if _critical_from_vitals(validated):
		return "CRITICAL", 0.95, ["vital_threshold"]
	if validated.get("spo2") is not None and validated["spo2"] < 94:
		return "HIGH", 0.8, ["low_spo2"]
	if validated.get("temperature") is not None and validated["temperature"] >= 39.0:
		return "MEDIUM", 0.65, ["fever"]
	return "LOW", 0.55, ["stable_vitals"]


def _model_risk(
	booster: xgb.Booster, features: np.ndarray
) -> Tuple[str, float, list[str]]:
	dmatrix = xgb.DMatrix(features)
	probs = booster.predict(dmatrix)
	if probs.ndim == 1:
		probs = np.array([probs])
	classes = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
	idx = int(np.argmax(probs[0]))
	confidence = float(probs[0][idx])
	return classes[idx], confidence, ["xgboost"]


def run_intake(state: PatientState) -> PatientState:
	vitals = _extract_vitals(state)
	validated, flags = _validate_vitals(vitals)
	state["validated_vitals"] = validated
	state["signal_quality"] = flags

	booster = _load_model()
	features = np.array(
		[
			state.get("age_months", 0),
			validated.get("spo2") or 0.0,
			validated.get("heart_rate") or 0.0,
			validated.get("temperature") or 0.0,
			validated.get("weight_kg") or 0.0,
		],
		dtype=np.float32,
	).reshape(1, -1)

	if booster:
		risk_level, confidence, explanation = _model_risk(booster, features)
	else:
		risk_level, confidence, explanation = _rule_based_risk(validated)

	state["risk_level"] = risk_level
	state["risk_confidence"] = confidence
	state["risk_explanation"] = explanation
	state["derived_features"] = {
		"spo2_deficit": 100 - validated.get("spo2", 100) if validated.get("spo2") else None,
		"fever_flag": validated.get("temperature") is not None
		and validated.get("temperature") >= 38.0,
	}

	if _critical_from_vitals(validated):
		state["risk_level"] = "CRITICAL"
		state["risk_confidence"] = max(state.get("risk_confidence") or 0.0, 0.9)

	return state
