# =============================================================================
# AyushBot Backend — Differential Diagnosis Schema (Agent 2 Output Contract)
# =============================================================================
#
# PURPOSE:
#   Pydantic model defining the structured output of Agent 2 (Differential
#   Diagnosis Agent). This schema ensures every diagnosis includes explicit
#   evidence citations — the core anti-hallucination mechanism.
#
# FIELDS:
#
#   DifferentialDiagnosis (top-level response):
#     - diagnoses: list[DiagnosisEntry] — Ranked list of 2-3 candidate conditions
#     - retrieval_metrics: RetrievalMetrics — Performance timing data
#     - evidence_chunks_used: int — Number of RAG chunks used for synthesis
#     - model_confidence: float — Overall confidence in the differential (0.0-1.0)
#
#   DiagnosisEntry (per candidate condition):
#     - rank: int — Position in the differential (1 = most likely)
#     - condition_name: str — Human-readable condition name
#       (e.g., "Severe Pneumonia", "Severe Acute Malnutrition")
#     - icd_code: Optional[str] — ICD-10 code if available from the source
#       (e.g., "J18.9", "E43")
#     - confidence: float — Agent's confidence in this specific diagnosis (0.0-1.0)
#     - evidence_summary: str — Brief synthesis of the supporting evidence
#       from retrieved protocol chunks (2-3 sentences)
#     - citations: list[Citation] — Exact source references
#     - matching_symptoms: list[str] — Which of the patient's symptoms match
#       this condition's typical presentation
#     - differentiating_factors: list[str] — What distinguishes this condition
#       from the other candidates in the differential
#
#   Citation (source reference):
#     - source_document: str — Name of the source (e.g., "MoHFW STW", "WHO IMCI")
#     - page_number: Optional[int] — Page in the original PDF
#     - section: Optional[str] — Section heading or chapter
#     - chunk_id: str — Internal chunk identifier for audit trail
#     - relevance_score: float — Cross-encoder relevance score for this chunk
#
#   RetrievalMetrics:
#     - dense_retrieval_ms: float — Time for FAISS query
#     - sparse_retrieval_ms: float — Time for BM25 query
#     - reranking_ms: float — Time for cross-encoder reranking
#     - llm_synthesis_ms: float — Time for LLM response generation
#     - total_ms: float — End-to-end Agent 2 execution time
#
# VALIDATION RULES:
#   - diagnoses list must contain 1-5 entries (minimum 1, maximum 5)
#   - Each diagnosis must have at least one citation (no uncited claims)
#   - confidence values must sum to <= 1.0 across all diagnoses
#   - If no matching protocol found, a single entry with condition_name =
#     "Unknown presentation" and confidence = 0.0 must be returned
# =============================================================================
