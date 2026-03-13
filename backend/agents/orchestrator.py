# =============================================================================
# AyushBot Backend — Multi-Agent Orchestrator (State Machine Router)
# =============================================================================
#
# PURPOSE:
#   This is the central brain of the AyushBot backend. It implements a
#   LangGraph-based Directed Acyclic Graph (DAG) state machine that routes
#   the shared Patient State Object between the five specialized agents.
#
#   It is NOT an agent itself — it is the controller that decides which agent
#   runs next, based on the current state of the patient assessment.
#
# ARCHITECTURE:
#   The orchestrator models clinical triage as a state graph with the
#   following nodes (agents) and edges (transitions):
#
#   START
#     → Agent 5 (Language): Translate ASHA's input to standardized clinical English
#     → Agent 1 (Intake): Validate vitals + compute risk badge
#       → IF Critical: SKIP to Agent 3 (emergency fast-track)
#       → ELSE: Continue to Agent 2
#     → Agent 2 (Diagnosis): EdgeRAG retrieval + LLM differential synthesis
#     → Agent 3 (Referral): Facility routing + drug dosage planning
#     → Agent 5 (Language): Translate clinical output back to ASHA's language
#   END
#
# THE PATIENT STATE OBJECT:
#   A single mutable state dictionary (TypedDict or Pydantic model) that
#   accumulates data as it passes through each agent. Each agent reads the
#   fields it needs and writes the fields it produces. Fields include:
#     - raw_vitals: dict of sensor readings (from BLE)
#     - validated_vitals: dict of Kalman-filtered, quality-checked vitals
#     - asha_input_text: raw text/voice transcription in local language
#     - translated_symptoms: standardized English clinical entities
#     - risk_level: enum (LOW, MEDIUM, HIGH, CRITICAL)
#     - differential_diagnosis: list of ranked diagnoses with citations
#     - action_plan: referral destination + drug list + dosage instructions
#     - asha_output_text: translated response in local language
#     - asha_output_audio: TTS audio bytes for voice delivery
#     - metadata: timestamps, agent execution times, confidence scores
#
# LANGGRAPH SPECIFICS:
#   - Uses LangGraph's StateGraph class for defining the agent DAG
#   - Each agent is registered as a node with an input/output state schema
#   - Conditional edges implement the "Critical → fast-track" bypass logic
#   - State checkpointing after each agent enables:
#       a. Full audit trail (every intermediate state is logged)
#       b. Replay capability (re-run from any checkpoint for debugging)
#       c. Graceful recovery (if an agent crashes, resume from last checkpoint)
#
# ERROR HANDLING:
#   - If any agent raises an exception, the orchestrator catches it, logs the
#     error, and attempts a fallback:
#       Agent 2 failure → return "Unable to diagnose; refer to PHC doctor"
#       Agent 3 failure → return generic "Refer to nearest PHC"
#       Agent 5 failure → return English output (ASHA may need help reading)
#   - Agent 1 failure is not recoverable — vitals are required. The system
#     returns an error asking the ASHA to re-measure.
#
# CONCURRENCY:
#   - The orchestrator is designed to handle ONE patient assessment at a time
#     per request (synchronous pipeline).
#   - Multiple concurrent ASHA requests are handled by FastAPI's async
#     request handling — each request gets its own orchestrator invocation
#     with an isolated state object.
#   - Agent 4 (FL Sync) runs asynchronously in the background and is NOT
#     part of the real-time triage DAG.
#
# LOGGING:
#   Every agent transition, state mutation, and error is logged with
#   structured JSON for post-hoc analysis and debugging. Includes:
#   - agent_name, start_time, end_time, duration_ms
#   - input_state_hash, output_state_hash (for state diff tracking)
#   - error (if any), fallback_used (bool)
# =============================================================================
