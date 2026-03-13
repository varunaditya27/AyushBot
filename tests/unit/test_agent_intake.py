# =============================================================================
# AyushBot Tests — Unit: Intake Agent (Agent 1)
# =============================================================================
#
# PURPOSE:
#   Unit tests for the Intake/Pre-Triage Agent (backend/agents/agent_intake.py).
#   Verifies that the agent correctly classifies patients into risk levels
#   based on vital signs and ASHA checklist inputs.
#
# TEST CASES:
#
#   test_classify_critical_case
#     Input: SpO2=85%, HR=180, Temp=40.2°C, chest_indrawing=True
#     Expected: risk_level=CRITICAL, confidence >= 0.8
#     Rationale: Multiple danger signs, severe hypoxia → CRITICAL
#
#   test_classify_low_risk_case
#     Input: SpO2=98%, HR=120, Temp=36.8°C, no_danger_signs
#     Expected: risk_level=LOW, confidence >= 0.7
#     Rationale: Normal vitals, no danger signs → LOW
#
#   test_classify_medium_risk_case
#     Input: SpO2=95%, HR=140, Temp=38.5°C, cough=True
#     Expected: risk_level=MEDIUM or HIGH
#     Rationale: Mild fever + elevated HR, borderline case
#
#   test_missing_spo2_handling
#     Input: SpO2=None (sensor failed), HR=130, Temp=37.5°C
#     Expected: Agent handles gracefully (uses imputed or fallback logic),
#       does NOT crash, flags the sensor failure in output
#
#   test_who_zscore_computation
#     Input: age_months=18, weight_kg=7.5, sex="female"
#     Expected: WAZ < -2 (underweight), correctly computed from WHO tables
#
#   test_output_schema_compliance
#     Input: Any valid patient data
#     Expected: Output conforms to schemas/patient_assessment.py Pydantic model
#
#   test_shap_explanation_present
#     Input: Any valid patient data
#     Expected: The output includes a SHAP-based explanation of which features
#       contributed most to the risk classification
#
# FIXTURES USED:
#   - sample_patient_state (from conftest.py)
#   - mock_xgboost_model (to avoid loading real model in tests)
# =============================================================================
