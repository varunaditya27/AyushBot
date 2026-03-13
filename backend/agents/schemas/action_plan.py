# =============================================================================
# AyushBot Backend — Action Plan Schema (Agent 3 Output Contract)
# =============================================================================
#
# PURPOSE:
#   Pydantic model defining the structured output of Agent 3 (Referral
#   Planning Agent). This schema describes the complete actionable plan
#   that the ASHA worker receives — including where to refer, what medicine
#   to give, and what immediate actions to take.
#
# FIELDS:
#
#   ActionPlan (top-level response):
#     - urgency: Literal["IMMEDIATE", "WITHIN_24H", "WITHIN_WEEK", "ROUTINE"]
#     - referral: ReferralDetails — Where to send the patient
#     - medications: list[Medication] — What drugs to administer/prescribe
#     - immediate_actions: list[str] — Things to do right now
#       (e.g., "Start ORS immediately", "Keep child warm", "Monitor breathing")
#     - follow_up: FollowUp — When and how to follow up
#     - referral_slip: ReferralSlip — Data for generating the printable slip
#     - primary_diagnosis: str — The condition driving this plan
#     - source_guideline: str — Which clinical guideline this plan is based on
#
#   ReferralDetails:
#     - facility_name: str — Name of the referral destination
#     - facility_type: Literal["PHC", "CHC", "DH", "HOME_MANAGEMENT"]
#     - address: str — Physical address or landmark description
#     - distance_km: float — Road distance from current location
#     - travel_time_minutes: int — Estimated travel time (from Dijkstra routing)
#     - route_description: str — Brief route description for the ASHA
#     - phone_number: Optional[str] — Facility contact number
#     - facility_coordinates: Optional[tuple[float, float]] — Lat/Lng
#
#   Medication:
#     - drug_name: str — Generic drug name (e.g., "Amoxicillin")
#     - dose_mg: float — Calculated dose in milligrams
#     - dose_per_kg: float — The mg/kg ratio used for the calculation
#     - frequency: str — How often (e.g., "Twice daily", "Every 8 hours")
#     - duration_days: int — How many days to continue
#     - route: Literal["ORAL", "TOPICAL", "IM", "IV"]
#     - formulation: str — Available form (e.g., "Syrup 125mg/5ml", "Tablet 250mg")
#     - instructions: str — ASHA-friendly plain language instructions
#     - source_citation: str — Which guideline specifies this dosage
#     - contraindications_checked: list[str] — What was checked (age, weight, allergies)
#
#   FollowUp:
#     - follow_up_date: Optional[str] — Relative ("After 3 days") or absolute date
#     - follow_up_actions: list[str] — What to check on follow-up
#     - danger_signs_to_watch: list[str] — Signs that warrant immediate re-referral
#       (e.g., "Child stops eating", "Breathing gets faster", "Fever returns")
#
#   ReferralSlip:
#     - patient_name: str
#     - patient_age: str
#     - asha_name: str
#     - date: str
#     - primary_complaint: str
#     - vital_signs_summary: str
#     - provisional_diagnosis: str
#     - medications_given: list[str]
#     - referral_reason: str
#     - destination_facility: str
#     (This data is used to generate a PDF or WhatsApp-shareable image)
#
# VALIDATION RULES:
#   - urgency IMMEDIATE requires facility_type to be CHC or DH (not HOME)
#   - dose_mg must be > 0 if a medication is listed
#   - dose_mg must not exceed known safe maximum for the drug + age group
#   - At least one of (referral, medications, immediate_actions) must be present
#   - All drug dosages must include a source_citation (no unattributed dosages)
# =============================================================================
