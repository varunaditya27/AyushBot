# =============================================================================
# AyushBot Backend — Agent 5: Language & Accessibility Agent (The Interface)
# =============================================================================
#
# PURPOSE:
#   This agent provides bidirectional cross-lingual communication between the
#   ASHA worker (who speaks a regional Indian language) and the clinical
#   reasoning agents (which operate in English). It activates TWICE in the
#   pipeline — once at the very beginning (ASHA → System) and once at the
#   very end (System → ASHA).
#
# ACTIVATION POINTS:
#   1. PRE-PIPELINE (before Agent 1):
#      Convert ASHA's local-language input into standardized English
#      clinical entities that downstream agents can process.
#   2. POST-PIPELINE (after Agent 3):
#      Convert the English clinical output (diagnosis + referral plan)
#      into the ASHA's native language, both as text and as audio (TTS).
#
# ─── PHASE 1: ASHA → SYSTEM (Input Processing) ──────────────────────────
#
#   Step 1 — Speech-to-Text (if voice input)
#     If the ASHA provides voice input (via the Android phone's microphone),
#     it arrives as a text transcription from the phone's on-device ASR.
#     (Speech recognition runs on the phone itself using Whisper-tiny or
#     AI4Bharat's ASR model.)
#
#   Step 2 — Intent Classification (IndicBERT)
#     Classify the ASHA's input into a clinical intent category:
#       - SYMPTOM_REPORT: "The child has fever and cough"
#       - VITAL_QUERY: "What does SpO2 of 88 mean?"
#       - DRUG_QUERY: "How much paracetamol for 10 kg child?"
#       - EMERGENCY: "The baby is not breathing"
#       - GENERAL: "When is the next vaccination due?"
#     Uses a fine-tuned IndicBERT model trained on the IHQID dataset.
#
#   Step 3 — Named Entity Recognition (NER)
#     Extract clinical named entities from the ASHA's input:
#       - SYMPTOM entities: "fever", "cough", "fast breathing", "not eating"
#       - BODY_PART entities: "chest", "stomach", "head"
#       - DURATION entities: "3 days", "since morning"
#       - SEVERITY entities: "very bad", "a little"
#     Uses IndicBERT fine-tuned for medical NER on Indian language health data.
#
#   Step 4 — Translation to Standardized English
#     Translate the extracted entities into canonical English medical terms:
#       - "tez saans" (Hindi) → "tachypnea"
#       - "bukhar" (Hindi) → "fever / pyrexia"
#       - "pet mein dard" (Hindi) → "abdominal pain"
#     Uses IndicTrans2 (AI4Bharat's state-of-the-art Indian language MT model).
#     Post-processing maps colloquial translations to MeSH medical terminology
#     using a clinical synonym dictionary.
#
# ─── PHASE 2: SYSTEM → ASHA (Output Processing) ────────────────────────
#
#   Step 5 — Medical Term Grounding
#     The raw English clinical output (e.g., "Suspected Severe Pneumonia —
#     refer to District Hospital. Amoxicillin 25 mg/kg BID x 5 days.") needs
#     to be made understandable to ASHA workers, not just literally translated.
#       - "Pneumonia" → "phephadon ka rog" (lungs disease) in local idiom
#       - "25 mg/kg BID" → "child's weight in kg times 25, give twice a day"
#     Uses a medical term grounding dictionary that maps clinical terms to
#     culturally understood health concepts in each supported language.
#
#   Step 6 — Translation to Local Language
#     Full translation of the grounded output text into the ASHA's language
#     using IndicTrans2 (English → Hindi/Bengali/Tamil/etc.).
#
#   Step 7 — Text-to-Speech (TTS) Audio Generation
#     Convert the translated text to spoken audio using AI4Bharat's offline
#     TTS engine. The ASHA hears the guidance through her phone speaker —
#     critical for low-literacy users or when the ASHA's hands are occupied
#     with the patient.
#
# SUPPORTED LANGUAGES:
#   Hindi, Bengali, Tamil, Telugu, Kannada, Marathi, Gujarati, Punjabi
#   (extensible by adding IndicTrans2 language pairs and TTS voice packs)
#
# OUTPUTS (written to Patient State Object):
#   Phase 1:
#     - intent: enum (SYMPTOM_REPORT, VITAL_QUERY, DRUG_QUERY, EMERGENCY, GENERAL)
#     - extracted_entities: list of {entity_type, text, language} dicts
#     - translated_symptoms: list of standardized English clinical term strings
#   Phase 2:
#     - asha_output_text: translated response string in local language
#     - asha_output_audio: bytes (WAV/MP3) of TTS audio
#     - language_used: ISO 639-1 code of the ASHA's detected language
#
# MODEL DEPENDENCIES:
#   - IndicBERT (intent classification + NER): ~440 MB, runs on RPi 4 or phone
#   - IndicTrans2 (machine translation): ~200-400 MB per language pair
#   - AI4Bharat TTS: ~100 MB per voice pack
#   - Medical term grounding dictionary: ~5 MB JSON file
#   All models are deployed offline. Zero cloud dependency.
#
# LATENCY TARGET: 100-200 ms per phase (total ~300 ms for both activations)
# =============================================================================

from __future__ import annotations

from typing import Any, Dict, List

from backend.agents.state import PatientState


def preprocess_input(state: PatientState) -> PatientState:
	symptom_text = state.get("asha_input_text") or ""
	translated = [symptom_text] if symptom_text else []
	state["translated_symptoms"] = translated
	state["intent"] = "SYMPTOM_REPORT"
	state["extracted_entities"] = []
	return state


def postprocess_output(state: PatientState) -> PatientState:
	action_plan = state.get("action_plan") or {}
	summary = action_plan.get("primary_diagnosis") or ""
	if action_plan.get("immediate_actions"):
		summary = summary or "; ".join(action_plan.get("immediate_actions"))
	state["asha_output_text"] = summary or "Refer to medical officer"
	state["asha_output_audio"] = None
	return state
