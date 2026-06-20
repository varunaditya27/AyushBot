# =============================================================================
# AyushBot Backend — Agent 2: Differential Diagnosis Agent (The Clinical Reasoner)
# =============================================================================
#
# PURPOSE:
#   This agent performs evidence-backed medical reasoning using the EdgeRAG
#   retrieval pipeline. It is explicitly BANNED from relying on its own
#   parametric memory (the LLM's training data) for diagnosis. Every clinical
#   assertion must be backed by a retrieved source document.
#
# INPUTS (from Patient State Object):
#   - translated_symptoms: standardized English clinical entities from Agent 5
#   - validated_vitals: quality-checked vital signs from Agent 1
#   - derived_features: engineered features (Z-scores, deltas) from Agent 1
#   - risk_level: risk badge from Agent 1 (used to scope the search)
#
# PROCESSING STEPS:
#
#   Step 1 — Query Construction
#     Synthesize a structured clinical query from the patient's presentation:
#     - Combine symptom entities with vital sign context:
#       e.g., "2-year-old child, SpO2 88%, Temperature 39.2°C, chest indrawing,
#       tachypnea, poor feeding"
#     - Add the risk level as a query filter (HIGH/CRITICAL cases search
#       emergency protocols; LOW cases search outpatient guidelines)
#
#   Step 2 — EdgeRAG Retrieval (via backend.rag.pipeline)
#     a. Dense Retrieval: Embed the query using all-MiniLM-L6-v2 bi-encoder,
#        retrieve top-100 candidate chunks from the FAISS HNSW index
#     b. Sparse Retrieval: BM25 keyword search on the same corpus for
#        complementary lexical matches (catches exact drug names, ICD codes)
#     c. Hybrid Fusion: Merge dense + sparse results using Reciprocal Rank
#        Fusion (RRF) to produce a unified ranked list
#     d. Cross-Encoder Reranking: Score the top-20 fused results using
#        ms-marco-MiniLM cross-encoder for precise clinical relevance
#     e. Top-K Selection: Take the top-5 reranked chunks as the evidence set
#
#   Step 3 — LLM-Grounded Synthesis (via backend.llm)
#     Feed the top-5 evidence chunks + patient presentation into the quantized
#     Phi-3 Mini (or Gemma-3 1B) using a strictly constrained Jinja2 prompt:
#     - The prompt instructs the LLM to ONLY synthesize from provided chunks
#     - It MUST cite the source (document name, page number) for each claim
#     - It MUST output a ranked differential diagnosis (2-3 conditions)
#     - It MUST NOT speculate beyond what the evidence chunks contain
#     - If no matching protocol is found: output "Unknown presentation —
#       refer to PHC Medical Officer" (fail-safe)
#
#   Step 4 — Output Validation
#     Parse and validate the LLM output using a Pydantic schema (DifferentialDiagnosis):
#     - Each diagnosis must have a condition name, confidence, and citation
#     - If the LLM output fails to parse, fall back to returning the top-3
#       chunk titles as "possible conditions" without LLM synthesis
#
# OUTPUTS (written to Patient State Object):
#   - differential_diagnosis: list of DifferentialDiagnosis objects
#     Each contains:
#       - condition_name: str (e.g., "Severe Pneumonia")
#       - icd_code: str (e.g., "J18.9")
#       - confidence: float (0.0-1.0)
#       - evidence_summary: str (synthesis from retrieved chunks)
#       - citations: list of {source, page, section} dicts
#   - retrieved_chunks: list of raw chunk objects (for audit trail / logging)
#   - retrieval_metrics: dict (retrieval_time_ms, rerank_time_ms, llm_time_ms)
#
# HALLUCINATION PREVENTION:
#   This is the most critical design constraint of Agent 2. Mechanisms:
#   1. LLM sees ONLY retrieved chunks — no system knowledge
#   2. Prompt explicitly forbids assertions without citations
#   3. Output is validated against retrieved chunk content
#   4. If zero relevant chunks are retrieved (cosine similarity all below
#      threshold), the agent returns "Unknown" rather than guessing
#
# LATENCY TARGET: 200-400 ms (retrieval ~100 ms + reranking ~50 ms + LLM ~200 ms)
# =============================================================================

from __future__ import annotations

import json
import logging
import os
import time
from functools import lru_cache
from typing import Any

from backend.agents.schemas.differential import (
	Citation,
	DiagnosisEntry,
	DifferentialDiagnosis,
	RetrievalMetrics,
)
from backend.agents.state import PatientState, add_pipeline_error
from backend.config import get_settings
from backend.llm.engine import LlamaEngine, create_engine
from backend.rag.retriever import create_retriever

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_retriever():
	return create_retriever()


@lru_cache(maxsize=1)
def _get_engine() -> LlamaEngine:
	return create_engine()


def _build_query(state: PatientState) -> str:
	symptoms = ", ".join(state.get("translated_symptoms") or [])
	vitals = state.get("validated_vitals", {})
	parts = []
	if symptoms:
		parts.append(f"Symptoms: {symptoms}")
	if vitals:
		parts.append(
			"Vitals: "
			+ ", ".join(
				f"{key}={value}" for key, value in vitals.items() if value is not None
			)
		)
	risk = state.get("risk_level")
	if risk:
		parts.append(f"Risk: {risk}")
	return "; ".join(parts) or "clinical assessment"


def _fallback_diagnosis(*, citation_status: str = "NO_EVIDENCE_RETRIEVED") -> DifferentialDiagnosis:
	entry = DiagnosisEntry(
		rank=1,
		condition_name="Unknown presentation",
		icd_code=None,
		confidence=0.0,
		evidence_summary=(
			"No matching protocol found in available evidence."
			if citation_status != "RAG_DISABLED"
			else "RAG retrieval is disabled; no evidence citations were available."
		),
		citations=[
			Citation(
				source_document=citation_status,
				page_number=None,
				section=None,
				chunk_id="none",
				relevance_score=0.0,
			)
		],
		matching_symptoms=[],
		differentiating_factors=[],
	)
	return DifferentialDiagnosis(
		diagnoses=[entry],
		possible_conditions=["Unknown presentation"],
		uncertainty="High uncertainty because supporting evidence was unavailable.",
		red_flags=[],
		recommended_next_action="Refer to PHC Medical Officer for clinical review.",
		citation_status=citation_status,  # type: ignore[arg-type]
		evidence_chunks_used=0,
		model_confidence=0.0,
	)


def _demo_citation(section: str, score: float = 0.92) -> Citation:
	return Citation(
		source_document="AyushBot demo clinical knowledge fixture",
		page_number=None,
		section=section,
		chunk_id=f"demo:{section.lower().replace(' ', '-')}",
		relevance_score=score,
	)


def _demo_diagnosis(state: PatientState) -> DifferentialDiagnosis | None:
	"""Development-only deterministic cases for a polished offline demo.

	These fixtures do not replace real RAG/LLM artifacts. They make the school
	project showcase reliable when the production clinical corpus is absent.
	"""
	if get_settings().environment == "production":
		return None
	if os.getenv("AYUSHBOT_DEMO_SHOWCASE", "").strip().lower() not in {
		"1",
		"true",
		"yes",
	}:
		return None

	text = " ".join(state.get("translated_symptoms") or []).lower()
	checklist = state.get("asha_checklist") or {}
	vitals = state.get("validated_vitals") or {}
	risk = state.get("risk_level")
	age_months = int(state.get("age_months") or 0)
	respiratory_rate = vitals.get("respiratory_rate")
	spo2 = vitals.get("spo2")
	temperature = vitals.get("temperature")

	def entry(
		*,
		rank: int,
		name: str,
		confidence: float,
		summary: str,
		section: str,
		matches: list[str],
		differentiators: list[str] | None = None,
	) -> DiagnosisEntry:
		return DiagnosisEntry(
			rank=rank,
			condition_name=name,
			icd_code=None,
			confidence=confidence,
			evidence_summary=summary,
			citations=[_demo_citation(section)],
			matching_symptoms=matches,
			differentiating_factors=differentiators or [],
		)

	if (
		"cough" in text
		or "breath" in text
		or checklist.get("chest_indrawing")
		or (
			respiratory_rate is not None
			and ((2 <= age_months <= 11 and respiratory_rate > 50) or (12 <= age_months <= 59 and respiratory_rate > 40))
		)
	):
		diagnoses = [
			entry(
				rank=1,
				name="Possible pneumonia or acute respiratory infection",
				confidence=0.72,
				summary=(
					"Cough or difficult breathing with fast breathing/chest indrawing "
					"is treated as a respiratory danger pattern in the demo protocol."
				),
				section="Respiratory danger signs",
				matches=[
					item
					for item in [
						"cough or breathing complaint" if ("cough" in text or "breath" in text) else "",
						"chest indrawing" if checklist.get("chest_indrawing") else "",
						"fast respiratory rate" if respiratory_rate is not None else "",
					]
					if item
				],
				differentiators=[
					f"SpO2={spo2}" if spo2 is not None else "SpO2 not provided",
					f"risk={risk}",
				],
			),
			entry(
				rank=2,
				name="Fever with respiratory symptoms",
				confidence=0.18,
				summary="Fever can accompany respiratory infection and should be reviewed with the full clinical picture.",
				section="Fever with cough",
				matches=["fever"] if "fever" in text or (temperature is not None and temperature >= 38) else [],
			),
		]
		return DifferentialDiagnosis(
			diagnoses=diagnoses,
			possible_conditions=[item.condition_name for item in diagnoses],
			uncertainty="Moderate. This is deterministic demo support, not a definitive diagnosis.",
			red_flags=[
				flag
				for flag in [
					"chest indrawing" if checklist.get("chest_indrawing") else "",
					"low oxygen saturation" if spo2 is not None and spo2 < 90 else "",
					"high fever" if temperature is not None and temperature > 40 else "",
				]
				if flag
			],
			recommended_next_action=(
				"Refer urgently according to the generated action plan."
				if risk in {"HIGH", "CRITICAL"}
				else "Follow home-care guidance and monitor for worsening symptoms."
			),
			citation_status="REQUIRED_AND_PRESENT",
			evidence_chunks_used=1,
			model_confidence=0.72,
		)

	if "diarr" in text or checklist.get("dehydration") or state.get("diarrhea_duration_days"):
		diagnosis = entry(
			rank=1,
			name="Possible diarrheal illness with dehydration risk",
			confidence=0.68,
			summary="Diarrhea duration and dehydration flags should prompt hydration counseling and escalation if danger signs appear.",
			section="Diarrhea and dehydration",
			matches=["diarrhea", "dehydration risk"],
		)
		return DifferentialDiagnosis(
			diagnoses=[diagnosis],
			possible_conditions=[diagnosis.condition_name],
			uncertainty="Moderate. Demo protocol requires Medical Officer review for severe signs.",
			red_flags=["dehydration"] if checklist.get("dehydration") else [],
			recommended_next_action="Give oral rehydration counseling and refer if severe signs are present.",
			citation_status="REQUIRED_AND_PRESENT",
			evidence_chunks_used=1,
			model_confidence=0.68,
		)

	if "fever" in text or (temperature is not None and temperature >= 38):
		diagnosis = entry(
			rank=1,
			name="Uncomplicated fever pattern",
			confidence=0.6,
			summary="Fever without configured danger signs is handled as routine follow-up in the demo protocol.",
			section="Routine fever follow-up",
			matches=["fever"],
		)
		return DifferentialDiagnosis(
			diagnoses=[diagnosis],
			possible_conditions=[diagnosis.condition_name],
			uncertainty="Moderate. Continue monitoring for danger signs.",
			red_flags=[],
			recommended_next_action="Home-care counseling with follow-up after 48 hours.",
			citation_status="REQUIRED_AND_PRESENT",
			evidence_chunks_used=1,
			model_confidence=0.6,
		)

	return None


def _normalise_evidence_item(item: dict[str, Any], index: int) -> dict[str, Any]:
	metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
	return {
		"evidence_id": metadata.get("chunk_id")
		or metadata.get("id")
		or item.get("chunk_id")
		or f"evidence-{index}",
		"text": item.get("text", ""),
		"source_document": metadata.get("source_document")
		or metadata.get("source")
		or metadata.get("source_file")
		or item.get("source")
		or "unknown",
		"section": metadata.get("section") or metadata.get("section_heading"),
		"score": item.get("score") or item.get("fused_score") or item.get("dense_score"),
	}


def _build_prompt(query: str, state: PatientState, evidence: list[dict[str, Any]]) -> str:
	payload = {
		"system_instruction": (
			"You are a clinical decision-support summarizer for a college showcase. "
			"Use only the supplied evidence. Do not invent medical facts, dosages, "
			"or rules. If evidence is insufficient, say uncertainty is high and "
			"recommend Medical Officer review."
		),
		"patient_summary": {
			"query": query,
			"age_months": state.get("age_months"),
			"sex": state.get("sex"),
			"risk_level": state.get("risk_level"),
			"validated_vitals": state.get("validated_vitals", {}),
			"derived_features": state.get("derived_features", {}),
			"symptoms": state.get("translated_symptoms", []),
		},
		"evidence": evidence,
		"required_json_schema": {
			"diagnoses": "1-5 ranked possible conditions with citations to evidence_id",
			"possible_conditions": "list of condition names",
			"uncertainty": "brief uncertainty statement",
			"red_flags": "list of red flags present in evidence/patient summary",
			"recommended_next_action": "safe next action, not a definitive treatment",
			"non_diagnostic_disclaimer": "must state this is decision support only",
			"citation_status": "REQUIRED_AND_PRESENT",
		},
	}
	return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _validate_diagnosis_output(
	raw_output: str,
	*,
	evidence: list[dict[str, Any]],
	retrieval_ms: float,
	llm_ms: float,
	start: float,
) -> DifferentialDiagnosis:
	diagnosis = DifferentialDiagnosis.model_validate_json(raw_output)
	evidence_ids = {str(item["evidence_id"]) for item in evidence}
	for entry in diagnosis.diagnoses:
		if not entry.citations:
			raise ValueError("Diagnosis entry missing citation")
		for citation in entry.citations:
			if citation.chunk_id not in evidence_ids:
				raise ValueError("Diagnosis citation does not reference retrieved evidence")
	diagnosis.citation_status = "REQUIRED_AND_PRESENT"
	diagnosis.evidence_chunks_used = len(evidence)
	diagnosis.retrieval_metrics = RetrievalMetrics(
		dense_retrieval_ms=retrieval_ms,
		llm_synthesis_ms=llm_ms,
		total_ms=(time.perf_counter() - start) * 1000,
	)
	return diagnosis


def run_diagnosis(state: PatientState) -> PatientState:
	start = time.perf_counter()
	query = _build_query(state)
	try:
		retriever = _get_retriever()
		retrieval_start = time.perf_counter()
		retrieval = retriever.query(query)
		retrieval_ms = (time.perf_counter() - retrieval_start) * 1000
		state["retrieved_chunks"] = retrieval.get("results", [])

		if retrieval.get("guardrail_triggered") or not retrieval.get("results"):
			diagnosis = None
			if retrieval.get("disabled"):
				diagnosis = _demo_diagnosis(state)
			if diagnosis is None:
				diagnosis = _fallback_diagnosis(
					citation_status=(
						"RAG_DISABLED" if retrieval.get("disabled") else "NO_EVIDENCE_RETRIEVED"
					)
				)
		else:
			engine = _get_engine()
			evidence = [
				_normalise_evidence_item(item, index)
				for index, item in enumerate(retrieval["results"], start=1)
				if isinstance(item, dict)
			]
			if not evidence:
				diagnosis = _fallback_diagnosis(citation_status="NO_EVIDENCE_RETRIEVED")
				state["differential_diagnosis"] = diagnosis.model_dump()
				state["retrieval_metrics"] = diagnosis.retrieval_metrics.model_dump()
				return state
			prompt = _build_prompt(query, state, evidence)
			llm_start = time.perf_counter()
			output = engine.generate_json(
				prompt,
				DifferentialDiagnosis,
				max_tokens=300,
			)
			llm_ms = (time.perf_counter() - llm_start) * 1000
			diagnosis = _validate_diagnosis_output(
				output,
				evidence=evidence,
				retrieval_ms=retrieval_ms,
				llm_ms=llm_ms,
				start=start,
			)

		state["differential_diagnosis"] = diagnosis.model_dump()
		state["retrieval_metrics"] = diagnosis.retrieval_metrics.model_dump()
	except Exception as exc:
		logger.error("Diagnosis agent failed: %s", exc)
		add_pipeline_error(
			state,
			stage="diagnosis",
			code=type(exc).__name__,
			message="Diagnosis fallback used.",
		)
		fallback = _fallback_diagnosis(citation_status="LLM_OUTPUT_INVALID")
		state["differential_diagnosis"] = fallback.model_dump()
		state["retrieval_metrics"] = fallback.retrieval_metrics.model_dump()

	return state
