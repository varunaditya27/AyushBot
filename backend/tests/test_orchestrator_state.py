from __future__ import annotations

from backend.agents import orchestrator


def _base_state():
	return {
		"age_months": 18,
		"sex": "female",
		"village_id": "synthetic-village",
		"asha_id": "asha-demo",
		"raw_vitals": {},
		"asha_checklist": {},
		"agent_timings": {},
		"errors": [],
		"pipeline_status": "IN_PROGRESS",
	}


def test_sequential_pipeline_success_has_predictable_status(monkeypatch):
	monkeypatch.setattr(orchestrator, "StateGraph", None)
	monkeypatch.setattr(
		orchestrator,
		"preprocess_input",
		lambda state: {**state, "translated_symptoms": ["fever"]},
	)
	monkeypatch.setattr(
		orchestrator,
		"run_intake",
		lambda state: {**state, "risk_level": "LOW", "risk_confidence": 0.5},
	)
	monkeypatch.setattr(
		orchestrator,
		"run_diagnosis",
		lambda state: {
			**state,
			"differential_diagnosis": {
				"diagnoses": [{"condition_name": "Synthetic"}]
			},
		},
	)
	monkeypatch.setattr(
		orchestrator,
		"run_referral",
		lambda state: {**state, "action_plan": {"primary_diagnosis": "Synthetic"}},
	)
	monkeypatch.setattr(
		orchestrator,
		"postprocess_output",
		lambda state: {**state, "asha_output_text": "Synthetic output"},
	)

	result = orchestrator.run_pipeline(_base_state())

	assert result["pipeline_status"] == "COMPLETED"
	assert result["errors"] == []
	assert result["asha_output_text"] == "Synthetic output"
	assert {"language_in", "intake", "diagnosis", "referral", "language_out"} <= set(
		result["agent_timings"]
	)


def test_critical_pipeline_skips_diagnosis_and_uses_referral_path(monkeypatch):
	diagnosis_called = {"value": False}
	monkeypatch.setattr(orchestrator, "StateGraph", None)
	monkeypatch.setattr(orchestrator, "preprocess_input", lambda state: state)
	monkeypatch.setattr(
		orchestrator,
		"run_intake",
		lambda state: {**state, "risk_level": "CRITICAL"},
	)

	def _diagnosis(state):
		diagnosis_called["value"] = True
		return state

	monkeypatch.setattr(orchestrator, "run_diagnosis", _diagnosis)
	monkeypatch.setattr(
		orchestrator,
		"run_referral",
		lambda state: {**state, "action_plan": {"urgency": "IMMEDIATE"}},
	)
	monkeypatch.setattr(orchestrator, "postprocess_output", lambda state: state)

	result = orchestrator.run_pipeline(_base_state())

	assert diagnosis_called["value"] is False
	assert result["risk_level"] == "CRITICAL"
	assert result["action_plan"]["urgency"] == "IMMEDIATE"


def test_agent_failure_returns_structured_error_and_fallback(monkeypatch):
	monkeypatch.setattr(orchestrator, "StateGraph", None)
	monkeypatch.setattr(orchestrator, "preprocess_input", lambda state: state)

	def _intake_failure(_state):
		raise ValueError("synthetic failure")

	monkeypatch.setattr(orchestrator, "run_intake", _intake_failure)
	monkeypatch.setattr(orchestrator, "run_diagnosis", lambda state: state)
	monkeypatch.setattr(orchestrator, "run_referral", lambda state: state)
	monkeypatch.setattr(orchestrator, "postprocess_output", lambda state: state)

	result = orchestrator.run_pipeline(_base_state())

	assert result["pipeline_status"] == "DEGRADED"
	assert result["risk_level"] == "MEDIUM"
	assert result["errors"][0]["stage"] == "intake"
	assert result["errors"][0]["code"] == "ValueError"
	assert result["errors"][0]["recoverable"] is True
	assert result["action_plan"]["immediate_actions"] == [
		"Refer to nearest available medical officer"
	]


def test_compiled_graph_is_cached(monkeypatch):
	orchestrator.clear_graph_cache()
	calls = {"compile": 0}

	class _Graph:
		def compile(self):
			calls["compile"] += 1
			return object()

	monkeypatch.setattr(orchestrator, "StateGraph", object())
	monkeypatch.setattr(orchestrator, "build_graph", lambda: _Graph())

	first = orchestrator.get_compiled_graph()
	second = orchestrator.get_compiled_graph()

	assert first is second
	assert calls["compile"] == 1
	orchestrator.clear_graph_cache()
