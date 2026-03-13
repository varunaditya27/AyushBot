# =============================================================================
# AyushBot Tests — Unit: Referral Agent (Agent 3)
# =============================================================================
#
# PURPOSE:
#   Unit tests for the Referral & Action Plan Agent (backend/agents/agent_referral.py).
#   Verifies correct referral routing, drug dosage calculations, and
#   action plan generation.
#
# TEST CASES:
#
#   test_critical_case_emergency_referral
#     Input: risk_level=CRITICAL, diagnosis=["severe_pneumonia"]
#     Expected: Action plan includes immediate evacuation instructions,
#       pre-referral treatment (first dose antibiotic), and the nearest
#       DH/CHC facility with emergency services
#
#   test_drug_dosage_weight_based
#     Input: weight_kg=10.0, drug="paracetamol", indication="fever"
#     Expected: Dosage = 150 mg (15 mg/kg for paracetamol)
#     Verify: Dosage within WHO pediatric dosage range
#     Safety: Dosage must NOT exceed max single dose for the child's weight
#
#   test_drug_dosage_age_fallback
#     Input: weight_kg=None (scale unavailable), age_months=24, drug="ORS"
#     Expected: ORS dose computed from age-based estimation
#     Note: Age-based dosing is less accurate but better than no dosing
#
#   test_facility_routing_dijkstra
#     Input: GPS coordinates, risk_level=HIGH
#     Expected: Agent returns the optimal facility based on:
#       - Distance (shortest travel time)
#       - Facility level (must be CHC or higher for HIGH risk)
#       - Facility availability (not already at capacity)
#     Verify: Routing uses Dijkstra's algorithm on the facility graph
#
#   test_low_risk_home_management_plan
#     Input: risk_level=LOW, diagnosis=["mild_diarrhea"]
#     Expected: Action plan includes home management instructions
#       (ORS recipe, danger sign watchlist, follow-up in 3 days)
#       NO referral generated (unnecessary system burden)
#
#   test_action_plan_schema_compliance
#     Input: Any valid case
#     Expected: Output conforms to schemas/action_plan.py Pydantic model
#
# FIXTURES USED:
#   - sample_patient_state, mock_llm_client
# =============================================================================
