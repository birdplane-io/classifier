# Classifier

A schema-first FastAPI service that routes transcript text by recording format and subject, while reporting transcript quality problems. Version 1 uses an OpenAI-compatible LiteLLM gateway and returns one strict, versioned classification shape.

## Requirements and setup

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- A running LiteLLM gateway with a model that supports OpenAI structured outputs

```bash
uv sync --extra dev
cp .env.example .env
```

Set the LiteLLM URL and key in `.env`, then start the API:

```bash
uv run python main.py
```

See [docs/environment.md](docs/environment.md) for every setting and the gateway topology. The application validates configuration and builds the classifier during FastAPI startup. Missing credentials, invalid values, or `CLASSIFIER_BACKEND=lightweight` prevent startup rather than producing fabricated labels.

## API contract

`POST /v1/classify` accepts exactly one non-blank `text` field:

```json
{
  "text": "Host: What did your trial measure? Guest: We compared two groups."
}
```

It returns the canonical `ClassificationResult` plus immutable provenance:

```json
{
  "classification": {
    "format": "interview",
    "route": "science",
    "quality_flags": []
  },
  "metadata": {
    "backend": "llm",
    "schema_version": "1",
    "model": "document-classifier",
    "prompt_version": "1"
  }
}
```

Valid formats are `interview`, `monologue`, `conversation`, `panel`, `lecture`, and `presentation`. Valid routes are `science`, `current_affairs`, `education`, `business`, `arts_and_culture`, and `general`. Quality flags are independently composable: `incomplete`, `poor_audio`, `overlapping_speech`, `speaker_labels_missing`, `repetition`, and `non_english`.

Every request makes at most one application-level `chat.completions.parse` call with temperature zero and the canonical Pydantic model as its response format. The service does not repair JSON, retry prompts, select fallback models, normalize near-matching labels, or return heuristic classifications. Retry and model-fallback policy belongs at the LiteLLM gateway.

### Errors

- `422 Unprocessable Entity`: blank text, the old request shape, extra fields, or another request validation failure.
- `502 Bad Gateway`: refusal, truncation, empty choices, missing parsed output, or output that does not match the schema.
- `503 Service Unavailable`: connection, timeout, rate-limit, authentication, or upstream API/status failure.

Provider exception text is never included in HTTP responses. `GET /v1/health` returns `{"status":"ok"}` after successful application startup.

### Breaking change

This version intentionally replaces the former `{"data": ...}` request and arbitrary result dictionaries. Clients must send `{"text": ...}` and consume the typed `classification` and `metadata` objects shown above. Review status and training-label persistence are not part of the live API.

## Evaluation

The checked-in `evaluation/data/classifier-v1.jsonl` contains 18 privacy-safe, synthetic, taxonomy-reviewed examples. It covers every format, route, and quality flag, including clean negative cases.

Evaluate a deterministic prediction JSONL file:

```bash
uv run python -m evaluation.evaluator --predictions predictions.jsonl
```

Each prediction line has this shape:

```json
{"id":"v1-001","classification":{"format":"interview","route":"science","quality_flags":[]}}
```

The report includes format and route accuracy, per-class precision/recall/F1, confusion matrices, and quality-flag micro/macro/per-label metrics. Dataset labels and predictions are validated through the same `ClassificationResult` model used by the LLM and API.

Live evaluation is explicit, calls the configured gateway, and must remain outside CI:

```bash
uv run python -m evaluation.evaluator --live
```

## Versioning

`CLASSIFICATION_SCHEMA_VERSION` and `PROMPT_VERSION` are independent:

- Changing a label, removing one, adding one, or changing a taxonomy meaning requires a schema-version bump and a newly reviewed dataset version.
- A prompt-only wording or instruction change that preserves taxonomy meaning requires a prompt-version bump.
- Metadata records both versions and the configured model on every successful response.

## Development

```bash
uv run --extra dev pytest
```

The lightweight backend, training-label persistence, teacher/student collection, confidence-based hybrid routing, and a documented privacy/retention policy are deliberately deferred. Until those exist, the service performs no training-record or debug-response writes.
