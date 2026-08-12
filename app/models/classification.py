"""Versioned classification taxonomy shared by every service boundary."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

CLASSIFICATION_SCHEMA_VERSION = "1"


class RecordingFormat(str, Enum):
    """The observable structure of the recording."""

    INTERVIEW = "interview"
    MONOLOGUE = "monologue"
    CONVERSATION = "conversation"
    PANEL = "panel"
    LECTURE = "lecture"
    PRESENTATION = "presentation"


class ProcessingRoute(str, Enum):
    """The downstream workflow best suited to the recording."""

    SCIENCE = "science"
    CURRENT_AFFAIRS = "current_affairs"
    EDUCATION = "education"
    BUSINESS = "business"
    ARTS_AND_CULTURE = "arts_and_culture"
    GENERAL = "general"


class QualityFlag(str, Enum):
    """Independent transcript defects that may affect later processing."""

    INCOMPLETE = "incomplete"
    POOR_AUDIO = "poor_audio"
    OVERLAPPING_SPEECH = "overlapping_speech"
    SPEAKER_LABELS_MISSING = "speaker_labels_missing"
    REPETITION = "repetition"
    NON_ENGLISH = "non_english"


class ClassificationResult(BaseModel):
    """The sole output contract implemented by classifiers."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    format: RecordingFormat
    route: ProcessingRoute
    quality_flags: tuple[QualityFlag, ...] = Field(default_factory=tuple)
