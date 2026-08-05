"""Classifier factory and interface."""
import os
from app.classifiers.base import Classifier
from app.classifiers.llm import LLMClassifier
from app.classifiers.embedding import EmbeddingClassifier

# Global classifier instance
_classifier: Classifier | None = None
_classifier_type: str | None = None


def get_classifier() -> Classifier:
    """
    Get the current classifier instance.
    
    Returns:
        The active Classifier instance
    """
    global _classifier, _classifier_type
    current_type = os.getenv("CLASSIFIER_TYPE", "llm").lower()

    if _classifier is None or _classifier_type != current_type:
        _classifier = _create_classifier()
        _classifier_type = current_type

    return _classifier


def reset_classifier_cache() -> None:
    """Reset cached classifier instance (useful for tests)."""
    global _classifier, _classifier_type
    _classifier = None
    _classifier_type = None


def _create_classifier() -> Classifier:
    """
    Create a classifier based on environment variable.
    
    CLASSIFIER_TYPE environment variable options:
    - "llm" (default) — LLM-based classifier
    - "embedding" — Embedding-based classifier
    
    Returns:
        Initialized Classifier instance
    """
    classifier_type = os.getenv("CLASSIFIER_TYPE", "llm").lower()
    
    if classifier_type == "embedding":
        return EmbeddingClassifier()
    elif classifier_type == "llm":
        return LLMClassifier()
    else:
        raise ValueError(
            f"Unknown CLASSIFIER_TYPE: {classifier_type}. "
            "Supported values: 'llm', 'embedding'"
        )


def classify(data: str) -> dict:
    """
    Classify input data using the active classifier.
    
    Args:
        data: Input text to classify
        
    Returns:
        Classification result dictionary
    """
    classifier = get_classifier()
    return classifier.classify(data)
