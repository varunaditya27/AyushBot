"""Tests for Phase 4.2 (Authentication) and 4.3 (Error Handling)."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cloud.api.main import app
from cloud.api.exceptions import (
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    BadRequestError,
)

client = TestClient(app)

# Valid API keys
ADMIN_KEY = "admin-key-12345"
OFFICER_KEY = "officer-key-67890"
READER_KEY = "read-only-key-11111"
INVALID_KEY = "invalid-key-99999"


class TestAuthentication:
    """Test authentication mechanisms."""

    def test_health_check_no_auth(self):
        """Health endpoints should not require authentication."""
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_fl_status_with_valid_admin_key(self):
        """FL status should be accessible with valid admin key."""
        response = client.get(
            "/api/v1/fl/status",
            headers={"Authorization": f"Bearer {ADMIN_KEY}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["server_running"] is True

    def test_fl_status_with_valid_officer_key(self):
        """FL status should be accessible with officer key."""
        response = client.get(
            "/api/v1/fl/status",
            headers={"Authorization": f"Bearer {OFFICER_KEY}"},
        )
        assert response.status_code == 200

    def test_fl_status_with_invalid_key(self):
        """FL status with invalid key should return 401."""
        response = client.get(
            "/api/v1/fl/status",
            headers={"Authorization": f"Bearer {INVALID_KEY}"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "UNAUTHORIZED"
        assert "request_id" in data

    def test_fl_status_without_auth(self):
        """FL status without authorization header should return 401."""
        response = client.get("/api/v1/fl/status")
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "UNAUTHORIZED"

    def test_malformed_auth_header(self):
        """Malformed authorization header should return 401."""
        response = client.get(
            "/api/v1/fl/status",
            headers={"Authorization": f"NotBearer {ADMIN_KEY}"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "Invalid authorization format" in data["error"]

    def test_missing_bearer_prefix(self):
        """Missing Bearer prefix should return 401."""
        response = client.get(
            "/api/v1/fl/status",
            headers={"Authorization": ADMIN_KEY},
        )
        assert response.status_code == 401


class TestErrorHandling:
    """Test error handling and structured responses."""

    def test_not_found_error(self):
        """Test 404 error response format."""
        response = client.get(
            "/api/v1/fl/rounds/9999",
            headers={"Authorization": f"Bearer {ADMIN_KEY}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "error_code" in data
        assert data["error_code"] == "NOT_FOUND"
        assert "request_id" in data
        assert "timestamp" in data
        assert "status_code" in data

    def test_bad_request_error(self):
        """Test 400 error response format."""
        response = client.get(
            "/api/v1/fl/rounds?skip=-1&limit=10",
            headers={"Authorization": f"Bearer {ADMIN_KEY}"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "BAD_REQUEST"
        assert data["status_code"] == 400
        assert "request_id" in data

    def test_unauthorized_error_response(self):
        """Test 401 error response format."""
        response = client.get(
            "/api/v1/fl/status",
            headers={"Authorization": "Bearer invalid-key"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "UNAUTHORIZED"
        assert data["status_code"] == 401
        assert "request_id" in data
        assert "timestamp" in data

    def test_error_response_has_request_id(self):
        """All error responses should include request_id."""
        response = client.get(
            "/api/v1/fl/rounds/999",
            headers={"Authorization": f"Bearer {ADMIN_KEY}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert "request_id" in data
        assert len(data["request_id"]) > 0

    def test_error_response_has_timestamp(self):
        """All error responses should include timestamp."""
        response = client.get(
            "/api/v1/fl/rounds/999",
            headers={"Authorization": f"Bearer {ADMIN_KEY}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert "timestamp" in data
        assert "T" in data["timestamp"]  # ISO format

    def test_error_response_consistency(self):
        """All error responses should have consistent structure."""
        endpoints = [
            ("/api/v1/fl/rounds/999", 404),
            ("/api/v1/fl/rounds?skip=-1&limit=10", 400),
        ]

        for endpoint, expected_status in endpoints:
            response = client.get(
                endpoint,
                headers={"Authorization": f"Bearer {ADMIN_KEY}"},
            )
            data = response.json()
            assert response.status_code == expected_status
            assert "error" in data
            assert "error_code" in data
            assert "status_code" in data
            assert "request_id" in data
            assert "timestamp" in data


class TestRoleBasedAccess:
    """Test role-based access control."""

    def test_admin_can_access_all(self):
        """Admin should access any endpoint."""
        response = client.get(
            "/api/v1/fl/status",
            headers={"Authorization": f"Bearer {ADMIN_KEY}"},
        )
        assert response.status_code == 200

    def test_officer_can_read(self):
        """Officer should access read-only endpoints."""
        response = client.get(
            "/api/v1/fl/status",
            headers={"Authorization": f"Bearer {OFFICER_KEY}"},
        )
        assert response.status_code == 200

    def test_reader_role_identified(self):
        """Reader should be able to access public endpoints."""
        response = client.get(
            "/api/v1/health/",
        )
        assert response.status_code == 200

    def test_different_keys_have_different_roles(self):
        """Different API keys should have different roles."""
        from cloud.api.auth import VALID_API_KEYS

        admin_user = VALID_API_KEYS[ADMIN_KEY]
        officer_user = VALID_API_KEYS[OFFICER_KEY]

        assert admin_user["role"] == "admin"
        assert officer_user["role"] == "officer"
        assert admin_user["role"] != officer_user["role"]


class TestErrorResponseStructure:
    """Test detailed error response structure."""

    def test_unauthorized_response_structure(self):
        """Test UnauthorizedError response structure."""
        response = client.get("/api/v1/fl/status")
        assert response.status_code == 401
        data = response.json()

        # Required fields
        assert "error" in data
        assert "error_code" in data
        assert "status_code" in data
        assert "request_id" in data
        assert "timestamp" in data

        # Correct values
        assert isinstance(data["error"], str)
        assert data["error_code"] == "UNAUTHORIZED"
        assert data["status_code"] == 401
        assert isinstance(data["request_id"], str)
        assert isinstance(data["timestamp"], str)

    def test_not_found_response_structure(self):
        """Test NotFoundError response structure."""
        response = client.get(
            "/api/v1/fl/rounds/999",
            headers={"Authorization": f"Bearer {ADMIN_KEY}"},
        )
        assert response.status_code == 404
        data = response.json()

        assert data["error_code"] == "NOT_FOUND"
        assert data["status_code"] == 404
        assert "Round" in data["error"]

    def test_bad_request_response_structure(self):
        """Test BadRequestError response structure."""
        response = client.get(
            "/api/v1/fl/rounds?skip=-1&limit=10",
            headers={"Authorization": f"Bearer {ADMIN_KEY}"},
        )
        assert response.status_code == 400
        data = response.json()

        assert data["error_code"] == "BAD_REQUEST"
        assert data["status_code"] == 400
        assert "Invalid" in data["error"]


class TestPublicVsPrivateEndpoints:
    """Test public vs private endpoint access."""

    def test_health_public(self):
        """Health endpoints are public."""
        response = client.get("/api/v1/health/")
        assert response.status_code == 200

    def test_fl_endpoints_require_auth(self):
        """FL endpoints require authentication."""
        response = client.get("/api/v1/fl/status")
        assert response.status_code == 401

    def test_model_endpoints_require_auth(self):
        """Model endpoints require authentication."""
        response = client.get("/api/v1/models/list")
        assert response.status_code == 401

    def test_authenticated_access_succeeds(self):
        """Authenticated requests to protected endpoints succeed."""
        response = client.get(
            "/api/v1/fl/status",
            headers={"Authorization": f"Bearer {ADMIN_KEY}"},
        )
        assert response.status_code == 200


class TestAuthErrorMessages:
    """Test auth-related error messages."""

    def test_invalid_key_error_message(self):
        """Invalid key should have appropriate error message."""
        response = client.get(
            "/api/v1/fl/status",
            headers={"Authorization": "Bearer invalid-key"},
        )
        data = response.json()
        assert "Invalid API key" in data["error"]

    def test_missing_auth_error_message(self):
        """Missing auth should have appropriate error message."""
        response = client.get("/api/v1/fl/status")
        data = response.json()
        assert "Unauthorized" in data["error"] or "Missing" in data["error"]

    def test_malformed_header_error_message(self):
        """Malformed header should have appropriate error message."""
        response = client.get(
            "/api/v1/fl/status",
            headers={"Authorization": "InvalidFormat key"},
        )
        data = response.json()
        assert "Invalid authorization format" in data["error"]
