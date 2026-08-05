"""Application configuration."""
import os
from typing import Optional


class Config:
    """Application configuration from environment variables."""

    # LLM Configuration (LiteLLM or direct provider)
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4-turbo")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.0"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "4000"))
    
    # LiteLLM Configuration
    # Set LLM_BASE_URL to use a custom endpoint (e.g., local server, LiteLLM proxy)
    # Leave empty to use provider's default endpoint
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "")
    
    # Provider selection: "openai", "anthropic", "local", etc.
    # Or use model naming convention: "openai/gpt-4", "claude-3-opus", etc.
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")

    # Classifier Selection
    CLASSIFIER_TYPE: str = os.getenv("CLASSIFIER_TYPE", "llm").lower()

    @classmethod
    def get_llm_api_key(cls) -> str:
        """Get LLM API key from supported environment variables."""
        return os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY", "")

    @classmethod
    def get_llm_model(cls) -> str:
        """Get LLM model name from supported environment variables."""
        return os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL", cls.LLM_MODEL)

    @classmethod
    def get_llm_temperature(cls) -> float:
        """Get LLM temperature from environment variables."""
        return float(os.getenv("LLM_TEMPERATURE", str(cls.LLM_TEMPERATURE)))

    @classmethod
    def get_llm_max_tokens(cls) -> int:
        """Get LLM max tokens from environment variables."""
        return int(os.getenv("LLM_MAX_TOKENS", str(cls.LLM_MAX_TOKENS)))

    @classmethod
    def get_llm_base_url(cls) -> str:
        """Get optional custom LLM base URL."""
        return os.getenv("LLM_BASE_URL", cls.LLM_BASE_URL)

    @classmethod
    def get_llm_provider(cls) -> str:
        """Get provider name from environment variables."""
        return os.getenv("LLM_PROVIDER", cls.LLM_PROVIDER)

    @classmethod
    def get_classifier_type(cls) -> str:
        """Get classifier type from environment variables."""
        return os.getenv("CLASSIFIER_TYPE", cls.CLASSIFIER_TYPE).lower()

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        classifier_type = cls.get_classifier_type()
        if classifier_type == "llm" and not cls.get_llm_api_key():
            raise ValueError(
                "LLM_API_KEY environment variable is required when using LLM classifier"
            )
        if classifier_type not in ["llm", "embedding"]:
            raise ValueError(
                f"Invalid CLASSIFIER_TYPE: {classifier_type}. "
                "Supported values: 'llm', 'embedding'"
            )


def get_config() -> Config:
    """Get application configuration."""
    return Config
