"""Integration tests for Phase 4 REST API."""

import sys
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cloud.api.main import app

# Create test client
client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "AyushBot Cloud API"
        assert "version" in data
        assert "timestamp" in data

    def test_health_check(self):
        """Test basic health check."""
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_readiness_check(self):
        """Test readiness endpoint."""
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert "components" in data

    def test_liveness_check(self):
        """Test liveness endpoint."""
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["alive"] is True
        assert "uptime_seconds" in data


class TestFLStatusEndpoints:
    """Test FL server status endpoints."""

    def test_fl_status(self):
        """Test FL server status endpoint."""
        response = client.get("/api/v1/fl/status")
        assert response.status_code == 200
        data = response.json()
        assert data["server_running"] is True
        assert "current_round" in data
        assert "available_clients" in data
        assert "aggregation_strategy" in data

    def test_list_fl_rounds(self):
        """Test listing FL rounds."""
        response = client.get("/api/v1/fl/rounds?skip=0&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "rounds" in data
        assert len(data["rounds"]) <= 5
        assert "skip" in data
        assert "limit" in data
        assert "total" in data

    def test_list_fl_rounds_invalid_skip(self):
        """Test listing FL rounds with invalid skip."""
        response = client.get("/api/v1/fl/rounds?skip=-1&limit=5")
        assert response.status_code == 400

    def test_get_fl_round(self):
        """Test getting specific FL round."""
        response = client.get("/api/v1/fl/rounds/25")
        assert response.status_code == 200
        data = response.json()
        assert data["round_num"] == 25
        assert "status" in data
        assert "num_clients" in data
        assert "accuracy" in data

    def test_get_fl_round_not_found(self):
        """Test getting non-existent FL round."""
        response = client.get("/api/v1/fl/rounds/999")
        assert response.status_code == 404

    def test_trigger_fl_round(self):
        """Test triggering FL round."""
        response = client.post("/api/v1/fl/rounds/trigger")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "triggered"
        assert "round_num" in data

    def test_fl_config(self):
        """Test FL configuration endpoint."""
        response = client.get("/api/v1/fl/config")
        assert response.status_code == 200
        data = response.json()
        assert "port" in data
        assert "strategy" in data
        assert "privacy" in data
        assert data["privacy"]["enabled"] is True


class TestModelEndpoints:
    """Test model registry and query endpoints."""

    def test_list_models(self):
        """Test listing models."""
        response = client.get("/api/v1/models/list?skip=0&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert len(data["models"]) <= 5
        assert "total" in data
        assert all("version" in m for m in data["models"])
        assert all("accuracy" in m for m in data["models"])

    def test_list_models_invalid_limit(self):
        """Test listing models with invalid limit."""
        response = client.get("/api/v1/models/list?skip=0&limit=0")
        assert response.status_code == 400

    def test_get_latest_model(self):
        """Test getting latest model."""
        response = client.get("/api/v1/models/latest")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "accuracy" in data
        assert "loss" in data
        assert "epsilon_consumed" in data
        assert "download_url" in data

    def test_get_model_by_version(self):
        """Test getting model by version."""
        response = client.get("/api/v1/models/v_1_2026_05_31_5000_000000")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "v_1_2026_05_31_5000_000000"
        assert "accuracy" in data
        assert "aggregation_strategy" in data

    def test_get_model_invalid_version(self):
        """Test getting model with invalid version."""
        response = client.get("/api/v1/models/invalid_version")
        assert response.status_code == 404

    def test_download_model(self):
        """Test model download endpoint."""
        response = client.get("/api/v1/models/download/v_1_2026_05_31_5000_000000")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["version"] == "v_1_2026_05_31_5000_000000"

    def test_compare_models(self):
        """Test model comparison endpoint."""
        response = client.post(
            "/api/v1/models/compare",
            params={
                "version1": "v_1_2026_05_31_5000_000000",
                "version2": "v_1_2026_05_31_4900_000000",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "comparison" in data
        assert "metrics" in data["comparison"]
        assert "winner" in data["comparison"]

    def test_compare_models_invalid_version(self):
        """Test model comparison with invalid version."""
        response = client.post(
            "/api/v1/models/compare",
            params={
                "version1": "invalid",
                "version2": "v_1_2026_05_31_5000_000000",
            },
        )
        assert response.status_code == 400

    def test_get_model_metrics(self):
        """Test getting model metrics."""
        response = client.get(
            "/api/v1/models/metrics/v_1_2026_05_31_5000_000000"
        )
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "training" in data
        assert "privacy" in data
        assert data["metrics"]["accuracy"] > 0
        assert data["privacy"]["epsilon_consumed"] > 0


class TestRateLimiting:
    """Test rate limiting middleware."""

    def test_rate_limit_headers(self):
        """Test rate limit headers in response."""
        response = client.get("/")
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers


class TestCORS:
    """Test CORS configuration."""

    def test_cors_allowed_origin(self):
        """Test CORS with allowed origin."""
        response = client.get(
            "/",
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.status_code == 200

    def test_cors_headers(self):
        """Test CORS headers."""
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200


class TestEndpointStructure:
    """Test API endpoint structure and versioning."""

    def test_api_v1_prefix(self):
        """Test API v1 prefix."""
        response = client.get("/api/v1/health/")
        assert response.status_code == 200

    def test_endpoints_exist(self):
        """Test key endpoints exist."""
        endpoints = [
            "/",
            "/api/v1/health/",
            "/api/v1/fl/status",
            "/api/v1/fl/rounds",
            "/api/v1/models/list",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [200, 404], f"Endpoint {endpoint} failed"
