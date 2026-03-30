"""AyushBot Backend — Differential Diagnosis Schema (Agent 2 Output Contract)."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class Citation(BaseModel):
	source_document: str
	page_number: Optional[int] = None
	section: Optional[str] = None
	chunk_id: str
	relevance_score: float = Field(..., ge=0.0, le=1.0)


class DiagnosisEntry(BaseModel):
	rank: int = Field(..., ge=1)
	condition_name: str
	icd_code: Optional[str] = None
	confidence: float = Field(..., ge=0.0, le=1.0)
	evidence_summary: str
	citations: List[Citation] = Field(default_factory=list)
	matching_symptoms: List[str] = Field(default_factory=list)
	differentiating_factors: List[str] = Field(default_factory=list)

	@field_validator("citations")
	@classmethod
	def _ensure_citations(cls, value: List[Citation]) -> List[Citation]:
		if not value:
			raise ValueError("Each diagnosis must include at least one citation")
		return value


class RetrievalMetrics(BaseModel):
	dense_retrieval_ms: float = 0.0
	sparse_retrieval_ms: float = 0.0
	reranking_ms: float = 0.0
	llm_synthesis_ms: float = 0.0
	total_ms: float = 0.0


class DifferentialDiagnosis(BaseModel):
	diagnoses: List[DiagnosisEntry] = Field(..., min_length=1, max_length=5)
	retrieval_metrics: RetrievalMetrics = Field(default_factory=RetrievalMetrics)
	evidence_chunks_used: int = 0
	model_confidence: float = Field(0.0, ge=0.0, le=1.0)

	@model_validator(mode="after")
	def _check_confidence_sum(self) -> "DifferentialDiagnosis":
		total = sum(entry.confidence for entry in self.diagnoses)
		if total > 1.0 + 1e-6:
			raise ValueError("Sum of diagnosis confidences must be <= 1.0")
		return self
