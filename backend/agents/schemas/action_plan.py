"""AyushBot Backend — Action Plan Schema (Agent 3 Output Contract)."""

from __future__ import annotations

from typing import List, Literal, Optional, Tuple

from pydantic import BaseModel, Field, model_validator


class ReferralDetails(BaseModel):
	facility_name: str
	facility_type: Literal["PHC", "CHC", "DH", "HOME_MANAGEMENT"]
	address: str
	distance_km: float = Field(..., ge=0.0)
	travel_time_minutes: int = Field(..., ge=0)
	route_description: str
	phone_number: Optional[str] = None
	facility_coordinates: Optional[Tuple[float, float]] = None


class Medication(BaseModel):
	drug_name: str
	dose_mg: float = Field(..., gt=0)
	dose_per_kg: float = Field(..., gt=0)
	frequency: str
	duration_days: int = Field(..., ge=1)
	route: Literal["ORAL", "TOPICAL", "IM", "IV"]
	formulation: str
	instructions: str
	source_citation: str
	contraindications_checked: List[str] = Field(default_factory=list)


class FollowUp(BaseModel):
	follow_up_date: Optional[str] = None
	follow_up_actions: List[str] = Field(default_factory=list)
	danger_signs_to_watch: List[str] = Field(default_factory=list)


class ReferralSlip(BaseModel):
	patient_name: str
	patient_age: str
	asha_name: str
	date: str
	primary_complaint: str
	vital_signs_summary: str
	provisional_diagnosis: str
	medications_given: List[str]
	referral_reason: str
	destination_facility: str


class ActionPlan(BaseModel):
	urgency: Literal["IMMEDIATE", "WITHIN_24H", "WITHIN_WEEK", "ROUTINE"]
	referral: Optional[ReferralDetails] = None
	medications: List[Medication] = Field(default_factory=list)
	immediate_actions: List[str] = Field(default_factory=list)
	follow_up: Optional[FollowUp] = None
	referral_slip: Optional[ReferralSlip] = None
	primary_diagnosis: str = ""
	source_guideline: str = ""

	@model_validator(mode="after")
	def _check_minimum_fields(self) -> "ActionPlan":
		if not self.referral and not self.medications and not self.immediate_actions:
			raise ValueError("ActionPlan must include referral, medications, or actions")
		if self.urgency == "IMMEDIATE" and self.referral:
			if self.referral.facility_type == "HOME_MANAGEMENT":
				raise ValueError("IMMEDIATE urgency cannot be HOME_MANAGEMENT")
		return self
