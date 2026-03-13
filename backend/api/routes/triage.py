# =============================================================================
# AyushBot Backend — API Route: Triage Endpoints
# =============================================================================
#
# PURPOSE:
#   Defines the core patient assessment API endpoints. These are the primary
#   endpoints that the ASHA's Android app calls to run a triage.
#
# ENDPOINTS:
#
#   POST /api/v1/triage/assess
#     The main triage endpoint. Accepts a PatientAssessment request body
#     and returns a complete triage result.
#     - Request body: PatientAssessment schema (from agents/schemas/)
#     - Invokes the LangGraph orchestrator to run all agents
#     - Response: TriageResult containing:
#       - risk_level: LOW / MEDIUM / HIGH / CRITICAL
#       - differential_diagnosis: ranked conditions with citations
#       - action_plan: referral + medications + instructions
#       - asha_output_text: translated response in local language
#       - asha_output_audio_url: URL to download TTS audio (if generated)
#     - Latency target: < 1 second end-to-end
#     - HTTP 200 on success
#     - HTTP 422 on validation error (bad request body)
#     - HTTP 500 on internal pipeline failure (with safe error message)
#
#   GET /api/v1/triage/history/{patient_id}
#     Retrieves the triage history for a specific patient.
#     - Returns a list of past TriageResult objects ordered by timestamp
#     - Used by the ASHA to review previous visits
#     - Paginated: ?page=1&per_page=10
#
#   GET /api/v1/triage/encounter/{encounter_id}
#     Retrieves a single triage encounter by its unique ID.
#     - Returns the full TriageResult including agent execution metadata
#     - Used for auditing and debugging
#
# REQUEST FLOW:
#   POST /assess → Validate input → Orchestrator → Agents 5→1→2→3→5 → Store
#   in DB → Return response
#
# ERROR HANDLING:
#   - Validation errors: Return 422 with field-level error details
#   - Agent failures: Return 200 with degraded response (fallback messages)
#   - Database errors: Return 500 with generic "Internal error" message
#   - Never expose internal stack traces or model details in error responses
# =============================================================================
