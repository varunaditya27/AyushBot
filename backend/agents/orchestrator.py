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

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from functools import lru_cache
from typing import Any

try:
	from langgraph.graph import END, StateGraph
except ImportError:
	END = None
	StateGraph = None  # type: ignore[assignment]

from backend.agents.agent_diagnosis import run_diagnosis
from backend.agents.agent_intake import run_intake
from backend.agents.agent_language import postprocess_output, preprocess_input
from backend.agents.agent_referral import run_referral
from backend.agents.state import PatientState, add_pipeline_error

logger = logging.getLogger(__name__)


def _is_critical(state: PatientState) -> str:
	return "referral" if state.get("risk_level") == "CRITICAL" else "diagnosis"


def _ensure_fallback_action_plan(state: PatientState) -> None:
	if state.get("action_plan"):
		return
	urgency = "IMMEDIATE" if state.get("risk_level") == "CRITICAL" else "WITHIN_24H"
	state["action_plan"] = {
		"urgency": urgency,
		"referral": None,
		"medications": [],
		"immediate_actions": ["Refer to nearest available medical officer"],
		"follow_up": {"follow_up_date": "As soon as possible"},
		"referral_slip": None,
		"primary_diagnosis": (
			(state.get("differential_diagnosis") or {})
			.get("diagnoses", [{}])[0]
			.get("condition_name", "Unknown presentation")
		),
		"source_guideline": "",
	}


def _fallback_for_agent(agent_name: str, state: PatientState) -> None:
	if agent_name == "intake":
		state.setdefault("risk_level", "MEDIUM")
		state.setdefault("risk_confidence", 0.0)
		state.setdefault("risk_explanation", {"reason": "intake_failure"})
		state.setdefault("validated_vitals", {})
		state.setdefault("derived_features", {})
		state.setdefault("signal_quality", {})
		state["classifier_status"] = "INTAKE_FAILURE"
		state["emergency_escalate"] = state.get("risk_level") == "CRITICAL"
	elif agent_name == "diagnosis":
		state["differential_diagnosis"] = {
			"diagnoses": [
				{
					"rank": 1,
					"condition_name": "Unknown presentation",
					"icd_code": None,
					"confidence": 0.0,
					"evidence_summary": "Diagnosis agent fallback used.",
					"citations": [],
					"matching_symptoms": [],
					"differentiating_factors": [],
				}
			],
			"evidence_chunks_used": 0,
			"model_confidence": 0.0,
		}
		state.setdefault("retrieved_chunks", [])
		state.setdefault("retrieval_metrics", {})
	elif agent_name == "referral":
		_ensure_fallback_action_plan(state)
	elif agent_name == "language_out":
		state.setdefault("asha_output_text", "Refer to medical officer")
		state.setdefault("asha_output_audio", None)


def _run_agent(
	agent_name: str,
	handler: Callable[[PatientState], PatientState],
	state: PatientState,
) -> PatientState:
	start = time.perf_counter()
	try:
		next_state = handler(state)
	except Exception as exc:
		logger.exception("%s agent failed", agent_name)
		add_pipeline_error(
			state,
			stage=agent_name,
			code=type(exc).__name__,
			message=f"{agent_name} fallback used.",
		)
		_fallback_for_agent(agent_name, state)
		state["pipeline_status"] = "DEGRADED"
		next_state = state
	next_state.setdefault("agent_timings", {})[agent_name] = (
		time.perf_counter() - start
	) * 1000
	return next_state


def _language_in(state: PatientState) -> PatientState:
	return _run_agent("language_in", preprocess_input, state)


def _intake(state: PatientState) -> PatientState:
	return _run_agent("intake", run_intake, state)


def _diagnosis(state: PatientState) -> PatientState:
	return _run_agent("diagnosis", run_diagnosis, state)


def _referral(state: PatientState) -> PatientState:
	state = _run_agent("referral", run_referral, state)
	_ensure_fallback_action_plan(state)
	return state


def _language_out(state: PatientState) -> PatientState:
	return _run_agent("language_out", postprocess_output, state)


def build_graph() -> Any:
	if StateGraph is None:
		raise RuntimeError("langgraph is not installed")
	graph = StateGraph(PatientState)
	graph.add_node("language_in", _language_in)
	graph.add_node("intake", _intake)
	graph.add_node("diagnosis", _diagnosis)
	graph.add_node("referral", _referral)
	graph.add_node("language_out", _language_out)

	graph.set_entry_point("language_in")
	graph.add_edge("language_in", "intake")
	graph.add_conditional_edges("intake", _is_critical)
	graph.add_edge("diagnosis", "referral")
	graph.add_edge("referral", "language_out")
	graph.add_edge("language_out", END)
	return graph


@lru_cache(maxsize=1)
def get_compiled_graph() -> Any:
	return build_graph().compile()


def clear_graph_cache() -> None:
	get_compiled_graph.cache_clear()


def _run_sequential(state: PatientState) -> PatientState:
	state = _language_in(state)
	state = _intake(state)
	if state.get("risk_level") != "CRITICAL":
		state = _diagnosis(state)
	state = _referral(state)
	return _language_out(state)


def run_pipeline(state: PatientState) -> PatientState:
	if StateGraph is None:
		result = _run_sequential(state)
	else:
		result = get_compiled_graph().invoke(state)
	if result.get("pipeline_status") == "IN_PROGRESS":
		result["pipeline_status"] = "DEGRADED" if result.get("errors") else "COMPLETED"
	return result
