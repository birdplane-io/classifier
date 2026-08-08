"""Tests for strict structured-output LLM classification."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import openai
import pytest

from app.classifiers import ClassificationInvalidResponse, ClassificationUnavailable
from app.classifiers.llm import LLMClassifier
from app.models import ClassificationResult


def parsed_response(
    parsed: object | None = None,
    *,
    refusal: str | None = None,
    finish_reason: str = "stop",
) -> SimpleNamespace:
    if parsed is None and refusal is None:
        parsed = ClassificationResult(format="interview", route="science")
    message = SimpleNamespace(parsed=parsed, refusal=refusal)
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message, finish_reason=finish_reason)]
    )


def classifier_with_response(response: object) -> tuple[LLMClassifier, MagicMock]:
    client = MagicMock()
    client.chat.completions.parse.return_value = response
    return LLMClassifier(client, "document-classifier", "system prompt"), client


def test_one_structured_output_call_returns_parsed_result() -> None:
    classifier, client = classifier_with_response(parsed_response())

    result = classifier.classify("Host: What did the study find?")

    assert result == ClassificationResult(format="interview", route="science")
    client.chat.completions.parse.assert_called_once_with(
        model="document-classifier",
        messages=[
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "Host: What did the study find?"},
        ],
        temperature=0,
        response_format=ClassificationResult,
    )


def provider_errors() -> list[openai.OpenAIError]:
    request = httpx.Request("POST", "http://gateway.test/v1/chat/completions")
    return [
        openai.APIConnectionError(request=request),
        openai.APITimeoutError(request=request),
        openai.RateLimitError(
            "rate limited",
            response=httpx.Response(429, request=request),
            body=None,
        ),
        openai.AuthenticationError(
            "unauthorised",
            response=httpx.Response(401, request=request),
            body=None,
        ),
        openai.APIStatusError(
            "gateway failure",
            response=httpx.Response(500, request=request),
            body=None,
        ),
    ]


@pytest.mark.parametrize("provider_error", provider_errors())
def test_provider_errors_are_unavailable(provider_error: Exception) -> None:
    classifier, client = classifier_with_response(parsed_response())
    client.chat.completions.parse.side_effect = provider_error

    with pytest.raises(ClassificationUnavailable, match="unavailable"):
        classifier.classify("text")


@pytest.mark.parametrize(
    "response",
    [
        SimpleNamespace(choices=[]),
        parsed_response(refusal="I cannot classify this"),
        parsed_response(finish_reason="length"),
        parsed_response(parsed=None, refusal="refused"),
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(parsed=None, refusal=None),
                    finish_reason="stop",
                )
            ]
        ),
        parsed_response(parsed={"format": "invented", "route": "science"}),
    ],
)
def test_unusable_output_is_invalid(response: object) -> None:
    classifier, _ = classifier_with_response(response)

    with pytest.raises(ClassificationInvalidResponse):
        classifier.classify("text")


def test_sdk_validation_failure_is_invalid() -> None:
    classifier, client = classifier_with_response(parsed_response())
    try:
        ClassificationResult.model_validate({"format": "invalid", "route": "science"})
    except Exception as validation_error:
        client.chat.completions.parse.side_effect = validation_error

    with pytest.raises(ClassificationInvalidResponse):
        classifier.classify("text")
