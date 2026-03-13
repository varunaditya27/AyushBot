# =============================================================================
# AyushBot Backend — Patient Assessment Schema (Agent 1 Input Contract)
# =============================================================================
#
# PURPOSE:
#   Pydantic model defining the structured input for a patient assessment
#   request. This schema validates the data received from the ASHA's Android
#   phone before it enters the agent pipeline.
#
# FIELDS:
#   - patient_id: Optional[str] — ABHA health ID or auto-generated UUID
#   - patient_name: str — Patient's name (local language, for display only)
#   - age_months: int — Age in months (validated: 0-600 range)
#   - sex: Literal["male", "female", "other"]
#   - weight_kg: Optional[float] — From HX711 sensor (None if sensor unavailable)
#   - village_id: str — Geographic identifier for referral routing
#   - asha_id: str — Unique ASHA worker identifier
#
#   - vitals: VitalsSnapshot sub-schema:
#       - spo2: Optional[int] — Peripheral oxygen saturation (0-100%)
#       - heart_rate: Optional[int] — Beats per minute
#       - temperature_celsius: Optional[float] — Body temperature
#       - weight_grams: Optional[int] — Weight in grams (alternative to weight_kg)
#       - measurement_timestamp: datetime — When vitals were captured
#       - signal_quality: dict — Per-sensor quality indicators
#
#   - asha_checklist: dict — Structured categorical inputs:
#       - is_breastfeeding: Optional[bool]
#       - chest_indrawing: Optional[bool]
#       - is_lethargic: Optional[bool]
#       - visible_wasting: Optional[bool]
#       - edema: Optional[bool]
#       - diarrhea_present: Optional[bool]
#       - vomiting: Optional[bool]
#       - convulsions: Optional[bool]
#       (extensible with additional IMCI checklist items)
#
#   - symptom_text: str — Free-text or voice-transcribed symptom description
#     in the ASHA's local language
#   - input_language: str — ISO 639-1 language code (e.g., "hi", "bn", "ta")
#
# VALIDATION RULES:
#   - age_months must be >= 0 and <= 600 (0-50 years, mostly pediatric)
#   - spo2 must be between 0 and 100 if provided
#   - heart_rate must be between 20 and 300 if provided
#   - temperature must be between 25.0 and 45.0 if provided
#   - asha_id and village_id are required (non-empty strings)
#   - At least one of (vitals, asha_checklist, symptom_text) must be present
# =============================================================================
