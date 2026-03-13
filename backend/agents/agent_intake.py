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
