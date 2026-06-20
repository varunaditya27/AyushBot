from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from backend.api import main as api_main
from backend.api.routes import triage
from backend.db.migrate import upgrade
from backend.db.session import reset_engine
from backend.security import auth
from backend.security.auth import AuthUser, Role


@pytest.mark.integration
def test_pipeline_smoke(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("AYUSHBOT_DB_PATH", str(db_path))
    reset_engine()
    upgrade(f"sqlite:///{db_path}")

    async def _auth_override():
        return AuthUser(user_id="asha-1", role=Role.ASHA_WORKER)

    api_main.app.dependency_overrides[auth.authenticate] = _auth_override

    def _run_stub(state):
        state["risk_level"] = "LOW"
        state["risk_confidence"] = 0.5
        state["action_plan"] = {"urgency": "ROUTINE", "immediate_actions": []}
        state["asha_output_text"] = "ok"
        return state

    monkeypatch.setattr(triage, "run_pipeline", _run_stub)

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
    api_main.app.dependency_overrides.clear()
    reset_engine()
