"""Pytest configuration and shared fixtures."""
import json
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_litellm_response():
    """Mock LiteLLM completion response."""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "classification": {
                                "recording_format": {
                                    "primary": "podcast_conversation",
                                    "secondary": [],
                                    "confidence": 0.95,
                                },
                                "subject_domain": {
                                    "primary": "computer_science_and_ai",
                                    "secondary": [],
                                    "confidence": 0.90,
                                },
                                "scientific_content": {
                                    "level": "substantive",
                                    "functions": ["concept_explanation"],
                                    "basis": "Test content",
                                    "confidence": 0.85,
                                },
                                "communicative_purpose": {
                                    "primary": "explain",
                                    "secondary": [],
                                    "confidence": 0.90,
                                },
                                "audience": {
                                    "level": "interested_non_specialist",
                                    "basis": "Accessible explanation",
                                    "confidence": 0.85,
                                },
                                "evidence_profile": {
                                    "empirical_evidence": "moderate",
                                    "quantitative_data": "low",
                                    "methodological_detail": "moderate",
                                    "source_attribution": "moderate",
                                    "causal_reasoning": "moderate",
                                    "philosophical_reasoning": "none",
                                    "normative_reasoning": "none",
                                    "policy_argument": "none",
                                    "personal_anecdote": "none",
                                    "speculation": "low",
                                },
                                "viewpoint_structure": {
                                    "type": "single_expository_viewpoint",
                                    "meaningful_disagreement": False,
                                    "objections_addressed": False,
                                    "consensus_reached": False,
                                    "unresolved_disagreement": False,
                                    "notes": "Single speaker",
                                },
                                "transcript_quality": {
                                    "overall": "good",
                                    "word_recognition": "good",
                                    "punctuation": "good",
                                    "speaker_turn_separation": "good",
                                    "speaker_identification": "good",
                                    "timestamps": "good",
                                    "completeness": "good",
                                    "repetition_resistance": "good",
                                    "flags": [],
                                    "notes": "Clean transcript",
                                },
                                "routing": {
                                    "primary": "general_transcript_summary",
                                    "secondary": [],
                                    "preprocessing_required": [],
                                    "reason": "Test classification",
                                },
                            },
                            "content_outline": {
                                "main_topic": "Test topic",
                                "major_subtopics": [],
                                "named_speakers_or_roles": [],
                                "languages_detected": ["English"],
                            },
                            "classification_notes": {
                                "ambiguities": [],
                                "unsupported_inferences_avoided": [],
                                "overall_confidence": 0.88,
                            },
                        }
                    )
                }
            }
        ]
    }


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        "classification": {
            "recording_format": {
                "primary": "podcast_conversation",
                "secondary": [],
                "confidence": 0.95,
            },
            "subject_domain": {
                "primary": "computer_science_and_ai",
                "secondary": [],
                "confidence": 0.90,
            },
            "scientific_content": {
                "level": "substantive",
                "functions": ["concept_explanation"],
                "basis": "Test content",
                "confidence": 0.85,
            },
            "communicative_purpose": {
                "primary": "explain",
                "secondary": [],
                "confidence": 0.90,
            },
            "audience": {
                "level": "interested_non_specialist",
                "basis": "Accessible explanation",
                "confidence": 0.85,
            },
            "evidence_profile": {
                "empirical_evidence": "moderate",
                "quantitative_data": "low",
                "methodological_detail": "moderate",
                "source_attribution": "moderate",
                "causal_reasoning": "moderate",
                "philosophical_reasoning": "none",
                "normative_reasoning": "none",
                "policy_argument": "none",
                "personal_anecdote": "none",
                "speculation": "low",
            },
            "viewpoint_structure": {
                "type": "single_expository_viewpoint",
                "meaningful_disagreement": False,
                "objections_addressed": False,
                "consensus_reached": False,
                "unresolved_disagreement": False,
                "notes": "Single speaker",
            },
            "transcript_quality": {
                "overall": "good",
                "word_recognition": "good",
                "punctuation": "good",
                "speaker_turn_separation": "good",
                "speaker_identification": "good",
                "timestamps": "good",
                "completeness": "good",
                "repetition_resistance": "good",
                "flags": [],
                "notes": "Clean transcript",
            },
            "routing": {
                "primary": "general_transcript_summary",
                "secondary": [],
                "preprocessing_required": [],
                "reason": "Test classification",
            },
        },
        "content_outline": {
            "main_topic": "Test topic",
            "major_subtopics": [],
            "named_speakers_or_roles": [],
            "languages_detected": ["English"],
        },
        "classification_notes": {
            "ambiguities": [],
            "unsupported_inferences_avoided": [],
            "overall_confidence": 0.88,
        },
    }


@pytest.fixture
def client_with_llm():
    """Create FastAPI test client with LLM classifier."""
    os.environ["CLASSIFIER_TYPE"] = "llm"
    os.environ["LLM_API_KEY"] = "test-key"
    os.environ["LLM_MODEL"] = "gpt-4-turbo"

    from app.classifier import reset_classifier_cache
    reset_classifier_cache()
    
    from app.main import app
    
    return TestClient(app)


@pytest.fixture
def client_with_embedding():
    """Create FastAPI test client with Embedding classifier."""
    os.environ["CLASSIFIER_TYPE"] = "embedding"

    from app.classifier import reset_classifier_cache
    reset_classifier_cache()
    
    from app.main import app
    
    return TestClient(app)


@pytest.fixture
def mock_openai_client(mocker, mock_openai_response):
    """Mock OpenAI client with successful response."""
    mock_message = MagicMock()
    mock_message.content = json.dumps(mock_openai_response)
    
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    
    mocker.patch("app.classifiers.llm.OpenAI", return_value=mock_client)
    
    return mock_client


@pytest.fixture
def mock_litellm_client(mocker, mock_litellm_response):
    """Mock LiteLLM completion function with successful response."""
    mocker.patch("app.classifiers.llm.litellm.api_key", "test-key")
    mocker.patch(
        "app.classifiers.llm.litellm.completion",
        return_value=mock_litellm_response,
    )


@pytest.fixture
def mock_openai_invalid_json(mocker):
    """Mock OpenAI client returning invalid JSON."""
    mock_message = MagicMock()
    mock_message.content = "This is not valid JSON"
    
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    
    mocker.patch("app.classifiers.llm.OpenAI", return_value=mock_client)
    
    return mock_client


@pytest.fixture
def mock_litellm_invalid_json(mocker):
    """Mock LiteLLM returning invalid JSON."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Invalid JSON"))]
    
    mocker.patch("app.classifiers.llm.litellm.api_key", "test-key")
    mocker.patch("app.classifiers.llm.litellm.completion", return_value=mock_response)


@pytest.fixture
def mock_openai_error(mocker):
    """Mock OpenAI client raising an error."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("API Error")
    
    mocker.patch("app.classifiers.llm.OpenAI", return_value=mock_client)
    
    return mock_client


@pytest.fixture
def mock_litellm_error(mocker):
    """Mock LiteLLM raising an error."""
    mocker.patch("app.classifiers.llm.litellm.api_key", "test-key")
    mocker.patch(
        "app.classifiers.llm.litellm.completion",
        side_effect=RuntimeError("API Error"),
    )
