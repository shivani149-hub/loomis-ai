"""Unit tests for the health check endpoint."""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_check_returns_200_and_expected_payload():
    """Verify GET /api/health returns 200 OK and expected service metadata."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "loomis-ai-backend"
    assert "version" in data

