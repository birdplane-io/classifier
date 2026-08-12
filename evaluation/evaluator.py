"""Validate classifier datasets and calculate deterministic metrics."""

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models import ClassificationResult, ProcessingRoute, QualityFlag, RecordingFormat

DATASET_VERSION = "1"
DEFAULT_DATASET = Path(__file__).with_name("data") / "classifier-v1.jsonl"


class EvaluationExample(BaseModel):
    """One reviewed, privacy-safe evaluation example."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    text: str
    expected: ClassificationResult
    dataset_version: Literal["1"]
    review_status: Literal["verified"]


class Prediction(BaseModel):
    """A stored deterministic prediction for one dataset example."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    classification: ClassificationResult


def _load_jsonl(path: Path, model: type[BaseModel]) -> list[BaseModel]:
    records: list[BaseModel] = []
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                records.append(model.model_validate_json(line))
            except Exception as error:
                raise ValueError(f"Invalid record at {path}:{line_number}") from error
    return records


def load_dataset(path: Path = DEFAULT_DATASET) -> list[EvaluationExample]:
    """Load and schema-validate a versioned dataset with unique IDs."""

    examples = [
        record for record in _load_jsonl(path, EvaluationExample)
        if isinstance(record, EvaluationExample)
    ]
    ids = [example.id for example in examples]
    if len(ids) != len(set(ids)):
        raise ValueError("Dataset example IDs must be unique")
    return examples


def load_predictions(path: Path) -> dict[str, ClassificationResult]:
    """Load schema-valid deterministic predictions keyed by example ID."""

    predictions = [
        record for record in _load_jsonl(path, Prediction)
        if isinstance(record, Prediction)
    ]
    keyed = {prediction.id: prediction.classification for prediction in predictions}
    if len(keyed) != len(predictions):
        raise ValueError("Prediction IDs must be unique")
    return keyed


def _safe_ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _prf(tp: int, fp: int, fn: int) -> dict[str, float | int]:
    precision = _safe_ratio(tp, tp + fp)
    recall = _safe_ratio(tp, tp + fn)
    f1 = _safe_ratio(2 * precision * recall, precision + recall)
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "support": tp + fn,
    }


def _single_label_metrics(
    expected: list[str], predicted: list[str], labels: list[str]
) -> dict[str, object]:
    confusion: dict[str, dict[str, int]] = {
        actual: {guess: 0 for guess in labels} for actual in labels
    }
    for actual, guess in zip(expected, predicted, strict=True):
        confusion[actual][guess] += 1

    per_class: dict[str, dict[str, float | int]] = {}
    for label in labels:
        tp = confusion[label][label]
        fp = sum(confusion[actual][label] for actual in labels if actual != label)
        fn = sum(confusion[label][guess] for guess in labels if guess != label)
        per_class[label] = _prf(tp, fp, fn)

    return {
        "accuracy": _safe_ratio(
            sum(actual == guess for actual, guess in zip(expected, predicted, strict=True)),
            len(expected),
        ),
        "per_class": per_class,
        "confusion_matrix": confusion,
    }


def _quality_metrics(
    expected: list[set[str]], predicted: list[set[str]]
) -> dict[str, object]:
    per_label: dict[str, dict[str, float | int]] = {}
    totals = Counter({"tp": 0, "fp": 0, "fn": 0})

    for flag in QualityFlag:
        label = flag.value
        tp = sum(label in actual and label in guess for actual, guess in zip(expected, predicted, strict=True))
        fp = sum(label not in actual and label in guess for actual, guess in zip(expected, predicted, strict=True))
        fn = sum(label in actual and label not in guess for actual, guess in zip(expected, predicted, strict=True))
        per_label[label] = _prf(tp, fp, fn)
        totals.update(tp=tp, fp=fp, fn=fn)

    micro = _prf(totals["tp"], totals["fp"], totals["fn"])
    macro = {
        metric: sum(float(values[metric]) for values in per_label.values()) / len(per_label)
        for metric in ("precision", "recall", "f1")
    }
    return {"micro": micro, "macro": macro, "per_label": per_label}


def compute_metrics(
    examples: list[EvaluationExample],
    predictions: dict[str, ClassificationResult],
) -> dict[str, object]:
    """Calculate multiclass and multilabel metrics for exact dataset IDs."""

    expected_ids = {example.id for example in examples}
    if set(predictions) != expected_ids:
        missing = sorted(expected_ids - set(predictions))
        unexpected = sorted(set(predictions) - expected_ids)
        raise ValueError(f"Prediction ID mismatch: missing={missing}, unexpected={unexpected}")

    actual = [example.expected for example in examples]
    guessed = [predictions[example.id] for example in examples]
    return {
        "dataset_version": DATASET_VERSION,
        "examples": len(examples),
        "format": _single_label_metrics(
            [result.format.value for result in actual],
            [result.format.value for result in guessed],
            [label.value for label in RecordingFormat],
        ),
        "route": _single_label_metrics(
            [result.route.value for result in actual],
            [result.route.value for result in guessed],
            [label.value for label in ProcessingRoute],
        ),
        "quality_flags": _quality_metrics(
            [{flag.value for flag in result.quality_flags} for result in actual],
            [{flag.value for flag in result.quality_flags} for result in guessed],
        ),
    }


def _live_predictions(examples: list[EvaluationExample]) -> dict[str, ClassificationResult]:
    from app.classifier import create_classification_service
    from app.config import get_settings

    service = create_classification_service(get_settings())
    return {example.id: service.classify(example.text).classification for example in examples}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--predictions", type=Path)
    source.add_argument(
        "--live",
        action="store_true",
        help="Explicitly call the configured LLM; never use this mode in CI.",
    )
    args = parser.parse_args()

    examples = load_dataset(args.dataset)
    predictions = (
        _live_predictions(examples)
        if args.live
        else load_predictions(args.predictions)
    )
    print(json.dumps(compute_metrics(examples, predictions), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
