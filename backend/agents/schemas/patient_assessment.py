"""AyushBot Backend — Patient Assessment Schema (Agent 1 Input Contract)."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class VitalsSnapshot(BaseModel):
	spo2: Optional[int] = Field(default=None, ge=0, le=100)
	heart_rate: Optional[int] = Field(default=None, ge=20, le=300)
	temperature_celsius: Optional[float] = Field(default=None, ge=25.0, le=45.0)
	weight_grams: Optional[int] = Field(default=None, ge=0, le=30000)
	measurement_timestamp: Optional[datetime] = None
	signal_quality: Dict[str, float] = Field(default_factory=dict)


class PatientAssessment(BaseModel):
	patient_id: Optional[str] = None
	patient_name: Optional[str] = None
	age_months: int = Field(..., ge=0, le=600)
	sex: str
	weight_kg: Optional[float] = Field(default=None, ge=0.0, le=60.0)
	village_id: str = Field(..., min_length=1)
	asha_id: str = Field(..., min_length=1)
	vitals: Optional[VitalsSnapshot] = None
	asha_checklist: Dict[str, Optional[bool]] = Field(default_factory=dict)
	symptom_text: Optional[str] = None
	input_language: Optional[str] = None

	@field_validator("sex")
	@classmethod
	def _normalize_sex(cls, value: str) -> str:
		normalized = value.strip().lower()
		if normalized not in {"male", "female", "other"}:
			raise ValueError("sex must be one of male, female, other")
		return normalized

	@model_validator(mode="after")
	def _check_minimum_inputs(self) -> "PatientAssessment":
		if not self.vitals and not self.asha_checklist and not self.symptom_text:
			raise ValueError("At least one of vitals, asha_checklist, symptom_text required")
		return self
