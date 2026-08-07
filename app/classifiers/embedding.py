"""Embedding-based classifier."""
from app.classifiers.base import Classifier


class EmbeddingClassifier(Classifier):
    """Classifier using text embeddings."""

    def __init__(self):
        """Initialize embedding classifier."""
        raise NotImplementedError(
            "EmbeddingClassifier is not implemented yet. "
            "Use CLASSIFIER_TYPE=llm."
        )

    def classify(self, data: str) -> dict:
        """
        Classify input using embeddings.
        
        Args:
            data: Input text to classify
            
        Returns:
            Classification result
        """
        raise NotImplementedError(
            "EmbeddingClassifier is not implemented yet. "
            "Use CLASSIFIER_TYPE=llm."
        )
