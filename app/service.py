"""Application service for classification and provenance."""

from dataclasses import dataclass

from app.classifiers.base import Classifier
from app.models import (
    CLASSIFICATION_SCHEMA_VERSION,
    ClassificationMetadata,
    ClassificationResponse,
)
from app.prompts import PROMPT_VERSION


@dataclass(frozen=True, slots=True)
class ClassificationService:
    """Invoke a classifier and attach stable provenance."""

    classifier: Classifier
    model: str

    def classify(self, text: str) -> ClassificationResponse:
        return ClassificationResponse(
            classification=self.classifier.classify(text),
            metadata=ClassificationMetadata(
                backend="llm",
                schema_version=CLASSIFICATION_SCHEMA_VERSION,
                model=self.model,
                prompt_version=PROMPT_VERSION,
            ),
        )
