# =============================================================================
# AyushBot Backend — Shared Patient State Object Schema
# =============================================================================
#
# PURPOSE:
#   Defines the central data structure that flows through the multi-agent
#   orchestration pipeline. This is the single mutable state object that
#   accumulates data as it passes through each agent.
#
#   Every agent reads the fields it needs and writes the fields it produces.
#   The orchestrator manages the lifecycle of this object for each patient
#   assessment request.
#
# WHY A SHARED STATE OBJECT:
#   Instead of agents communicating via message queues or RPC calls, they
#   share a single structured state object. This design:
#     1. Enables full state serialization for audit trails and replay
#     2. Makes agent dependencies explicit (agent reads field X, writes field Y)
#     3. Avoids complex inter-agent communication protocols
#     4. Allows LangGraph to checkpoint state after each agent transition
#
# SCHEMA STRUCTURE:
#   The state object is a LangGraph-compatible TypedDict (or Pydantic model)
#   with the following field groups:
#
#   === PATIENT IDENTITY ===
#   - patient_id: optional ABHA ID or locally-generated UUID
#   - patient_name: string (local language)
#   - age_months: integer (age in months — critical for pediatric dosing)
#   - sex: enum (MALE, FEMALE, OTHER)
#   - weight_kg: float (from HX711 sensor or manual entry)
#   - village_id: string (geographic identifier for routing)
#   - asha_id: string (identifier of the ASHA conducting the assessment)
#
#   === RAW INPUTS ===
#   - raw_vitals: dict of sensor readings as received from BLE
#   - asha_input_text: raw text/voice transcription in local language
#   - asha_checklist: dict of structured categorical inputs
#   - input_language: ISO 639-1 code of the ASHA's language
#
#   === AGENT 5 (PHASE 1) OUTPUTS ===
#   - intent: clinical intent enum
#   - extracted_entities: list of NER results
#   - translated_symptoms: list of standardized English terms
#
#   === AGENT 1 OUTPUTS ===
#   - validated_vitals: quality-checked and filtered vital signs
#   - derived_features: engineered features (Z-scores, deltas, composites)
#   - risk_level: enum (LOW, MEDIUM, HIGH, CRITICAL)
#   - risk_confidence: float
#   - risk_explanation: list of contributing features
#   - signal_quality: dict of per-sensor quality flags
#
#   === AGENT 2 OUTPUTS ===
#   - differential_diagnosis: list of DifferentialDiagnosis schemas
#   - retrieved_chunks: list of RAG chunk objects (for audit)
#   - retrieval_metrics: dict of timing info
#
#   === AGENT 3 OUTPUTS ===
#   - action_plan: ActionPlan schema (referral + drugs + instructions)
#   - routing_result: facility details + Dijkstra path
#   - prescriptions: list of drug dosage objects
#
#   === AGENT 5 (PHASE 2) OUTPUTS ===
#   - asha_output_text: translated response in local language
#   - asha_output_audio: TTS audio bytes
#
#   === METADATA ===
#   - request_id: UUID for this assessment
#   - created_at: ISO timestamp
#   - agent_timings: dict of per-agent execution durations
#   - errors: list of any errors or fallbacks triggered
#   - pipeline_status: enum (IN_PROGRESS, COMPLETED, FAILED)
# =============================================================================
