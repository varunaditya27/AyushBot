from __future__ import annotations

from backend.agents.agent_referral import run_referral


def test_critical_case_emergency_referral(sample_patient_state, sample_facility_db, monkeypatch):
    monkeypatch.setenv("AYUSHBOT_DB_PATH", sample_facility_db["db_path"])
    sample_patient_state["risk_level"] = "CRITICAL"
    result = run_referral(sample_patient_state)
    assert result.get("action_plan") is not None
    assert result["action_plan"]["urgency"] == "IMMEDIATE"
