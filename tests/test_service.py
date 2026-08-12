"""Tests for classification provenance."""

from app.models import ClassificationResult
from app.service import ClassificationService


class FixedClassifier:
    def classify(self, text: str) -> ClassificationResult:
        return ClassificationResult(format="panel", route="current_affairs")


def test_service_attaches_immutable_versioned_metadata() -> None:
    response = ClassificationService(
        classifier=FixedClassifier(), model="document-classifier"
    ).classify("Panel transcript")

    assert response.model_dump(mode="json") == {
        "classification": {
            "format": "panel",
            "route": "current_affairs",
            "quality_flags": [],
        },
        "metadata": {
            "backend": "llm",
            "schema_version": "1",
            "model": "document-classifier",
            "prompt_version": "1",
        },
    }
