"""Tests for classifier implementations."""
import json
from unittest.mock import MagicMock, patch

import pytest

from app.classifiers.embedding import EmbeddingClassifier
from app.classifiers.llm import LLMClassifier


@pytest.mark.unit
class TestLLMClassifier:
    """Tests for LLMClassifier with LiteLLM."""

    def test_llm_classifier_init_success(self, mocker, monkeypatch, mock_openai_response):
        """Test LLMClassifier initializes successfully with API key and LiteLLM."""
        monkeypatch.setenv("LLM_API_KEY", "test-key")
        monkeypatch.setenv("LLM_MODEL", "gpt-4-turbo")
        monkeypatch.setenv("LLM_TEMPERATURE", "0.0")
        monkeypatch.setenv("LLM_MAX_TOKENS", "4000")
        mocker.patch("app.classifiers.llm.litellm.api_key", "test-key")
        
        classifier = LLMClassifier()
        
        assert classifier.api_key == "test-key"
        assert classifier.model == "gpt-4-turbo"
        assert classifier.temperature == 0.0
        assert classifier.max_tokens == 4000

    def test_llm_classifier_init_no_api_key(self, monkeypatch):
        """Test LLMClassifier raises error without API key."""
        monkeypatch.setenv("LLM_API_KEY", "")
        
        # Reload config
        from importlib import reload
        import app.config
        reload(app.config)
        
        with pytest.raises(ValueError, match="LLM_API_KEY"):
            LLMClassifier()

    def test_llm_classifier_classify_success(self, mocker, monkeypatch, mock_openai_response):
        """Test LLMClassifier.classify returns parsed classification via LiteLLM."""
        monkeypatch.setenv("LLM_API_KEY", "test-key")
        monkeypatch.setenv("LLM_MODEL", "gpt-4-turbo")

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(mock_openai_response)))
        ]
        
        mocker.patch("app.classifiers.llm.litellm.api_key", "test-key")
        mocker.patch("app.classifiers.llm.litellm.completion", return_value=mock_response)
        
        classifier = LLMClassifier()
        result = classifier.classify("Test content")
        
        assert "classification" in result
        assert "gpt-4-turbo" in result["method"]
        assert "recording_format" in result["classification"]

    def test_llm_classifier_classify_success_with_list_content(self, mocker, monkeypatch, mock_openai_response):
        """Test LLMClassifier.classify handles responses where content is a list of parts."""
        monkeypatch.setenv("LLM_API_KEY", "test-key")

        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": [
                            {"type": "output_text", "text": json.dumps(mock_openai_response)},
                        ]
                    }
                }
            ]
        }

        mocker.patch("app.classifiers.llm.litellm.api_key", "test-key")
        mocker.patch("app.classifiers.llm.litellm.completion", return_value=mock_response)

        classifier = LLMClassifier()
        result = classifier.classify("Test content")

        assert "classification" in result
        assert result["classification"]["recording_format"]["primary"] == "podcast_conversation"

    def test_llm_classifier_classify_invalid_json(self, mocker, monkeypatch):
        """Test LLMClassifier.classify returns graceful fallback on invalid JSON."""
        monkeypatch.setenv("LLM_API_KEY", "test-key")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Not JSON"))]
        
        mocker.patch("app.classifiers.llm.litellm.api_key", "test-key")
        mocker.patch("app.classifiers.llm.litellm.completion", return_value=mock_response)
        
        classifier = LLMClassifier()
        result = classifier.classify("Test content")

        assert "classification" in result
        assert "error" in result
        assert "fallback" in result["method"]

    def test_llm_classifier_classify_json_in_code_fence(self, mocker, monkeypatch, mock_openai_response):
        """Test LLMClassifier.classify parses JSON wrapped in markdown fences."""
        monkeypatch.setenv("LLM_API_KEY", "test-key")

        fenced_json = f"```json\n{json.dumps(mock_openai_response)}\n```"
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=fenced_json))]

        mocker.patch("app.classifiers.llm.litellm.api_key", "test-key")
        mocker.patch("app.classifiers.llm.litellm.completion", return_value=mock_response)

        classifier = LLMClassifier()
        result = classifier.classify("Test content")

        assert "classification" in result
        assert result["classification"]["recording_format"]["primary"] == "podcast_conversation"

    def test_llm_classifier_classify_repair_malformed_json(self, mocker, monkeypatch, mock_openai_response):
        """Test LLMClassifier.classify repairs missing comma locally without retry call."""
        monkeypatch.setenv("LLM_API_KEY", "test-key")

        malformed_json = '{"classification": {"recording_format": {"primary": "podcast_conversation" "secondary": []}}}'
        first_response = MagicMock()
        first_response.choices = [MagicMock(message=MagicMock(content=malformed_json))]

        completion_mock = mocker.patch(
            "app.classifiers.llm.litellm.completion",
            return_value=first_response,
        )
        mocker.patch("app.classifiers.llm.litellm.api_key", "test-key")

        classifier = LLMClassifier()
        result = classifier.classify("Test content")

        assert "classification" in result
        assert completion_mock.call_count == 1

    def test_llm_classifier_classify_repair_with_llm_fallback(self, mocker, monkeypatch, mock_openai_response):
        """Test LLMClassifier.classify retries with JSON repair call when local fixes fail."""
        monkeypatch.setenv("LLM_API_KEY", "test-key")

        malformed_json = "Not JSON at all"
        repaired_json = json.dumps(mock_openai_response)

        first_response = MagicMock()
        first_response.choices = [MagicMock(message=MagicMock(content=malformed_json))]

        repair_response = MagicMock()
        repair_response.choices = [MagicMock(message=MagicMock(content=repaired_json))]

        completion_mock = mocker.patch(
            "app.classifiers.llm.litellm.completion",
            side_effect=[first_response, repair_response],
        )
        mocker.patch("app.classifiers.llm.litellm.api_key", "test-key")

        classifier = LLMClassifier()
        result = classifier.classify("Test content")

        assert "classification" in result
        assert completion_mock.call_count == 2

    def test_llm_classifier_classify_handles_truncated_output(self, mocker, monkeypatch, mock_openai_response):
        """Test LLMClassifier.classify handles truncated JSON via salvage or retry."""
        monkeypatch.setenv("LLM_API_KEY", "test-key")

        truncated_json = "{\"classification\": {\"audience\": {\"level\": \"general_public\""
        complete_json = json.dumps(mock_openai_response)

        first_response = MagicMock()
        first_response.choices = [MagicMock(message=MagicMock(content=truncated_json))]

        second_response = MagicMock()
        second_response.choices = [MagicMock(message=MagicMock(content=complete_json))]

        completion_mock = mocker.patch(
            "app.classifiers.llm.litellm.completion",
            side_effect=[first_response, second_response],
        )
        mocker.patch("app.classifiers.llm.litellm.api_key", "test-key")

        classifier = LLMClassifier()
        result = classifier.classify("Test content")

        assert "classification" in result
        assert completion_mock.call_count in (1, 2)

    def test_llm_classifier_salvages_truncated_tail_field(self, mocker, monkeypatch):
        """Test truncated JSON ending mid-key is salvaged into partial valid result."""
        monkeypatch.setenv("LLM_API_KEY", "test-key")

        truncated_payload = (
            '{\n'
            '  "classification": {\n'
            '    "recording_format": {\n'
            '      "primary": "podcast_conversation",\n'
            '      "secondary": ["demonstration_or_tutorial"],\n'
            '      "confidence": 0.90\n'
            '    },\n'
            '    "viewpoint_structure": {\n'
            '      "type": "interviewer_and_guest",\n'
            '      "meaningful_disagreement": false,\n'
            '      "objections'
        )

        response = MagicMock()
        response.choices = [MagicMock(message=MagicMock(content=truncated_payload))]

        completion_mock = mocker.patch(
            "app.classifiers.llm.litellm.completion",
            return_value=response,
        )
        mocker.patch("app.classifiers.llm.litellm.api_key", "test-key")

        classifier = LLMClassifier()
        result = classifier.classify("Test content")

        assert completion_mock.call_count >= 1
        assert "classification" in result
        assert result["classification"]["recording_format"]["primary"] == "podcast_conversation"

    def test_llm_classifier_classify_api_error(self, mocker, monkeypatch):
        """Test LLMClassifier.classify handles LiteLLM API errors."""
        monkeypatch.setenv("LLM_API_KEY", "test-key")

        mocker.patch("app.classifiers.llm.litellm.api_key", "test-key")
        mocker.patch(
            "app.classifiers.llm.litellm.completion",
            side_effect=RuntimeError("API Error"),
        )
        
        classifier = LLMClassifier()
        
        with pytest.raises(RuntimeError, match="LLM classification failed"):
            classifier.classify("Test content")

    def test_llm_classifier_classify_empty_response(self, mocker, monkeypatch):
        """Test LLMClassifier.classify returns graceful fallback on empty responses."""
        monkeypatch.setenv("LLM_API_KEY", "test-key")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=None))]
        
        mocker.patch("app.classifiers.llm.litellm.api_key", "test-key")
        mocker.patch("app.classifiers.llm.litellm.completion", return_value=mock_response)
        
        classifier = LLMClassifier()
        result = classifier.classify("Test content")

        assert "classification" in result
        assert "error" in result
        assert "fallback" in result["method"]
        assert result["fallback_source"] == "heuristic"

    def test_llm_classifier_heuristic_fallback_has_informative_labels(self, mocker, monkeypatch):
        """Test heuristic fallback returns useful low-confidence labels."""
        monkeypatch.setenv("LLM_API_KEY", "test-key")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=None))]

        mocker.patch("app.classifiers.llm.litellm.api_key", "test-key")
        mocker.patch("app.classifiers.llm.litellm.completion", return_value=mock_response)

        classifier = LLMClassifier()
        text = "In this podcast episode, the host demos AI coding workflows and API usage."
        result = classifier.classify(text)

        assert result["classification"]["recording_format"]["primary"] == "podcast_conversation"
        assert result["classification"]["subject_domain"]["primary"] == "computer_science_and_ai"
        assert result["classification"]["routing"]["primary"] == "general_transcript_summary"

    def test_llm_classifier_uses_secondary_model_when_configured(self, mocker, monkeypatch, mock_openai_response):
        """Test fallback model is attempted when primary model yields empty outputs."""
        monkeypatch.setenv("LLM_API_KEY", "test-key")
        monkeypatch.setenv("LLM_MODEL", "openai/local-fast")
        monkeypatch.setenv("LLM_FALLBACK_MODEL", "openai/local-deep")

        empty_response = MagicMock()
        empty_response.choices = [MagicMock(message=MagicMock(content=None))]

        valid_response = MagicMock()
        valid_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(mock_openai_response)))
        ]

        completion_mock = mocker.patch(
            "app.classifiers.llm.litellm.completion",
            side_effect=[
                empty_response,
                empty_response,
                empty_response,
                valid_response,
            ],
        )
        mocker.patch("app.classifiers.llm.litellm.api_key", "test-key")

        classifier = LLMClassifier()
        result = classifier.classify("Test content")

        assert "classification" in result
        assert completion_mock.call_count == 4

    def test_llm_classifier_classify_empty_then_minimal_retry(self, mocker, monkeypatch, mock_openai_response):
        """Test LLMClassifier retries with minimal prompt when first response is empty."""
        monkeypatch.setenv("LLM_API_KEY", "test-key")

        empty_response = MagicMock()
        empty_response.choices = [MagicMock(message=MagicMock(content=None))]

        valid_response = MagicMock()
        valid_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(mock_openai_response)))
        ]

        completion_mock = mocker.patch(
            "app.classifiers.llm.litellm.completion",
            side_effect=[empty_response, valid_response],
        )
        mocker.patch("app.classifiers.llm.litellm.api_key", "test-key")

        classifier = LLMClassifier()
        result = classifier.classify("Test content")

        assert "classification" in result
        assert completion_mock.call_count == 2

    def test_llm_classifier_with_custom_endpoint(self, mocker, monkeypatch, mock_openai_response):
        """Test LLMClassifier with custom LLM endpoint."""
        monkeypatch.setenv("LLM_API_KEY", "test-key")
        monkeypatch.setenv("LLM_MODEL", "gpt-4-turbo")
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(mock_openai_response)))
        ]
        
        monkeypatch.setenv("LLM_BASE_URL", "http://localhost:4000")
        mocker.patch("app.classifiers.llm.litellm.api_key", "test-key")
        mocker.patch("app.classifiers.llm.litellm.api_base", "http://localhost:4000")
        mocker.patch("app.classifiers.llm.litellm.completion", return_value=mock_response)
        
        # Reload config to pick up env var
        from importlib import reload
        import app.config
        reload(app.config)
        
        classifier = LLMClassifier()
        result = classifier.classify("Test content")
        
        assert result is not None
        assert "classification" in result


@pytest.mark.unit
class TestEmbeddingClassifier:
    """Tests for EmbeddingClassifier."""

    def test_embedding_classifier_init(self):
        """Test EmbeddingClassifier explicitly fails until implemented."""
        with pytest.raises(NotImplementedError, match="not implemented"):
            EmbeddingClassifier()

    def test_embedding_classifier_classify(self):
        """Test EmbeddingClassifier.classify is unavailable until implementation exists."""
        with pytest.raises(NotImplementedError, match="not implemented"):
            EmbeddingClassifier()
