# =============================================================================
# AyushBot Tests — Integration: Full Triage Pipeline (Orchestrator)
# =============================================================================
#
# PURPOSE:
#   End-to-end integration test for the complete triage pipeline, running
#   all 5 agents through the LangGraph orchestrator (backend/agents/orchestrator.py).
#   Verifies that the agent pipeline produces a clinically coherent output
#   from raw sensor input to final action plan.
#
# TEST SCENARIO:
#
#   test_full_pipeline_critical_case
#     Input: Sensor payload with SpO2=85%, HR=180, Temp=40.2°C
#            ASHA checklist: chest_indrawing=True, not_drinking=True
#     Expected pipeline flow:
#       1. Language Agent: Translates input (if in local language)
#       2. Intake Agent: Classifies as CRITICAL (SpO2 < 90% + danger signs)
#       3. Diagnosis Agent: Retrieves pneumonia guidelines, generates
#          differential (severe pneumonia likely top diagnosis)
#       4. Referral Agent: Generates emergency referral with pre-referral
#          treatment and nearest facility with oxygen
#       5. Language Agent: Translates output to local language
#     Verify:
#       - Pipeline completes without errors
#       - Risk level = CRITICAL
#       - Action plan includes emergency referral
#       - Drug dosage is weight-appropriate
#       - Total pipeline latency logged
#
#   test_full_pipeline_low_risk_case
#     Input: Normal vitals, mild symptoms (e.g., mild cough, no fever)
#     Expected:
#       - Risk level = LOW
#       - Home management plan generated
#       - NO referral generated
#       - Follow-up instructions included
#
#   test_pipeline_with_sensor_failure
#     Input: SpO2=None (sensor failed), other vitals normal
#     Expected:
#       - Pipeline still completes (graceful degradation)
#       - Warning flag set in output (sensor_failure: true)
#       - Risk assessment uses available data only
#
#   test_pipeline_state_consistency
#     After running any scenario, verify that:
#       - The PatientState object is consistent across all agents
#       - No agent modified data from a previous agent's output improperly
#       - All timestamps are monotonically increasing
#
# MOCKING STRATEGY:
#   Integration tests mock the LLM and FAISS index (to avoid loading
#   multi-GB models in CI) but run everything else with real logic.
#   For full end-to-end with real models, see tests/simulation/.
#
# FIXTURES USED:
#   - sample_patient_state, mock_llm_client, mock_faiss_index, db_session
# =============================================================================
