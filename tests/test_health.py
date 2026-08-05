"""Tests for health check endpoint."""
import pytest


@pytest.mark.unit
def test_health_endpoint(client_with_llm):
    """Test GET /v1/health returns 200 with status ok."""
    response = client_with_llm.get("/v1/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.unit
def test_root_endpoint(client_with_llm):
    """Test GET / returns 200 with classifier info."""
    response = client_with_llm.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Classifier API"
    assert "classifier" in data
    assert data["classifier"] == "llm"
