"""
Unit tests for DevOps Info Service FastAPI application.

Tests cover all endpoints, response structures, and error cases.
"""

import pytest
from fastapi.testclient import TestClient
from app import app, get_uptime
import time


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestMainEndpoint:
    """Tests for the main endpoint GET /"""

    def test_main_endpoint_returns_200(self, client):
        """Test that main endpoint returns 200 OK status."""
        response = client.get("/")
        assert response.status_code == 200

    def test_main_endpoint_returns_json(self, client):
        """Test that main endpoint returns JSON content type."""
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"

    def test_main_endpoint_has_required_top_level_keys(self, client):
        """Test that response contains all required top-level keys."""
        response = client.get("/")
        data = response.json()

        required_keys = ["service", "system", "runtime", "request", "endpoints"]
        for key in required_keys:
            assert key in data, f"Missing required key: {key}"

    def test_service_section_structure(self, client):
        """Test service section contains correct fields."""
        response = client.get("/")
        service = response.json()["service"]

        assert "name" in service
        assert "version" in service
        assert "description" in service
        assert "framework" in service
        assert service["framework"] == "FastAPI"

    def test_system_section_structure(self, client):
        """Test system section contains correct fields."""
        response = client.get("/")
        system = response.json()["system"]

        required_fields = [
            "hostname", "platform", "platform_version",
            "architecture", "cpu_count", "python_version"
        ]
        for field in required_fields:
            assert field in system, f"Missing system field: {field}"

        # Verify data types
        assert isinstance(system["hostname"], str)
        assert isinstance(system["cpu_count"], int)

    def test_runtime_section_structure(self, client):
        """Test runtime section contains correct fields."""
        response = client.get("/")
        runtime = response.json()["runtime"]

        assert "uptime_seconds" in runtime
        assert "uptime_human" in runtime
        assert "current_time" in runtime
        assert "timezone" in runtime

        # Verify data types
        assert isinstance(runtime["uptime_seconds"], int)
        assert isinstance(runtime["uptime_human"], str)
        assert runtime["timezone"] == "UTC"

    def test_request_section_structure(self, client):
        """Test request section contains correct fields."""
        response = client.get("/")
        request_data = response.json()["request"]

        assert "client_ip" in request_data
        assert "user_agent" in request_data
        assert "method" in request_data
        assert "path" in request_data

        # Verify values
        assert request_data["method"] == "GET"
        assert request_data["path"] == "/"

    def test_endpoints_section_structure(self, client):
        """Test endpoints section contains list of available endpoints."""
        response = client.get("/")
        endpoints = response.json()["endpoints"]

        assert isinstance(endpoints, list)
        assert len(endpoints) >= 2  # At least / and /health

        # Check each endpoint has required fields
        for endpoint in endpoints:
            assert "path" in endpoint
            assert "method" in endpoint
            assert "description" in endpoint

    def test_uptime_increases_over_time(self, client):
        """Test that uptime increases between requests."""
        response1 = client.get("/")
        uptime1 = response1.json()["runtime"]["uptime_seconds"]

        time.sleep(1)  # Wait 1 second

        response2 = client.get("/")
        uptime2 = response2.json()["runtime"]["uptime_seconds"]

        assert uptime2 >= uptime1, "Uptime should increase over time"

    def test_custom_user_agent_captured(self, client):
        """Test that custom User-Agent header is captured."""
        custom_ua = "CustomBot/1.0"
        response = client.get("/", headers={"User-Agent": custom_ua})
        data = response.json()

        assert data["request"]["user_agent"] == custom_ua


class TestHealthEndpoint:
    """Tests for the health check endpoint GET /health"""

    def test_health_endpoint_returns_200(self, client):
        """Test that health endpoint returns 200 OK status."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self, client):
        """Test that health endpoint returns JSON content type."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"

    def test_health_endpoint_has_required_fields(self, client):
        """Test that health response contains all required fields."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data

    def test_health_status_is_healthy(self, client):
        """Test that health status returns 'healthy'."""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"

    def test_health_timestamp_format(self, client):
        """Test that timestamp is in ISO format."""
        response = client.get("/health")
        data = response.json()

        timestamp = data["timestamp"]
        # Basic ISO format check (YYYY-MM-DD)
        assert "T" in timestamp
        assert ":" in timestamp

    def test_health_uptime_is_positive(self, client):
        """Test that uptime is a positive integer."""
        response = client.get("/health")
        data = response.json()

        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0


class TestErrorHandling:
    """Tests for error cases and edge conditions."""

    def test_404_not_found(self, client):
        """Test that non-existent endpoints return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_404_returns_json_error(self, client):
        """Test that 404 response contains error message."""
        response = client.get("/nonexistent")
        data = response.json()

        assert "error" in data
        assert "message" in data
        assert data["error"] == "Not Found"

    def test_invalid_method_on_main(self, client):
        """Test that POST to GET-only endpoint returns 405."""
        response = client.post("/")
        assert response.status_code == 405

    def test_invalid_method_on_health(self, client):
        """Test that POST to health endpoint returns 405."""
        response = client.post("/health")
        assert response.status_code == 405


class TestUptimeFunction:
    """Tests for the get_uptime() helper function."""

    def test_get_uptime_returns_tuple(self):
        """Test that get_uptime returns a tuple."""
        result = get_uptime()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_get_uptime_first_element_is_int(self):
        """Test that uptime seconds is an integer."""
        seconds, _ = get_uptime()
        assert isinstance(seconds, int)
        assert seconds >= 0

    def test_get_uptime_second_element_is_string(self):
        """Test that uptime human format is a string."""
        _, human = get_uptime()
        assert isinstance(human, str)
        assert "hours" in human or "minutes" in human

    def test_get_uptime_format(self):
        """Test that uptime human format contains expected words."""
        _, human = get_uptime()
        assert "hours" in human
        assert "minutes" in human

