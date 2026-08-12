"""Classifier and classification-service construction."""

from openai import OpenAI

from app.classifiers import Classifier, LLMClassifier
from app.config import ClassifierBackend, Settings
from app.prompts import load_classification_prompt
from app.service import ClassificationService


class ClassifierConfigurationError(ValueError):
    """The selected backend cannot be constructed."""


def create_classifier(settings: Settings) -> Classifier:
    """Construct the configured classifier or fail during startup."""

    if settings.classifier_backend is ClassifierBackend.LIGHTWEIGHT:
        raise ClassifierConfigurationError(
            "The lightweight classifier backend is not implemented"
        )

    client = OpenAI(
        api_key=settings.llm_api_key.get_secret_value(),
        base_url=str(settings.llm_base_url),
        timeout=settings.llm_timeout,
        max_retries=0,
    )
    return LLMClassifier(
        client=client,
        model=settings.llm_model,
        prompt=load_classification_prompt(),
    )


def create_classification_service(settings: Settings) -> ClassificationService:
    """Construct a service with immutable classifier provenance."""

    return ClassificationService(
        classifier=create_classifier(settings),
        model=settings.llm_model,
    )
