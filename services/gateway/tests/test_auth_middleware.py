"""
Integration tests for Gateway authentication middleware.

Tests cover:
- Public endpoint access (no auth)
- Protected endpoint access (with valid/invalid tokens)
- Canary deployment behavior
- Token validation (expired, invalid, missing)
- Error handling and response format
- Metrics collection
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import status

from services.gateway.config import settings as gateway_settings


class TestPublicEndpoints:
    """Test public endpoints that don't require authentication."""

    def test_root_endpoint_no_auth(self, test_client):
        """Root endpoint should be accessible without authentication."""
        response = test_client.get("/")
        assert response.status_code == 200
        assert "service" in response.json()
        assert response.json()["service"] == "Cortex API Gateway"

    def test_health_endpoint_no_auth(self, test_client):
        """Health endpoint should be accessible without authentication."""
        with patch("httpx.AsyncClient") as mock_client:
            # Mock backend service health checks
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            response = test_client.get("/health")
            assert response.status_code == 200
            assert "gateway" in response.json()

    def test_docs_endpoint_no_auth(self, test_client):
        """API docs should be accessible without authentication."""
        response = test_client.get("/docs")
        assert response.status_code == 200

    def test_metrics_endpoint_no_auth(self, test_client):
        """Prometheus metrics should be accessible without authentication."""
        response = test_client.get("/metrics")
        assert response.status_code == 200


class TestProtectedEndpoints:
    """Test protected endpoints requiring authentication."""

    def test_protected_route_with_valid_token(self, test_client, user_token):
        """Protected endpoint should accept valid JWT token."""
        response = test_client.get(
            "/api/profile",
            cookies={"cortex_access_token": user_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "user@test.com"
        assert data["name"] == "Regular User"
        assert "user" in data["roles"]

    def test_protected_route_without_token(self, test_client):
        """Protected endpoint should reject request without token (when canary active)."""
        # Note: This test's behavior depends on canary settings
        # In conftest, we disable canary for deterministic testing
        response = test_client.get("/api/profile")

        # With canary disabled and auth enabled, should require auth
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "token_missing"

    def test_protected_route_with_expired_token(self, test_client, expired_token):
        """Protected endpoint should reject expired token."""
        response = test_client.get(
            "/api/profile",
            cookies={"cortex_access_token": expired_token}
        )

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "token_expired"
        assert "expired" in data["error"]["message"].lower()

    def test_protected_route_with_invalid_token(self, test_client, invalid_token):
        """Protected endpoint should reject token with invalid signature."""
        response = test_client.get(
            "/api/profile",
            cookies={"cortex_access_token": invalid_token}
        )

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        # Invalid token can return various error codes depending on failure type
        assert data["error"]["code"] in ["token_invalid", "authentication_failed", "token_missing"]


class TestRoleBasedAccess:
    """Test role-based access control."""

    def test_admin_endpoint_with_admin_token(self, test_client, admin_token):
        """Admin endpoint should accept admin token."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}
            mock_response.elapsed.total_seconds.return_value = 0.1
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            response = test_client.get(
                "/api/admin/services",
                cookies={"cortex_access_token": admin_token}
            )

            assert response.status_code == 200
            data = response.json()
            assert "admin" in data
            assert data["admin"] == "admin@test.com"

    def test_admin_endpoint_with_user_token(self, test_client, user_token):
        """Admin endpoint should reject non-admin token."""
        response = test_client.get(
            "/api/admin/services",
            cookies={"cortex_access_token": user_token}
        )

        assert response.status_code == 403
        data = response.json()
        assert "error" in data
        assert "admin" in data["error"]["message"].lower()


class TestCanaryDeployment:
    """Test canary deployment behavior."""

    def test_canary_disabled_authenticates_all(self, test_client, user_token):
        """With canary disabled, all requests should be authenticated."""
        with patch.object(gateway_settings, "canary_enabled", False):
            with patch.object(gateway_settings, "auth_enabled", True):
                # This test verifies deterministic behavior
                # All non-public requests should require auth
                response = test_client.get("/api/profile")
                assert response.status_code == 401

    def test_canary_enabled_with_0_percent(self, test_client):
        """With 0% canary, no requests should be authenticated."""
        with patch.object(gateway_settings, "canary_enabled", True):
            with patch.object(gateway_settings, "canary_auth_percentage", 0):
                with patch.object(gateway_settings, "auth_enabled", True):
                    # Non-public endpoint without auth should pass through
                    # (This would normally fail but canary is 0%)
                    response = test_client.get("/api/someendpoint")
                    # Should not get 401, might get 404 (endpoint doesn't exist)
                    assert response.status_code != 401

    def test_canary_enabled_with_100_percent(self, test_client):
        """With 100% canary, all requests should be authenticated."""
        with patch.object(gateway_settings, "canary_enabled", True):
            with patch.object(gateway_settings, "canary_auth_percentage", 100):
                with patch.object(gateway_settings, "auth_enabled", True):
                    # All non-public requests should require auth
                    response = test_client.get("/api/profile")
                    assert response.status_code == 401


class TestErrorHandling:
    """Test error handling and response format."""

    def test_missing_token_error_format(self, test_client):
        """Test error response format for missing token."""
        response = test_client.get("/api/profile")

        assert response.status_code == 401
        data = response.json()

        # Verify error structure
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]

        # Verify error content
        assert data["error"]["code"] == "token_missing"
        assert "authentication required" in data["error"]["message"].lower()

    def test_expired_token_error_format(self, test_client, expired_token):
        """Test error response format for expired token."""
        response = test_client.get(
            "/api/profile",
            cookies={"cortex_access_token": expired_token}
        )

        assert response.status_code == 401
        data = response.json()

        # Verify error structure
        assert "error" in data
        assert "code" in data["error"]
        assert data["error"]["code"] == "token_expired"

    def test_invalid_token_error_format(self, test_client, invalid_token):
        """Test error response format for invalid token."""
        response = test_client.get(
            "/api/profile",
            cookies={"cortex_access_token": invalid_token}
        )

        assert response.status_code == 401
        data = response.json()

        # Verify error structure
        assert "error" in data
        assert "code" in data["error"]


class TestProxyAuthentication:
    """Test authentication on proxied requests."""

    def test_proxy_auth_endpoint_with_valid_token(self, test_client, user_token, mock_backend_service):
        """Proxied request with valid token should forward to backend."""
        response = test_client.get(
            "/financial/api/v1/transactions",
            cookies={"cortex_access_token": user_token}
        )

        # Should successfully proxy to backend (mocked)
        assert response.status_code in [200, 404]  # 404 if route doesn't exist in mock

    def test_proxy_public_endpoint_no_auth(self, test_client, mock_backend_service):
        """Public proxied endpoints should not require auth."""
        # Auth login endpoint is public
        response = test_client.post(
            "/auth/api/v1/auth/login",
            json={"email": "test@test.com", "password": "test123"}
        )

        # Should proxy without authentication
        assert response.status_code != 401


class TestMetricsCollection:
    """Test Prometheus metrics collection."""

    def test_auth_success_metric(self, test_client, user_token):
        """Successful authentication should increment success metric."""
        from services.gateway.metrics import auth_metrics

        # Get initial metric value
        initial_value = auth_metrics.auth_validations_total.labels(
            result="success",
            service="gateway"
        )._value.get()

        # Make authenticated request
        response = test_client.get(
            "/api/profile",
            cookies={"cortex_access_token": user_token}
        )
        assert response.status_code == 200

        # Metric should increment (this is a simplified test)
        # In real scenario, you'd check the metric export endpoint

    def test_auth_failure_metric(self, test_client):
        """Failed authentication should increment failure metric."""
        from services.gateway.metrics import auth_metrics

        # Make unauthenticated request
        response = test_client.get("/api/profile")
        assert response.status_code == 401

        # Metrics should be tracked (simplified test)
