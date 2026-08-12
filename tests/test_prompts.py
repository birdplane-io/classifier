"""Tests for the packaged, versioned prompt."""

from app.models import ProcessingRoute, QualityFlag, RecordingFormat
from app.prompts import PROMPT_VERSION, load_classification_prompt


def test_prompt_version_and_loading() -> None:
    prompt = load_classification_prompt()

    assert PROMPT_VERSION == "1"
    assert prompt.startswith("You classify transcript excerpts.")


def test_prompt_defines_the_entire_taxonomy() -> None:
    prompt = load_classification_prompt()
    labels = (*RecordingFormat, *ProcessingRoute, *QualityFlag)

    for label in labels:
        assert f"`{label.value}`" in prompt
