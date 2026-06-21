"""Language localization provider interface for AyushBot.

The default provider is intentionally a no-op for local showcase development.
It preserves text and structured clinical fields while making the limitation
explicit in state metadata.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from backend.agents.state import PatientState, add_pipeline_error
from backend.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LocalizationResult:
	text: str
	source_language: str
	target_language: str
	confidence: float
	provider: str
	limitations: list[str]
	human_review_required: bool = False


class LocalizationProvider(Protocol):
	name: str

	def localize(
		self, text: str, *, source_language: str, target_language: str
	) -> LocalizationResult:
		...


class NoOpLocalizationProvider:
	name = "noop"

	def localize(
		self, text: str, *, source_language: str, target_language: str
	) -> LocalizationResult:
		return LocalizationResult(
			text=text,
			source_language=source_language,
			target_language=target_language,
			confidence=1.0 if source_language == target_language else 0.0,
			provider=self.name,
			limitations=(
				["No translation performed; text preserved verbatim."]
				if source_language != target_language
				else ["No-op provider used; structured fields preserved."]
			),
			human_review_required=source_language != target_language,
		)


def get_provider() -> LocalizationProvider:
	settings = get_settings().language
	if settings.provider == "noop":
		return NoOpLocalizationProvider()
	raise RuntimeError(f"Unsupported localization provider: {settings.provider}")


def _target_language(state: PatientState) -> str:
	return state.get("input_language") or get_settings().language.default_language


def _apply_result(state: PatientState, result: LocalizationResult, stage: str) -> None:
	review_threshold = get_settings().language.require_human_review_below_confidence
	human_review_required = (
		result.human_review_required or result.confidence < review_threshold
	)
	state.setdefault("localization", {})[stage] = {
		"provider": result.provider,
		"source_language": result.source_language,
		"target_language": result.target_language,
		"confidence": result.confidence,
		"limitations": result.limitations,
		"human_review_required": human_review_required,
	}
	if human_review_required:
		add_pipeline_error(
			state,
			stage=f"language_{stage}",
			code="LOCALIZATION_REVIEW_REQUIRED",
			message="Localization provider could not guarantee medical translation quality.",
		)


def preprocess_input(state: PatientState) -> PatientState:
	settings = get_settings().language
	language = _target_language(state)
	if language not in settings.enabled_languages:
		add_pipeline_error(
			state,
			stage="language_in",
			code="UNSUPPORTED_LANGUAGE",
			message=f"Unsupported language: {language}",
		)
		language = settings.default_language

	symptom_text = state.get("asha_input_text") or ""
	try:
		result = get_provider().localize(
			symptom_text,
			source_language=language,
			target_language="en",
		)
	except Exception as exc:
		logger.exception("Input localization failed")
		add_pipeline_error(
			state,
			stage="language_in",
			code=type(exc).__name__,
			message="Input localization failed; original text preserved.",
		)
		result = NoOpLocalizationProvider().localize(
			symptom_text,
			source_language=language,
			target_language="en",
		)

	_apply_result(state, result, "input")
	state["translated_symptoms"] = [result.text] if result.text else []
	state["intent"] = "SYMPTOM_REPORT"
	state["extracted_entities"] = []
	return state


def _clinical_summary(state: PatientState) -> str:
	action_plan = state.get("action_plan") or {}
	summary = action_plan.get("primary_diagnosis") or ""
	if action_plan.get("immediate_actions"):
		summary = summary or "; ".join(action_plan.get("immediate_actions"))
	return summary or "Refer to medical officer"


def postprocess_output(state: PatientState) -> PatientState:
	settings = get_settings().language
	target = _target_language(state)
	if target not in settings.enabled_languages:
		add_pipeline_error(
			state,
			stage="language_out",
			code="UNSUPPORTED_LANGUAGE",
			message=f"Unsupported language: {target}",
		)
		target = settings.default_language

	summary = _clinical_summary(state)
	try:
		result = get_provider().localize(
			summary,
			source_language="en",
			target_language=target,
		)
	except Exception as exc:
		logger.exception("Output localization failed")
		add_pipeline_error(
			state,
			stage="language_out",
			code=type(exc).__name__,
			message="Output localization failed; English text preserved.",
		)
		result = NoOpLocalizationProvider().localize(
			summary,
			source_language="en",
			target_language=target,
		)

	_apply_result(state, result, "output")
	state["asha_output_text"] = result.text
	state["asha_output_audio"] = None
	return state
