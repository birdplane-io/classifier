"""Tests for configuration."""
import os
from importlib import reload

import pytest


@pytest.mark.unit
class TestConfig:
    """Tests for app configuration."""

    def test_config_load_defaults(self, monkeypatch):
        """Test Config loads with default values."""
        # Clear environment
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        monkeypatch.delenv("LLM_MODEL", raising=False)
        monkeypatch.delenv("LLM_BASE_URL", raising=False)
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        monkeypatch.delenv("CLASSIFIER_TYPE", raising=False)
        
        import app.config
        reload(app.config)
        from app.config import Config
        
        assert Config.LLM_MODEL == "gpt-4-turbo"
        assert Config.LLM_TEMPERATURE == 0.0
        assert Config.LLM_MAX_TOKENS == 4000
        assert Config.LLM_PROVIDER == "openai"
        assert Config.LLM_BASE_URL == ""
        assert Config.CLASSIFIER_TYPE == "llm"

    def test_config_load_from_env(self, monkeypatch):
        """Test Config loads values from environment."""
        monkeypatch.setenv("LLM_API_KEY", "test-key-123")
        monkeypatch.setenv("LLM_MODEL", "claude-3-opus")
        monkeypatch.setenv("LLM_TEMPERATURE", "0.5")
        monkeypatch.setenv("LLM_MAX_TOKENS", "2000")
        monkeypatch.setenv("LLM_BASE_URL", "http://localhost:4000")
        monkeypatch.setenv("LLM_PROVIDER", "anthropic")
        
        import app.config
        reload(app.config)
        from app.config import Config
        
        assert Config.LLM_API_KEY == "test-key-123"
        assert Config.LLM_MODEL == "claude-3-opus"
        assert Config.LLM_TEMPERATURE == 0.5
        assert Config.LLM_MAX_TOKENS == 2000
        assert Config.LLM_BASE_URL == "http://localhost:4000"
        assert Config.LLM_PROVIDER == "anthropic"

    def test_config_validate_llm_without_api_key(self, monkeypatch):
        """Test Config.validate raises error for LLM without API key."""
        monkeypatch.setenv("CLASSIFIER_TYPE", "llm")
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        
        import app.config
        reload(app.config)
        from app.config import Config
        
        with pytest.raises(ValueError, match="LLM_API_KEY"):
            Config.validate()

    def test_config_validate_embedding_no_key_required(self, monkeypatch):
        """Test Config.validate succeeds for embedding classifier without API key."""
        monkeypatch.setenv("CLASSIFIER_TYPE", "embedding")
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        
        import app.config
        reload(app.config)
        from app.config import Config
        
        # Should not raise
        Config.validate()

    def test_config_validate_invalid_classifier_type(self, monkeypatch):
        """Test Config.validate raises error for invalid classifier type."""
        monkeypatch.setenv("CLASSIFIER_TYPE", "unknown_classifier")
        monkeypatch.setenv("LLM_API_KEY", "test-key")
        
        import app.config
        reload(app.config)
        from app.config import Config
        
        with pytest.raises(ValueError, match="Invalid CLASSIFIER_TYPE"):
            Config.validate()

    def test_config_classifier_type_case_insensitive(self, monkeypatch):
        """Test CLASSIFIER_TYPE is case-insensitive."""
        monkeypatch.setenv("CLASSIFIER_TYPE", "LLM")
        
        import app.config
        reload(app.config)
        from app.config import Config
        
        assert Config.CLASSIFIER_TYPE == "llm"

    def test_config_custom_endpoint(self, monkeypatch):
        """Test Config with custom LLM endpoint."""
        monkeypatch.setenv("LLM_API_KEY", "local-key")
        monkeypatch.setenv("LLM_MODEL", "llama2")
        monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434")
        monkeypatch.setenv("LLM_PROVIDER", "local")
        
        import app.config
        reload(app.config)
        from app.config import Config
        
        assert Config.LLM_BASE_URL == "http://localhost:11434"
        assert Config.LLM_PROVIDER == "local"
        assert Config.LLM_MODEL == "llama2"
