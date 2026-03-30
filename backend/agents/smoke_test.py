"""Smoke test for Phase 4 agent pipeline."""

from __future__ import annotations

import sys

from backend.agents.orchestrator import run_pipeline
from backend.agents.schemas.patient_assessment import PatientAssessment
from backend.agents.state import state_from_assessment


def main() -> int:
    assessment = PatientAssessment(
        patient_id="demo",
        patient_name="Demo",
        age_months=24,
        sex="male",
        village_id="village-1",
        asha_id="asha-1",
        symptom_text="cough and fever",
    )
    state = state_from_assessment(assessment)
    result = run_pipeline(state)
    print({"risk_level": result.get("risk_level"), "action_plan": bool(result.get("action_plan"))})
    return 0


if __name__ == "__main__":
    sys.exit(main())
