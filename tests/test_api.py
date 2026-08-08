"""Tests for the typed classification HTTP boundary."""

from fastapi.testclient import TestClient
import pytest

from app.classifier import ClassifierConfigurationError
from app.classifiers import ClassificationInvalidResponse, ClassificationUnavailable
from app.config import Settings
from app.main import create_app
from app.models import ClassificationResult
from app.service import ClassificationService


class ResultClassifier:
    def classify(self, text: str) -> ClassificationResult:
        return ClassificationResult(format="interview", route="science")


class FailingClassifier:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def classify(self, text: str) -> ClassificationResult:
        raise self.error


def client_for(classifier: object) -> TestClient:
    service = ClassificationService(classifier=classifier, model="document-classifier")  # type: ignore[arg-type]
    return TestClient(create_app(service=service))


def test_classify_request_and_response_contract() -> None:
    with client_for(ResultClassifier()) as client:
        response = client.post("/v1/classify", json={"text": "Host: Welcome."})

    assert response.status_code == 200
    assert response.json() == {
        "classification": {
            "format": "interview",
            "route": "science",
            "quality_flags": [],
        },
        "metadata": {
            "backend": "llm",
            "schema_version": "1",
            "model": "document-classifier",
            "prompt_version": "1",
        },
    }


def test_old_request_shape_and_blank_text_are_rejected() -> None:
    with client_for(ResultClassifier()) as client:
        old_shape = client.post("/v1/classify", json={"data": "legacy"})
        blank = client.post("/v1/classify", json={"text": "  \n"})

    assert old_shape.status_code == 422
    assert blank.status_code == 422


def test_unavailable_backend_maps_to_sanitised_503() -> None:
    classifier = FailingClassifier(ClassificationUnavailable("secret provider failure"))
    with client_for(classifier) as client:
        response = client.post("/v1/classify", json={"text": "Transcript"})

    assert response.status_code == 503
    assert response.json() == {"detail": "Classification backend is unavailable"}
    assert "secret" not in response.text


def test_invalid_backend_output_maps_to_sanitised_502() -> None:
    classifier = FailingClassifier(ClassificationInvalidResponse("raw model output"))
    with client_for(classifier) as client:
        response = client.post("/v1/classify", json={"text": "Transcript"})

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Classification backend returned an invalid response"
    }
    assert "raw model" not in response.text


def test_lightweight_backend_fails_during_application_startup() -> None:
    settings = Settings(
        _env_file=None,
        classifier_backend="lightweight",
        llm_base_url="http://gateway.test/v1",
        llm_api_key="secret",
    )

    with pytest.raises(ClassifierConfigurationError, match="not implemented"):
        with TestClient(create_app(settings=settings)):
            pass
