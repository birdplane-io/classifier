"""Base classifier interface."""
from abc import ABC, abstractmethod


class Classifier(ABC):
    """Base class for all classifiers."""

    @abstractmethod
    def classify(self, data: str) -> dict:
        """
        Classify input data.
        
        Args:
            data: Input text to classify
            
        Returns:
            Classification result dictionary with keys:
            - result: Classification label/category
            - confidence: Confidence score (0.0-1.0)
            - input: Echo of input data
        """
        pass
