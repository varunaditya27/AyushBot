from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("langgraph")

from fastapi.testclient import TestClient

from backend.api import main as api_main
from backend.security.auth import AuthUser, Role


@pytest.mark.integration
def test_pipeline_smoke(monkeypatch, tmp_path):
    monkeypatch.setenv("AYUSHBOT_DB_PATH", str(tmp_path / "test.db"))

    async def _auth_override(*_args, **_kwargs):
        return AuthUser(user_id="asha", role=Role.ASHA_WORKER)

    api_main.app.dependency_overrides[api_main.authenticate] = _auth_override

    def _run_stub(state):
        state["risk_level"] = "LOW"
        state["risk_confidence"] = 0.5
        state["action_plan"] = {"urgency": "ROUTINE", "immediate_actions": []}
        state["asha_output_text"] = "ok"
        return state

    monkeypatch.setattr(api_main, "run_pipeline", _run_stub, raising=False)

    client = TestClient(api_main.app)
    response = client.post(
        "/api/v1/triage/assess",
        json={
            "age_months": 18,
            "sex": "female",
            "village_id": "village-1",
            "asha_id": "asha-1",
            "symptom_text": "fever",
        },
    )
    assert response.status_code == 200
