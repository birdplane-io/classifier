"""LLM-based classifier using LiteLLM."""
from datetime import datetime, timezone
import json
import os
import re
from typing import Any

import litellm

from app.classifiers.base import Classifier
from app.config import Config
from app.prompts import load_prompt


class LLMClassifier(Classifier):
    """Classifier using Large Language Models via LiteLLM."""

    def __init__(self):
        """Initialize LLM classifier with LiteLLM configuration."""
        api_key = Config.get_llm_api_key()
        if not api_key:
            raise ValueError("LLM_API_KEY environment variable is required")

        # Configure LiteLLM
        self.model = Config.get_llm_model()
        self.api_key = api_key
        self.api_base = Config.get_llm_base_url() or None
        self.provider = Config.get_llm_provider()
        self.temperature = Config.get_llm_temperature()
        self.max_tokens = Config.get_llm_max_tokens()
        self.fallback_model = os.getenv("LLM_FALLBACK_MODEL", "").strip() or None

        # Set LiteLLM API key
        litellm.api_key = self.api_key

        # Set custom endpoint if provided
        if self.api_base:
            litellm.api_base = self.api_base

        try:
            self.system_prompt = load_prompt("classifier")
        except FileNotFoundError as e:
            raise RuntimeError(f"Failed to load classifier prompt: {e}")

    def classify(self, data: str) -> dict[str, Any]:
        """
        Classify input using LiteLLM.

        LiteLLM can route to:
        - OpenAI (gpt-4, gpt-3.5-turbo)
        - Anthropic (claude-3-opus, claude-3-sonnet)
        - Custom endpoints (local models, LiteLLM proxy)
        - Other providers
        
        Args:
            data: Input text to classify

        Returns:
            Classification result with full structure from LLM

        Raises:
            ValueError: If API response is invalid
            RuntimeError: If API call fails
        """
        try:
            classification = self._classify_with_fallback(data)

            # Add method metadata
            method = f"llm ({self.model})"
            if classification.get("error"):
                method = f"{method} fallback"
            classification["method"] = method

            return classification

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")
        except litellm.APIConnectionError as e:
            raise RuntimeError(f"Failed to connect to LLM endpoint: {e}")
        except litellm.RateLimitError as e:
            raise RuntimeError(f"LLM rate limit exceeded: {e}")
        except litellm.AuthenticationError as e:
            raise RuntimeError(f"LLM authentication failed: {e}")
        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(f"LLM classification failed: {e}")

    def _classify_with_fallback(self, data: str) -> dict[str, Any]:
        """Attempt classification via multiple strategies, then return graceful fallback."""
        base_attempts = [
            {"label": "full_prompt", "compact": False, "minimal": False},
            {"label": "compact_prompt", "compact": True, "minimal": False},
            {"label": "minimal_schema", "compact": True, "minimal": True},
        ]
        models = [self.model]
        if self.fallback_model and self.fallback_model != self.model:
            models.append(self.fallback_model)

        failures: list[str] = []

        for model_name in models:
            for attempt in base_attempts:
                response_text = self._request_classification(
                    data,
                    model_name=model_name,
                    compact=attempt["compact"],
                    minimal=attempt["minimal"],
                )

                if not response_text:
                    failures.append(f"{model_name}/{attempt['label']}: empty response")
                    continue

                try:
                    return self._parse_llm_json(response_text)
                except ValueError as e:
                    failures.append(f"{model_name}/{attempt['label']}: {e}")

        return self._build_graceful_fallback(data=data, failures=failures)

    def _build_graceful_fallback(self, data: str, failures: list[str]) -> dict[str, Any]:
        """Return a valid low-confidence payload when model output is unavailable."""
        preview = data[:120].strip().replace("\n", " ")
        if not preview:
            preview = "No transcript content provided."

        return {
            "classification": {
                "recording_format": {
                    "primary": self._heuristic_recording_format(data),
                    "secondary": [],
                    "confidence": 0.3,
                },
                "subject_domain": {
                    "primary": self._heuristic_subject_domain(data),
                    "secondary": [],
                    "confidence": 0.3,
                },
                "scientific_content": {
                    "level": self._heuristic_scientific_level(data),
                    "functions": self._heuristic_scientific_functions(data),
                    "basis": "Estimated by deterministic keyword-based fallback.",
                    "confidence": 0.25,
                },
                "communicative_purpose": {
                    "primary": self._heuristic_purpose(data),
                    "secondary": [],
                    "confidence": 0.25,
                },
                "audience": {
                    "level": self._heuristic_audience(data),
                    "basis": "Estimated from lexical style and keyword cues.",
                    "confidence": 0.25,
                },
                "evidence_profile": {
                    "empirical_evidence": "low",
                    "quantitative_data": "low",
                    "methodological_detail": "low",
                    "source_attribution": "unknown",
                    "causal_reasoning": "low",
                    "philosophical_reasoning": "low",
                    "normative_reasoning": "low",
                    "policy_argument": "low",
                    "personal_anecdote": "low",
                    "speculation": "moderate",
                },
                "viewpoint_structure": {
                    "type": "unclear",
                    "meaningful_disagreement": False,
                    "objections_addressed": False,
                    "consensus_reached": False,
                    "unresolved_disagreement": False,
                    "notes": "Model output unavailable.",
                },
                "transcript_quality": {
                    "overall": "uncertain",
                    "word_recognition": "uncertain",
                    "punctuation": "uncertain",
                    "speaker_turn_separation": "uncertain",
                    "speaker_identification": "uncertain",
                    "timestamps": "uncertain",
                    "completeness": "uncertain",
                    "repetition_resistance": "uncertain",
                    "flags": ["other"],
                    "notes": "Classification degraded due to unusable model response.",
                },
                "routing": {
                    "primary": self._heuristic_route(data),
                    "secondary": ["manual_review_required"],
                    "preprocessing_required": [],
                    "reason": "LLM output unavailable after multiple strategies; heuristic fallback applied.",
                },
            },
            "content_outline": {
                "main_topic": self._heuristic_main_topic(data),
                "major_subtopics": [],
                "named_speakers_or_roles": [],
                "languages_detected": [],
            },
            "classification_notes": {
                "ambiguities": failures,
                "unsupported_inferences_avoided": [
                    f"Fallback used for input preview: {preview}"
                ],
                "overall_confidence": 0.25,
            },
            "error": (
                "LLM response was empty or invalid after multiple attempts. "
                "Returned deterministic heuristic fallback classification."
            ),
            "fallback_source": "heuristic",
        }

    @staticmethod
    def _heuristic_recording_format(data: str) -> str:
        text = data.lower()
        if any(k in text for k in ["host", "guest", "podcast", "episode"]):
            return "podcast_conversation"
        if any(k in text for k in ["interviewer", "interview", "question", "q:", "a:"]):
            return "expert_interview"
        if any(k in text for k in ["lecture", "today we will", "class", "students"]):
            return "lecture"
        if any(k in text for k in ["meeting", "agenda", "action item"]):
            return "meeting"
        if any(k in text for k in ["tutorial", "demo", "step by step"]):
            return "demonstration_or_tutorial"
        return "mixed_format"

    @staticmethod
    def _heuristic_subject_domain(data: str) -> str:
        text = data.lower()
        domain_keywords = [
            ("computer_science_and_ai", ["ai", "model", "prompt", "code", "software", "llm", "api"]),
            ("medicine_and_health", ["patient", "clinical", "disease", "health", "treatment"]),
            ("politics_and_current_affairs", ["government", "election", "policy", "minister"]),
            ("economics_and_business", ["market", "revenue", "business", "startup", "sales"]),
            ("education", ["course", "teacher", "student", "lesson"]),
        ]
        for domain, keywords in domain_keywords:
            if any(k in text for k in keywords):
                return domain
        return "general_or_mixed"

    @staticmethod
    def _heuristic_scientific_level(data: str) -> str:
        text = data.lower()
        technical_terms = ["hypothesis", "dataset", "experiment", "method", "results", "statistical"]
        score = sum(1 for term in technical_terms if term in text)
        if score >= 4:
            return "substantive"
        if score >= 2:
            return "light"
        return "none"

    @staticmethod
    def _heuristic_scientific_functions(data: str) -> list[str]:
        level = LLMClassifier._heuristic_scientific_level(data)
        if level == "none":
            return ["not_applicable"]
        if level == "light":
            return ["science_communication", "concept_explanation"]
        return ["concept_explanation", "methodology_description", "results_interpretation"]

    @staticmethod
    def _heuristic_purpose(data: str) -> str:
        text = data.lower()
        if any(k in text for k in ["how to", "step", "tutorial", "guide"]):
            return "teach"
        if any(k in text for k in ["debate", "argue", "disagree"]):
            return "debate"
        if any(k in text for k in ["announc", "launch", "introducing", "new feature"]):
            return "promote"
        if any(k in text for k in ["explain", "why", "because"]):
            return "explain"
        return "inform"

    @staticmethod
    def _heuristic_audience(data: str) -> str:
        text = data.lower()
        if any(k in text for k in ["beginner", "new to", "intro"]):
            return "general_public"
        if any(k in text for k in ["api", "architecture", "implementation", "sdk"]):
            return "interested_non_specialist"
        return "general_public"

    @staticmethod
    def _heuristic_route(data: str) -> str:
        fmt = LLMClassifier._heuristic_recording_format(data)
        if fmt == "meeting":
            return "meeting_summary"
        if fmt in {"lecture", "demonstration_or_tutorial"}:
            return "technical_tutorial_analysis"
        return "general_transcript_summary"

    @staticmethod
    def _heuristic_main_topic(data: str) -> str:
        text = data.strip()
        if not text:
            return "unknown"
        first_sentence = re.split(r"[.!?\n]", text, maxsplit=1)[0].strip()
        return first_sentence[:120] if first_sentence else "unknown"

    def _request_classification(
        self,
        data: str,
        model_name: str | None = None,
        compact: bool = False,
        minimal: bool = False,
    ) -> str | None:
        """Request classification JSON from LLM, optionally with compact output constraints."""
        if minimal:
            minimal_prompt = (
                "You are a transcript classifier. Return only valid JSON, no markdown, no extra text. "
                "Use this exact structure with concise values: "
                '{"classification":{"recording_format":{"primary":"","confidence":0.0},'
                '"subject_domain":{"primary":"","confidence":0.0},'
                '"scientific_content":{"level":"","confidence":0.0},'
                '"routing":{"primary":"","reason":""}},'
                '"classification_notes":{"overall_confidence":0.0}}'
            )
            messages = [
                {"role": "system", "content": minimal_prompt},
                {"role": "user", "content": data},
            ]
            request_temperature = 0.0
            request_max_tokens = min(self.max_tokens, 900)
        elif compact:
            compact_instruction = (
                "Return only valid JSON matching the required structure. "
                "Keep text fields concise (max 12 words each) to avoid truncation. "
                "No markdown, no extra text."
            )
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "system", "content": compact_instruction},
                {"role": "user", "content": data},
            ]
            request_temperature = self.temperature
            request_max_tokens = self.max_tokens
        else:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": data},
            ]
            request_temperature = self.temperature
            request_max_tokens = self.max_tokens

        response = litellm.completion(
            model=model_name or self.model,
            messages=messages,
            temperature=request_temperature,
            max_tokens=request_max_tokens,
        )
        return self._extract_response_text(response)

    @staticmethod
    def _extract_response_text(response: Any) -> str | None:
        """Extract the model text content from LiteLLM response formats."""
        if isinstance(response, dict):
            choice = response.get("choices", [{}])[0]
            content = choice.get("message", {}).get("content")
            text = LLMClassifier._normalize_content_to_text(content)
            if text:
                return text
            text = LLMClassifier._normalize_content_to_text(choice.get("text"))
            if text:
                return text
            return None

        choices = getattr(response, "choices", None)
        if not choices:
            return None

        first_choice = choices[0]
        message = getattr(first_choice, "message", None)
        content = getattr(message, "content", None) if message is not None else None
        text = LLMClassifier._normalize_content_to_text(content)
        if text:
            return text

        text = LLMClassifier._normalize_content_to_text(getattr(first_choice, "text", None))
        if text:
            return text

        return None

    @staticmethod
    def _normalize_content_to_text(content: Any) -> str | None:
        """Normalize provider content variants into a plain text string."""
        if content is None:
            return None

        if isinstance(content, str):
            normalized = content.strip()
            return normalized or None

        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    if item.strip():
                        parts.append(item.strip())
                    continue
                if isinstance(item, dict):
                    text = item.get("text") or item.get("content")
                    if isinstance(text, str) and text.strip():
                        parts.append(text.strip())
            if parts:
                return "\n".join(parts)
            return None

        if isinstance(content, dict):
            text = content.get("text") or content.get("content")
            if isinstance(text, str):
                normalized = text.strip()
                return normalized or None
            return None

        return None

    @staticmethod
    def _extract_json_candidate(text: str) -> str:
        """Extract the most likely JSON object from model output."""
        stripped = text.strip()

        fence_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", stripped, flags=re.DOTALL)
        if fence_match:
            stripped = fence_match.group(1).strip()

        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end >= start:
            return stripped[start : end + 1]

        return stripped

    @staticmethod
    def _remove_trailing_commas(text: str) -> str:
        """Normalize a common JSON formatting issue from LLM output."""
        return re.sub(r",\s*([}\]])", r"\1", text)

    @staticmethod
    def _insert_missing_commas(text: str) -> str:
        """Best-effort repair for missing commas between adjacent JSON values."""
        result: list[str] = []
        in_string = False
        escaped = False

        def previous_non_whitespace() -> str | None:
            for ch in reversed(result):
                if not ch.isspace():
                    return ch
            return None

        for ch in text:
            if in_string:
                result.append(ch)
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                prev = previous_non_whitespace()
                if prev and (
                    prev in ('"', '}', ']')
                    or prev.isdigit()
                    or prev in ('e', 'E', 'l')
                ) and prev not in (':', ',', '{', '['):
                    result.append(',')
                    result.append(' ')
                in_string = True
                result.append(ch)
                continue

            if ch in ('{', '['):
                prev = previous_non_whitespace()
                if prev and (
                    prev in ('"', '}', ']')
                    or prev.isdigit()
                    or prev in ('e', 'E', 'l')
                ) and prev not in (':', ',', '{', '['):
                    result.append(',')
                    result.append(' ')

            result.append(ch)

        return ''.join(result)

    @staticmethod
    def _is_likely_truncated_json(text: str) -> bool:
        """Detect likely truncation by unbalanced JSON delimiters or unterminated strings."""
        in_string = False
        escaped = False
        brace_depth = 0
        bracket_depth = 0

        for ch in text:
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
            elif ch == '{':
                brace_depth += 1
            elif ch == '}':
                brace_depth -= 1
            elif ch == '[':
                bracket_depth += 1
            elif ch == ']':
                bracket_depth -= 1

        return in_string or brace_depth > 0 or bracket_depth > 0

    def _repair_json_with_llm(self, invalid_json: str) -> str | None:
        """Ask the model for a strict JSON rewrite when parsing fails."""
        try:
            response = litellm.completion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You repair malformed JSON. Return only valid JSON with no markdown "
                            "and no extra text. Preserve keys and values exactly when possible."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Rewrite this as valid JSON only:\n\n"
                            f"{invalid_json}"
                        ),
                    },
                ],
                temperature=0.0,
                max_tokens=min(self.max_tokens, 2000),
            )
            return self._extract_response_text(response)
        except Exception:
            # Best-effort fallback only; caller will raise the original parse failure.
            return None

    def _parse_llm_json(self, response_text: str) -> dict[str, Any]:
        """Parse LLM output as JSON with robust fallback strategies."""
        candidates = [
            response_text,
            self._extract_json_candidate(response_text),
        ]

        parse_error: json.JSONDecodeError | None = None

        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError as e:
                parse_error = e

            try:
                return json.loads(self._remove_trailing_commas(candidate))
            except json.JSONDecodeError as e:
                parse_error = e

            try:
                repaired = self._insert_missing_commas(candidate)
                repaired = self._remove_trailing_commas(repaired)
                return json.loads(repaired)
            except json.JSONDecodeError as e:
                parse_error = e

            if self._is_likely_truncated_json(candidate):
                salvaged = self._salvage_truncated_json(candidate)
                if salvaged is not None:
                    return salvaged

        repaired_text = self._repair_json_with_llm(response_text)
        if repaired_text:
            repaired_candidate = self._extract_json_candidate(repaired_text)
            try:
                return json.loads(repaired_candidate)
            except json.JSONDecodeError as e:
                parse_error = e

            if self._is_likely_truncated_json(repaired_candidate):
                salvaged = self._salvage_truncated_json(repaired_candidate)
                if salvaged is not None:
                    return salvaged

        if parse_error is None:
            raise ValueError("Failed to parse LLM response as JSON")

        self._capture_parse_failure(response_text=response_text, parse_error=parse_error)

        raise ValueError(f"Failed to parse LLM response as JSON: {parse_error}")

    @staticmethod
    def _close_open_json_structures(text: str) -> str:
        """Close unterminated strings and JSON containers for a best-effort parse."""
        stack: list[str] = []
        in_string = False
        escaped = False

        for ch in text:
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
            elif ch in ('{', '['):
                stack.append(ch)
            elif ch == '}' and stack and stack[-1] == '{':
                stack.pop()
            elif ch == ']' and stack and stack[-1] == '[':
                stack.pop()

        candidate = text.rstrip()
        while candidate.endswith((',', ':')):
            candidate = candidate[:-1].rstrip()

        if in_string:
            candidate += '"'

        for opener in reversed(stack):
            candidate += '}' if opener == '{' else ']'

        return candidate

    def _salvage_truncated_json(self, text: str) -> dict[str, Any] | None:
        """Recover a parseable partial JSON object from truncated model output."""
        candidate = self._extract_json_candidate(text).rstrip()
        if not candidate:
            return None

        # First attempt: close current structure as-is.
        try:
            return json.loads(self._close_open_json_structures(candidate))
        except json.JSONDecodeError:
            pass

        # If tail contains an incomplete key/value, trim back to previous safe comma.
        comma_positions: list[int] = []
        in_string = False
        escaped = False
        for idx, ch in enumerate(candidate):
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
            elif ch == ',':
                comma_positions.append(idx)

        for pos in reversed(comma_positions):
            trimmed = candidate[:pos].rstrip()
            if not trimmed:
                continue
            try:
                return json.loads(self._close_open_json_structures(trimmed))
            except json.JSONDecodeError:
                continue

        return None

    def _capture_parse_failure(self, response_text: str, parse_error: json.JSONDecodeError) -> None:
        """Persist raw failed LLM output to disk when debug capture is enabled."""
        capture_enabled = os.getenv("LLM_DEBUG_CAPTURE", "false").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if not capture_enabled:
            return
        capture_dir = os.getenv("LLM_DEBUG_DIR", ".llm_debug")
        os.makedirs(capture_dir, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        filename = f"parse_failure_{timestamp}.json"
        path = os.path.join(capture_dir, filename)

        payload = {
            "model": self.model,
            "error": str(parse_error),
            "raw_response": response_text,
            "json_candidate": self._extract_json_candidate(response_text),
        }

        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
        except OSError:
            # Debug capture should never break classification flow.
            return
