from __future__ import annotations

import pytest

from backend.agents import agent_language
from backend.agents.agent_language import LocalizationResult
from backend.config import clear_settings_cache


@pytest.fixture(autouse=True)
def _clear_config():
	clear_settings_cache()
	yield
	clear_settings_cache()


def _state(**updates):
	state = {
		"asha_input_text": "fever and cough",
		"input_language": "en",
		"action_plan": {
			"primary_diagnosis": "Synthetic condition",
			"immediate_actions": ["Refer to medical officer"],
		},
		"errors": [],
	}
	state.update(updates)
	return state


def test_noop_provider_preserves_text_and_structured_fields(tmp_path, monkeypatch):
	config = tmp_path / "config.yaml"
	config.write_text(
		"""
language:
  provider: noop
  enabled_languages: [en, hi]
  default_language: en
""",
		encoding="utf-8",
	)
	monkeypatch.setenv("AYUSHBOT_CONFIG", str(config))

	state = _state(input_language="en")
	before_action_plan = dict(state["action_plan"])
	result = agent_language.preprocess_input(state)
	result = agent_language.postprocess_output(result)

	assert result["translated_symptoms"] == ["fever and cough"]
	assert result["asha_output_text"] == "Synthetic condition"
	assert result["action_plan"] == before_action_plan
	assert result["localization"]["input"]["provider"] == "noop"
	assert result["localization"]["output"]["confidence"] == 1.0


def test_unsupported_language_is_flagged_and_falls_back(tmp_path, monkeypatch):
	config = tmp_path / "config.yaml"
	config.write_text(
		"""
language:
  provider: noop
  enabled_languages: [en]
  default_language: en
""",
		encoding="utf-8",
	)
	monkeypatch.setenv("AYUSHBOT_CONFIG", str(config))

	result = agent_language.preprocess_input(_state(input_language="zz"))

	assert result["translated_symptoms"] == ["fever and cough"]
	assert result["errors"][0]["code"] == "UNSUPPORTED_LANGUAGE"


class _FailingProvider:
	name = "failing"

	def localize(self, text: str, *, source_language: str, target_language: str):
		raise RuntimeError("synthetic provider failure")


def test_provider_failure_preserves_text_and_records_error(monkeypatch):
	monkeypatch.setattr(agent_language, "get_provider", lambda: _FailingProvider())

	result = agent_language.preprocess_input(_state())

	assert result["translated_symptoms"] == ["fever and cough"]
	assert any(error["code"] == "RuntimeError" for error in result["errors"])
	assert result["localization"]["input"]["provider"] == "noop"


class _LowConfidenceProvider:
	name = "low-confidence"

	def localize(self, text: str, *, source_language: str, target_language: str):
		return LocalizationResult(
			text=f"localized:{text}",
			source_language=source_language,
			target_language=target_language,
			confidence=0.4,
			provider=self.name,
			limitations=["synthetic low confidence"],
		)


def test_low_confidence_localization_requires_review(monkeypatch):
	monkeypatch.setattr(agent_language, "get_provider", lambda: _LowConfidenceProvider())

	result = agent_language.postprocess_output(_state(input_language="hi"))

	assert result["asha_output_text"].startswith("localized:")
	assert result["localization"]["output"]["human_review_required"] is True
	assert result["errors"][-1]["code"] == "LOCALIZATION_REVIEW_REQUIRED"
