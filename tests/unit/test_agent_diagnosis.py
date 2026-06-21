# =============================================================================
# AyushBot Tests — Unit: Diagnosis Agent (Agent 2)
# =============================================================================
#
# PURPOSE:
#   Unit tests for the Differential Diagnosis Agent (backend/agents/agent_diagnosis.py).
#   Verifies that the agent correctly performs EdgeRAG retrieval and LLM-based
#   differential diagnosis.
#
# TEST CASES:
#
#   test_rag_retrieval_relevant_chunks
#     Input: Symptoms = ["high_fever", "rash", "joint_pain"]
#     Expected: RAG retrieves chunks about dengue, measles, chikungunya
#       (relevant differential diagnoses for fever + rash + joint pain)
#     Mock: FAISS index with pre-loaded test chunks
#
#   test_differential_list_format
#     Input: Any valid symptom set
#     Expected: Output contains a ranked list of differential diagnoses,
#       each with (condition_name, confidence_score, supporting_evidence)
#     Schema: Must conform to schemas/differential.py
#
#   test_top_diagnosis_clinically_reasonable
#     Input: SpO2=88%, cough, chest_indrawing, fever
#     Expected: Top diagnosis should be pneumonia (classic IMCI presentation)
#     Note: This is a clinical reasonableness check, not exact match
#
#   test_rag_retrieval_with_empty_index
#     Input: Any symptoms, but FAISS index is empty
#     Expected: Agent handles gracefully — falls back to LLM-only reasoning
#       (without RAG context), flags that no guidelines were retrieved
#
#   test_llm_context_window_not_exceeded
#     Input: A case with many symptoms that retrieves many RAG chunks
#     Expected: The total prompt (system + RAG context + symptoms) fits
#       within Phi-3 Mini's 4096 token context window. Excess chunks
#       are pruned by the reranker.
#
#   test_output_includes_guideline_citations
#     Input: Any valid case
#     Expected: Each diagnosis in the output cites which ASHA guideline
#       section supports it (traceability for the doctor to verify)
#
# FIXTURES USED:
#   - sample_patient_state, mock_llm_client, mock_faiss_index
# =============================================================================

import json

from backend.agents.agent_diagnosis import run_diagnosis


class _StubRetriever:
	def query(self, _text):
		return {"results": [], "guardrail_triggered": True}


def test_guardrail_fallback(sample_patient_state, monkeypatch):
	from backend.agents import agent_diagnosis

	monkeypatch.setattr(agent_diagnosis, "_get_retriever", lambda: _StubRetriever())
	result = run_diagnosis(sample_patient_state)
	diagnosis = result["differential_diagnosis"]
	assert diagnosis["diagnoses"][0]["condition_name"] == "Unknown presentation"
	assert diagnosis["citation_status"] == "NO_EVIDENCE_RETRIEVED"
	assert diagnosis["non_diagnostic_disclaimer"]


class _DisabledRetriever:
	def query(self, _text):
		return {"results": [], "guardrail_triggered": True, "disabled": True}


def test_rag_disabled_citation_behavior_is_explicit(sample_patient_state, monkeypatch):
	from backend.agents import agent_diagnosis

	monkeypatch.setattr(agent_diagnosis, "_get_retriever", lambda: _DisabledRetriever())
	result = run_diagnosis(sample_patient_state)
	diagnosis = result["differential_diagnosis"]
	assert diagnosis["citation_status"] == "RAG_DISABLED"
	assert diagnosis["diagnoses"][0]["citations"][0]["source_document"] == "RAG_DISABLED"


class _EvidenceRetriever:
	def query(self, _text):
		return {
			"guardrail_triggered": False,
			"results": [
				{
					"text": "Synthetic evidence only.",
					"score": 0.91,
					"metadata": {
						"chunk_id": "chunk-1",
						"source": "synthetic-guideline.txt",
						"section": "demo",
					},
				}
			],
		}


class _ValidEngine:
	def __init__(self):
		self.prompt = None

	def generate_json(self, prompt, _schema, max_tokens):
		self.prompt = prompt
		return json.dumps(
			{
				"diagnoses": [
					{
						"rank": 1,
						"condition_name": "Synthetic condition",
						"confidence": 0.4,
						"evidence_summary": "Supported by synthetic fixture.",
						"citations": [
							{
								"source_document": "synthetic-guideline.txt",
								"page_number": None,
								"section": "demo",
								"chunk_id": "chunk-1",
								"relevance_score": 0.91,
							}
						],
						"matching_symptoms": ["fever"],
						"differentiating_factors": [],
					}
				],
				"possible_conditions": ["Synthetic condition"],
				"uncertainty": "Moderate uncertainty.",
				"red_flags": ["high fever"],
				"recommended_next_action": "Review with Medical Officer.",
				"non_diagnostic_disclaimer": "Decision support only.",
				"citation_status": "REQUIRED_AND_PRESENT",
				"model_confidence": 0.4,
			}
		)


def test_llm_output_is_validated_and_prompt_is_structured(
	sample_patient_state, monkeypatch
):
	from backend.agents import agent_diagnosis

	engine = _ValidEngine()
	monkeypatch.setattr(agent_diagnosis, "_get_retriever", lambda: _EvidenceRetriever())
	monkeypatch.setattr(agent_diagnosis, "_get_engine", lambda: engine)
	result = run_diagnosis(sample_patient_state)
	diagnosis = result["differential_diagnosis"]
	prompt = json.loads(engine.prompt)
	assert prompt["system_instruction"]
	assert prompt["evidence"][0]["evidence_id"] == "chunk-1"
	assert diagnosis["possible_conditions"] == ["Synthetic condition"]
	assert diagnosis["red_flags"] == ["high fever"]
	assert diagnosis["recommended_next_action"] == "Review with Medical Officer."
	assert diagnosis["citation_status"] == "REQUIRED_AND_PRESENT"


class _InvalidCitationEngine:
	def generate_json(self, _prompt, _schema, max_tokens):
		return json.dumps(
			{
				"diagnoses": [
					{
						"rank": 1,
						"condition_name": "Unsupported",
						"confidence": 0.2,
						"evidence_summary": "bad citation",
						"citations": [
							{
								"source_document": "unknown",
								"chunk_id": "missing-chunk",
								"relevance_score": 0.5,
							}
						],
					}
				],
				"citation_status": "REQUIRED_AND_PRESENT",
			}
		)


def test_invalid_llm_citation_falls_back(sample_patient_state, monkeypatch):
	from backend.agents import agent_diagnosis

	monkeypatch.setattr(agent_diagnosis, "_get_retriever", lambda: _EvidenceRetriever())
	monkeypatch.setattr(agent_diagnosis, "_get_engine", lambda: _InvalidCitationEngine())
	result = run_diagnosis(sample_patient_state)
	assert result["differential_diagnosis"]["citation_status"] == "LLM_OUTPUT_INVALID"
	assert result["errors"][-1]["stage"] == "diagnosis"
