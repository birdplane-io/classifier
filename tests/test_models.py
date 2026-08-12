"""Tests for the canonical versioned classification contract."""

import pytest
from pydantic import ValidationError

from app.models import (
    CLASSIFICATION_SCHEMA_VERSION,
    ClassificationResult,
    ProcessingRoute,
    QualityFlag,
    RecordingFormat,
)


def test_schema_version_is_explicit() -> None:
    assert CLASSIFICATION_SCHEMA_VERSION == "1"


@pytest.mark.parametrize("recording_format", list(RecordingFormat))
def test_accepts_every_recording_format(recording_format: RecordingFormat) -> None:
    result = ClassificationResult(format=recording_format, route="general")
    assert result.format is recording_format


@pytest.mark.parametrize("route", list(ProcessingRoute))
def test_accepts_every_processing_route(route: ProcessingRoute) -> None:
    result = ClassificationResult(format="monologue", route=route)
    assert result.route is route


@pytest.mark.parametrize("flag", list(QualityFlag))
def test_accepts_every_quality_flag(flag: QualityFlag) -> None:
    result = ClassificationResult(
        format="conversation", route="general", quality_flags=[flag]
    )
    assert result.quality_flags == (flag,)


def test_quality_flags_default_empty_and_allow_multiple() -> None:
    clean = ClassificationResult(format="interview", route="science")
    flagged = ClassificationResult(
        format="interview",
        route="science",
        quality_flags=["poor_audio", "incomplete"],
    )

    assert clean.quality_flags == ()
    assert flagged.quality_flags == (
        QualityFlag.POOR_AUDIO,
        QualityFlag.INCOMPLETE,
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [("format", "podcast"), ("route", "unknown"), ("quality_flags", ["noisy"])],
)
def test_rejects_unknown_enum_values(field: str, value: object) -> None:
    payload = {"format": "interview", "route": "general", "quality_flags": []}
    payload[field] = value

    with pytest.raises(ValidationError):
        ClassificationResult.model_validate(payload)


def test_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ClassificationResult.model_validate(
            {"format": "interview", "route": "science", "confidence": 0.9}
        )
