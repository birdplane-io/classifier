"""Tests for validated classifier configuration."""

import pytest
from pydantic import ValidationError

from app.config import ClassifierBackend, Settings


def test_settings_defaults() -> None:
    settings = Settings(
        _env_file=None,
        llm_base_url="http://gateway.test/v1",
        llm_api_key="secret",
    )

    assert settings.classifier_backend is ClassifierBackend.LLM
    assert settings.llm_model == "document-classifier"
    assert settings.llm_timeout == 30.0


def test_settings_environment_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLASSIFIER_BACKEND", "lightweight")
    monkeypatch.setenv("LLM_BASE_URL", "https://gateway.test/v1")
    monkeypatch.setenv("LLM_API_KEY", "environment-secret")
    monkeypatch.setenv("LLM_MODEL", "classifier-canary")
    monkeypatch.setenv("LLM_TIMEOUT", "4.5")

    settings = Settings(_env_file=None)

    assert settings.classifier_backend is ClassifierBackend.LIGHTWEIGHT
    assert str(settings.llm_base_url) == "https://gateway.test/v1"
    assert settings.llm_api_key.get_secret_value() == "environment-secret"
    assert settings.llm_model == "classifier-canary"
    assert settings.llm_timeout == 4.5


def test_missing_llm_credentials_are_invalid() -> None:
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None)

    missing_fields = {item["loc"][0] for item in error.value.errors()}
    assert missing_fields == {"llm_base_url", "llm_api_key"}


def test_invalid_backend_is_rejected() -> None:
    with pytest.raises(ValidationError, match="llm.*lightweight"):
        Settings(
            _env_file=None,
            classifier_backend="hybrid",
            llm_base_url="http://gateway.test/v1",
            llm_api_key="secret",
        )
