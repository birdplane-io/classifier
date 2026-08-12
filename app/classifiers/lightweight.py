"""Reserved lightweight classifier backend."""

from app.classifiers.base import ClassificationUnavailable
from app.models import ClassificationResult


class LightweightClassifier:
    """Placeholder for a future local classifier implementation."""

    def classify(self, text: str) -> ClassificationResult:
        raise ClassificationUnavailable("Lightweight classifier is not implemented")
