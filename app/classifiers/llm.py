"""Strict structured-output classifier backed by an OpenAI-compatible client."""

from typing import Any

import openai
from pydantic import ValidationError

from app.classifiers.base import (
    ClassificationInvalidResponse,
    ClassificationUnavailable,
)
from app.models import ClassificationResult


class LLMClassifier:
    """Classify with one structured-output request to a LiteLLM gateway."""

    def __init__(self, client: Any, model: str, prompt: str) -> None:
        self._client = client
        self.model = model
        self._prompt = prompt

    def classify(self, text: str) -> ClassificationResult:
        try:
            response = self._client.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0,
                response_format=ClassificationResult,
            )
        except (openai.LengthFinishReasonError, openai.ContentFilterFinishReasonError) as error:
            raise ClassificationInvalidResponse("LLM output was incomplete") from error
        except ValidationError as error:
            raise ClassificationInvalidResponse("LLM output did not match the schema") from error
        except openai.APIError as error:
            raise ClassificationUnavailable("LLM backend is unavailable") from error

        if not response.choices:
            raise ClassificationInvalidResponse("LLM response contained no choices")

        choice = response.choices[0]
        if choice.finish_reason != "stop":
            raise ClassificationInvalidResponse("LLM output was incomplete")

        message = choice.message
        if getattr(message, "refusal", None):
            raise ClassificationInvalidResponse("LLM refused the classification")
        if message.parsed is None:
            raise ClassificationInvalidResponse("LLM response had no parsed output")

        try:
            return ClassificationResult.model_validate(message.parsed)
        except ValidationError as error:
            raise ClassificationInvalidResponse("LLM output did not match the schema") from error
