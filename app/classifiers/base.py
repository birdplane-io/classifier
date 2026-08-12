"""Structural classifier contract and its public failure categories."""

from typing import Protocol, runtime_checkable

from app.models import ClassificationResult


class ClassificationError(Exception):
    """Base exception for expected classification failures."""


class ClassificationUnavailable(ClassificationError):
    """The configured classification backend could not be reached or used."""


class ClassificationInvalidResponse(ClassificationError):
    """The backend returned no complete, schema-valid classification."""


@runtime_checkable
class Classifier(Protocol):
    """Anything that can produce the canonical classification result."""

    def classify(self, text: str) -> ClassificationResult:
        """Classify transcript text."""
        ...
