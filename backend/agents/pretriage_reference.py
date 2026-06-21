"""Validated versioned references for deterministic pre-triage."""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReferenceModel(BaseModel):
	model_config = ConfigDict(extra="forbid")


class VitalBounds(ReferenceModel):
	minimum: float | None = None
	maximum: float | None = None


class SignalQualityConfig(ReferenceModel):
	window_readings: int = Field(ge=2)
	window_seconds: int = Field(ge=1)
	spo2_cv_max: float = Field(gt=0)
	min_quality_score: float | None = Field(default=None, ge=0, le=1)
	bounds: dict[str, VitalBounds]


class RuleCondition(ReferenceModel):
	field: str
	operator: Literal["eq", "lt", "lte", "gt", "gte", "truthy"]
	value: float | str | bool | None = None


class ClinicalRule(ReferenceModel):
	id: str
	label: str
	risk: Literal["MEDIUM", "HIGH", "CRITICAL"]
	enabled: bool = True
	conditions: list[RuleCondition] = Field(min_length=1)
	source: str
	medical_review_required: bool = True


class PreTriageRuleset(ReferenceModel):
	schema_version: int = Field(ge=1)
	ruleset_version: str
	status: Literal["DRAFT", "MEDICALLY_REVIEWED"]
	sources: list[str]
	signal_quality: SignalQualityConfig
	rules: list[ClinicalRule]

	@model_validator(mode="after")
	def _unique_rule_ids(self) -> "PreTriageRuleset":
		ids = [rule.id for rule in self.rules]
		if len(ids) != len(set(ids)):
			raise ValueError("Rule IDs must be unique")
		return self


class GrowthRow(ReferenceModel):
	sex: Literal["male", "female"]
	age_months: int = Field(ge=0)
	l_value: float = Field(alias="l")
	m_value: float = Field(gt=0, alias="m")
	s_value: float = Field(gt=0, alias="s")


class GrowthReference(ReferenceModel):
	schema_version: int = Field(ge=1)
	reference_version: str
	source: str
	status: Literal["TEMPLATE", "MEDICALLY_REVIEWED"]
	rows: list[GrowthRow]

	@model_validator(mode="after")
	def _unique_rows(self) -> "GrowthReference":
		keys = [(row.sex, row.age_months) for row in self.rows]
		if len(keys) != len(set(keys)):
			raise ValueError("Growth reference has duplicate sex/age rows")
		return self

	def weight_for_age_zscore(
		self, *, sex: str, age_months: int, weight_kg: float
	) -> float | None:
		if sex not in {"male", "female"} or weight_kg <= 0:
			return None
		rows = sorted(
			(row for row in self.rows if row.sex == sex),
			key=lambda row: row.age_months,
		)
		if not rows or age_months < rows[0].age_months or age_months > rows[-1].age_months:
			return None
		lower = max(row for row in rows if row.age_months <= age_months)
		upper = min(row for row in rows if row.age_months >= age_months)
		if lower.age_months == upper.age_months:
			l_value, m_value, s_value = (
				lower.l_value,
				lower.m_value,
				lower.s_value,
			)
		else:
			fraction = (age_months - lower.age_months) / (
				upper.age_months - lower.age_months
			)
			l_value = lower.l_value + fraction * (
				upper.l_value - lower.l_value
			)
			m_value = lower.m_value + fraction * (
				upper.m_value - lower.m_value
			)
			s_value = lower.s_value + fraction * (
				upper.s_value - lower.s_value
			)
		if l_value == 0:
			return math.log(weight_kg / m_value) / s_value
		return ((weight_kg / m_value) ** l_value - 1) / (l_value * s_value)


def _load_json(path: Path) -> dict[str, Any]:
	if not path.is_file():
		raise FileNotFoundError(f"Reference file not found: {path}")
	data = json.loads(path.read_text(encoding="utf-8"))
	if not isinstance(data, dict):
		raise ValueError(f"Reference root must be an object: {path}")
	return data


@lru_cache(maxsize=8)
def load_ruleset(path: Path) -> PreTriageRuleset:
	return PreTriageRuleset.model_validate(_load_json(path))


@lru_cache(maxsize=8)
def load_growth_reference(path: Path) -> GrowthReference:
	return GrowthReference.model_validate(_load_json(path))


def load_ruleset_with_policy(
	path: Path,
	*,
	allow_draft_rules: bool,
	require_reviewed_rules: bool,
) -> PreTriageRuleset:
	ruleset = load_ruleset(path)
	if require_reviewed_rules and ruleset.status != "MEDICALLY_REVIEWED":
		raise RuntimeError("Pre-triage ruleset is not medically reviewed")
	if not allow_draft_rules and ruleset.status != "MEDICALLY_REVIEWED":
		raise RuntimeError("Draft pre-triage rules are not allowed")
	if any(rule.medical_review_required for rule in ruleset.rules if rule.enabled):
		if require_reviewed_rules or not allow_draft_rules:
			raise RuntimeError(
				"Pre-triage rules contain values awaiting medical review"
			)
	return ruleset


def load_growth_reference_with_policy(
	path: Path,
	*,
	allow_draft_rules: bool,
	require_reviewed_rules: bool,
) -> GrowthReference:
	growth = load_growth_reference(path)
	if require_reviewed_rules and growth.status != "MEDICALLY_REVIEWED":
		raise RuntimeError("WHO weight-for-age reference is not medically reviewed")
	if not allow_draft_rules and growth.status != "MEDICALLY_REVIEWED":
		raise RuntimeError("Draft WHO weight-for-age reference is not allowed")
	if require_reviewed_rules and not growth.rows:
		raise RuntimeError("WHO weight-for-age reference has no reviewed rows")
	return growth


def clear_reference_caches() -> None:
	load_ruleset.cache_clear()
	load_growth_reference.cache_clear()
