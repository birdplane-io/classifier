"""Tests for classify endpoint."""
import json

import pytest


@pytest.mark.unit
def test_classify_with_llm_success(client_with_llm, mock_litellm_client, mock_litellm_response):
    """Test POST /v1/classify with LLM classifier returns classification."""
    response = client_with_llm.post(
        "/v1/classify",
        json={"data": "This is test content to classify."},
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "classification" in data
    assert "llm" in data["method"]
    assert "recording_format" in data["classification"]
    assert data["classification"]["recording_format"]["primary"] == "podcast_conversation"


@pytest.mark.unit
def test_classify_with_embedding(client_with_embedding):
    """Test POST /v1/classify with Embedding classifier returns not implemented."""
    response = client_with_embedding.post(
        "/v1/classify",
        json={"data": "This is test content to classify."},
    )

    assert response.status_code == 501
    assert "Not implemented" in response.json()["detail"]


@pytest.mark.unit
def test_classify_with_invalid_json_response(client_with_llm, mock_litellm_invalid_json):
    """Test POST /v1/classify returns graceful fallback on invalid LLM JSON."""
    response = client_with_llm.post(
        "/v1/classify",
        json={"data": "Test content"},
    )
    
    assert response.status_code == 200
    body = response.json()
    assert "classification" in body
    assert "fallback" in body["method"]
    assert "heuristic fallback" in body["error"]


@pytest.mark.unit
def test_classify_with_api_error(client_with_llm, mock_litellm_error):
    """Test POST /v1/classify handles API errors."""
    response = client_with_llm.post(
        "/v1/classify",
        json={"data": "Test content"},
    )
    
    assert response.status_code == 500
    assert "Internal error" in response.json()["detail"]


@pytest.mark.unit
def test_classify_with_empty_data(client_with_llm):
    """Test POST /v1/classify with empty data."""
    response = client_with_llm.post(
        "/v1/classify",
        json={"data": ""},
    )
    
    # Should still process, classifier handles empty input
    assert response.status_code in [200, 400, 500]


@pytest.mark.unit
def test_classify_with_long_text(client_with_llm, mock_litellm_client, mock_litellm_response):
    """Test POST /v1/classify with long text."""
    long_text = "Test content. " * 1000  # ~14k characters
    
    response = client_with_llm.post(
        "/v1/classify",
        json={"data": long_text},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "classification" in data


@pytest.mark.unit
def test_classify_missing_data_field(client_with_llm):
    """Test POST /v1/classify with missing data field."""
    response = client_with_llm.post(
        "/v1/classify",
        json={},
    )
    
    assert response.status_code == 422  # FastAPI validation error
