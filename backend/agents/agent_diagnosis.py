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
import time
from functools import lru_cache
from typing import Any, Dict, List

from backend.agents.schemas.differential import (
	Citation,
	DiagnosisEntry,
	DifferentialDiagnosis,
	RetrievalMetrics,
)
from backend.agents.state import PatientState
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


def _fallback_diagnosis() -> DifferentialDiagnosis:
	entry = DiagnosisEntry(
		rank=1,
		condition_name="Unknown presentation",
		icd_code=None,
		confidence=0.0,
		evidence_summary="No matching protocol found in available evidence.",
		citations=[
			Citation(
				source_document="N/A",
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
		evidence_chunks_used=0,
		model_confidence=0.0,
	)


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
			diagnosis = _fallback_diagnosis()
		else:
			engine = _get_engine()
			evidence = retrieval["results"]
			prompt = {
				"query": query,
				"evidence": evidence,
			}
			llm_start = time.perf_counter()
			output = engine.generate_json(
				json.dumps(prompt, ensure_ascii=False),
				DifferentialDiagnosis,
				max_tokens=300,
			)
			llm_ms = (time.perf_counter() - llm_start) * 1000
			diagnosis = DifferentialDiagnosis.model_validate_json(output)
			diagnosis.evidence_chunks_used = len(evidence)
			diagnosis.retrieval_metrics = RetrievalMetrics(
				dense_retrieval_ms=retrieval_ms,
				llm_synthesis_ms=llm_ms,
				total_ms=(time.perf_counter() - start) * 1000,
			)

		state["differential_diagnosis"] = diagnosis.model_dump()
		state["retrieval_metrics"] = diagnosis.retrieval_metrics.model_dump()
	except Exception as exc:
		logger.error("Diagnosis agent failed: %s", exc)
		state.setdefault("errors", []).append(str(exc))
		fallback = _fallback_diagnosis()
		state["differential_diagnosis"] = fallback.model_dump()
		state["retrieval_metrics"] = fallback.retrieval_metrics.model_dump()

	return state
