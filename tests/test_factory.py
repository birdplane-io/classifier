"""Tests for startup-time classifier selection."""

from unittest.mock import MagicMock, patch

import pytest

from app.classifier import ClassifierConfigurationError, create_classifier
from app.classifiers import LLMClassifier
from app.config import Settings


def settings(backend: str = "llm") -> Settings:
    return Settings(
        _env_file=None,
        classifier_backend=backend,
        llm_base_url="http://gateway.test/v1",
        llm_api_key="gateway-secret",
    )


def test_factory_configures_openai_client_for_litellm_gateway() -> None:
    client = MagicMock()
    with patch("app.classifier.OpenAI", return_value=client) as openai:
        classifier = create_classifier(settings())

    assert isinstance(classifier, LLMClassifier)
    openai.assert_called_once_with(
        api_key="gateway-secret",
        base_url="http://gateway.test/v1",
        timeout=30.0,
        max_retries=0,
    )


def test_lightweight_selection_fails_fast() -> None:
    with pytest.raises(ClassifierConfigurationError, match="not implemented"):
        create_classifier(settings("lightweight"))
