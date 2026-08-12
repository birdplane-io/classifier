"""Environment-backed classifier configuration."""

from enum import Enum
from functools import lru_cache

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ClassifierBackend(str, Enum):
    """Configured classifier implementations."""

    LLM = "llm"
    LIGHTWEIGHT = "lightweight"


class Settings(BaseSettings):
    """Validated service settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    classifier_backend: ClassifierBackend = ClassifierBackend.LLM
    llm_base_url: AnyHttpUrl
    llm_api_key: SecretStr = Field(min_length=1)
    llm_model: str = Field(default="document-classifier", min_length=1)
    llm_timeout: float = Field(default=30.0, gt=0)


@lru_cache
def get_settings() -> Settings:
    """Return one validated settings object per process."""

    return Settings()  # type: ignore[call-arg]
