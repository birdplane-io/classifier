"""Typed HTTP request and response envelopes."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.classification import ClassificationResult


class ClassifyRequest(BaseModel):
    """A transcript classification request."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be blank")
        return value


class ClassificationMetadata(BaseModel):
    """Immutable provenance for one classification."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    backend: Literal["llm"]
    schema_version: Literal["1"]
    model: str
    prompt_version: Literal["1"]


class ClassificationResponse(BaseModel):
    """The API response envelope."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    classification: ClassificationResult
    metadata: ClassificationMetadata
