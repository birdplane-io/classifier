"""Tests for dataset validity and evaluation metrics."""

import pytest

from app.models import ClassificationResult, ProcessingRoute, QualityFlag, RecordingFormat
from evaluation.evaluator import EvaluationExample, compute_metrics, load_dataset


def test_checked_in_dataset_is_valid_and_covers_taxonomy() -> None:
    examples = load_dataset()

    assert len(examples) == 18
    assert len({example.id for example in examples}) == len(examples)
    assert {example.dataset_version for example in examples} == {"1"}
    assert {example.review_status for example in examples} == {"verified"}
    assert {example.expected.format for example in examples} == set(RecordingFormat)
    assert {example.expected.route for example in examples} == set(ProcessingRoute)
    assert {
        flag for example in examples for flag in example.expected.quality_flags
    } == set(QualityFlag)
    assert any(not example.expected.quality_flags for example in examples)


def example(
    identifier: str, format: str, route: str, flags: list[str]
) -> EvaluationExample:
    return EvaluationExample.model_validate(
        {
            "id": identifier,
            "text": "Synthetic transcript.",
            "expected": {"format": format, "route": route, "quality_flags": flags},
            "dataset_version": "1",
            "review_status": "verified",
        }
    )


def test_deterministic_metric_calculations() -> None:
    examples = [
        example("a", "interview", "science", ["poor_audio"]),
        example("b", "monologue", "general", []),
        example("c", "interview", "science", ["poor_audio", "incomplete"]),
    ]
    predictions = {
        "a": ClassificationResult(
            format="interview", route="science", quality_flags=["poor_audio"]
        ),
        "b": ClassificationResult(
            format="interview", route="general", quality_flags=["repetition"]
        ),
        "c": ClassificationResult(
            format="interview", route="general", quality_flags=["incomplete"]
        ),
    }

    metrics = compute_metrics(examples, predictions)

    assert metrics["format"]["accuracy"] == pytest.approx(2 / 3)  # type: ignore[index]
    assert metrics["route"]["accuracy"] == pytest.approx(2 / 3)  # type: ignore[index]
    format_classes = metrics["format"]["per_class"]  # type: ignore[index]
    assert format_classes["interview"]["precision"] == pytest.approx(2 / 3)
    assert format_classes["interview"]["recall"] == 1.0
    assert format_classes["interview"]["f1"] == pytest.approx(0.8)
    quality = metrics["quality_flags"]  # type: ignore[assignment]
    assert quality["micro"]["precision"] == pytest.approx(2 / 3)
    assert quality["micro"]["recall"] == pytest.approx(2 / 3)
    assert quality["micro"]["f1"] == pytest.approx(2 / 3)
    assert quality["per_label"]["poor_audio"]["recall"] == pytest.approx(0.5)
    assert quality["per_label"]["incomplete"]["f1"] == 1.0
    assert quality["per_label"]["repetition"]["precision"] == 0.0
    confusion = metrics["format"]["confusion_matrix"]  # type: ignore[index]
    assert confusion["monologue"]["interview"] == 1


def test_perfect_predictions_score_one() -> None:
    examples = load_dataset()
    metrics = compute_metrics(
        examples, {example.id: example.expected for example in examples}
    )

    assert metrics["format"]["accuracy"] == 1.0  # type: ignore[index]
    assert metrics["route"]["accuracy"] == 1.0  # type: ignore[index]
    assert metrics["quality_flags"]["micro"]["f1"] == 1.0  # type: ignore[index]


def test_prediction_ids_must_match_dataset() -> None:
    examples = [example("expected", "interview", "science", [])]

    with pytest.raises(ValueError, match="missing=.*expected.*unexpected=.*other"):
        compute_metrics(
            examples,
            {"other": ClassificationResult(format="interview", route="science")},
        )
