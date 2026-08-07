"""Versioned classifier prompt loading."""

from importlib.resources import files

PROMPT_VERSION = "1"


def load_classification_prompt() -> str:
    """Load the classifier system prompt packaged with the application."""

    return (
        files("app.prompts")
        .joinpath("classification-v1.md")
        .read_text(encoding="utf-8")
        .strip()
    )


__all__ = ["PROMPT_VERSION", "load_classification_prompt"]
