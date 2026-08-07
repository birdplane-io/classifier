# Classifier

A minimal FastAPI server with v1 API endpoints for classification tasks.

## Implementation Documentation

For architecture and implementation details, see `IMPLEMENTATION.md`.

## Setup

Install dependencies using [uv](https://astral.sh/uv/):

```bash
uv sync
```

This creates a `.venv/` virtual environment with all required packages.

### Environment Configuration

Copy `.env.example` to `.env` and fill in your LLM API key:

```bash
cp .env.example .env
```

Then edit `.env`:

```env
LLM_API_KEY=sk-your-api-key-here
LLM_MODEL=gpt-4-turbo
CLASSIFIER_TYPE=llm
```

The `.env` file is automatically loaded by the application at startup using `python-dotenv`. It is **not** committed to git for security (see `.gitignore`).

#### LLM Provider Options

The classifier uses **LiteLLM** to support multiple LLM providers:

**OpenAI (default):**
```env
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4-turbo
LLM_PROVIDER=openai
```

**Anthropic Claude:**
```env
LLM_API_KEY=sk-ant-...
LLM_MODEL=claude-3-opus-20240229
LLM_PROVIDER=anthropic
```

**Local Model (via Ollama or similar):**
```env
LLM_API_KEY=not-needed
LLM_MODEL=ollama/llama2
LLM_BASE_URL=http://localhost:11434
```

**Custom OpenAI-compatible Endpoint:**
```env
LLM_API_KEY=your-api-key
LLM_MODEL=your-model-name
LLM_BASE_URL=https://api.custom-provider.com/v1
```

**LiteLLM Proxy Server:**
```env
LLM_API_KEY=your-key
LLM_MODEL=gpt-4-turbo
LLM_BASE_URL=http://localhost:4000
```

#### Required Environment Variables

- `LLM_API_KEY` — API key for your LLM provider

#### Optional Environment Variables

- `LLM_MODEL` — Model name (default: `gpt-4-turbo`)
- `LLM_TEMPERATURE` — Temperature for responses (default: `0.0`)
- `LLM_MAX_TOKENS` — Max tokens in response (default: `4000`)
- `LLM_BASE_URL` — Custom endpoint URL (optional, leave empty for provider defaults)
- `LLM_PROVIDER` — Provider name (default: `openai`, auto-inferred from model if omitted)
- `CLASSIFIER_TYPE` — Classifier to use (default: `llm`)

## Running the Server

Start the development server:

```bash
uv run python main.py
```

The server will start on `http://localhost:8000`.

### LLM Provider Support

The classifier uses **LiteLLM** to support multiple LLM providers:

- **OpenAI** — gpt-4-turbo, gpt-3.5-turbo, etc.
- **Anthropic** — claude-3-opus, claude-3-sonnet, etc.
- **Local Models** — Ollama, LM Studio, vLLM, etc.
- **Custom Endpoints** — OpenAI-compatible servers, LiteLLM proxy, etc.
- **Other Providers** — Cohere, Replicate, Together AI, etc.

### Classifier Selection

Set the `CLASSIFIER_TYPE` environment variable to choose which classifier to use:

```bash
# Use LLM classifier (default)
uv run python main.py

# Use embedding classifier
CLASSIFIER_TYPE=embedding uv run python main.py
```

Supported classifiers:
- `llm` (default) — LLM-based classification via LiteLLM
- `embedding` — Embedding-based classification (stub)

## API Documentation

Once running, view interactive API docs at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints

### GET `/v1/health`

Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

### POST `/v1/classify`

Classify input data using the selected classifier.

**Request:**
```json
{
  "data": "Full transcript or text to classify"
}
```

**Response (LLM Classifier):**
```json
{
  "classification": {
    "recording_format": {
      "primary": "podcast_conversation",
      "secondary": ["expert_interview"],
      "confidence": 0.92
    },
    "subject_domain": {
      "primary": "neuroscience_and_psychology",
      "secondary": ["philosophy_and_ethics"],
      "confidence": 0.88
    },
    "scientific_content": {
      "level": "substantive",
      "functions": ["concept_explanation", "research_report"],
      "basis": "Discussion of neuroscience research, methods, and findings",
      "confidence": 0.85
    },
    "communicative_purpose": {
      "primary": "explain",
      "secondary": ["inform"],
      "confidence": 0.90
    },
    "audience": {
      "level": "interested_non_specialist",
      "basis": "Mix of technical concepts with accessible explanations",
      "confidence": 0.82
    },
    "evidence_profile": {
      "empirical_evidence": "high",
      "quantitative_data": "moderate",
      "methodological_detail": "moderate",
      "source_attribution": "moderate",
      "causal_reasoning": "high",
      "philosophical_reasoning": "low",
      "normative_reasoning": "low",
      "policy_argument": "none",
      "personal_anecdote": "low",
      "speculation": "moderate"
    },
    "viewpoint_structure": {
      "type": "interviewer_and_guest",
      "meaningful_disagreement": false,
      "objections_addressed": true,
      "consensus_reached": true,
      "unresolved_disagreement": false,
      "notes": "Collaborative discussion without substantive disagreement"
    },
    "transcript_quality": {
      "overall": "good",
      "word_recognition": "good",
      "punctuation": "usable",
      "speaker_turn_separation": "good",
      "speaker_identification": "usable",
      "timestamps": "good",
      "completeness": "good",
      "repetition_resistance": "good",
      "flags": [],
      "notes": "Clean transcript with minor punctuation issues"
    },
    "routing": {
      "primary": "science_panel_analysis",
      "secondary": ["speaker_dynamics_analysis"],
      "preprocessing_required": [],
      "reason": "Substantive scientific discussion in accessible format; suitable for direct analysis"
    }
  },
  "method": "llm"
}
```

The LLM classifier returns a comprehensive structured classification following the transcript classification schema. For the Embedding classifier, a simpler classification is returned.

## Project Structure

```
classifier/
├── README.md
├── pyproject.toml          # Project metadata & dependencies
├── uv.lock                 # Locked dependency versions
├── main.py                 # Server entry point
└── app/
    ├── __init__.py
    ├── main.py             # FastAPI app setup
    ├── classifier.py       # Classifier factory
    └── classifiers/        # Classifier implementations
    │   ├── __init__.py
    │   ├── base.py         # Base Classifier class
    │   ├── llm.py          # LLMClassifier (stub)
    │   └── embedding.py    # EmbeddingClassifier (stub)
    └── routes/
        ├── __init__.py
        ├── health.py       # Health check endpoint
        └── classify.py     # Classification endpoint
```

## Development

To add development dependencies:

```bash
uv sync --extra dev
```

### Running Tests

Run all tests:

```bash
uv run pytest
```

Run tests with verbose output:

```bash
uv run pytest -v
```

Run specific test file:

```bash
uv run pytest tests/test_health.py
```

Run tests matching a pattern:

```bash
uv run pytest -k "test_classify"
```

Run with coverage:

```bash
uv run pytest --cov=app
```

Tests are organized into:
- `tests/test_health.py` — Health check endpoint tests
- `tests/test_classify.py` — Classification endpoint tests
- `tests/test_classifiers.py` — Classifier implementation tests
- `tests/test_config.py` — Configuration tests
- `tests/conftest.py` — Shared pytest fixtures and mocks

## License

MIT
