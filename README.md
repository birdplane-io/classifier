# Classifier

A minimal FastAPI server with v1 API endpoints for classification tasks.

## Setup

Install dependencies using [uv](https://astral.sh/uv/):

```bash
uv sync
```

This creates a `.venv/` virtual environment with all required packages.

## Running the Server

Start the development server:

```bash
uv run python main.py
```

The server will start on `http://localhost:8000`.

### Selecting a Classifier

Set the `CLASSIFIER_TYPE` environment variable to choose which classifier to use:

```bash
# Use LLM classifier (default)
uv run python main.py

# Use embedding classifier
CLASSIFIER_TYPE=embedding uv run python main.py
```

Supported classifiers:
- `llm` (default) — LLM-based classification
- `embedding` — Embedding-based classification

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

Classify input data.

**Request:**
```json
{
  "data": "text to classify"
}
```

**Response:**
```json
{
  "result": "llm_classified",
  "confidence": 0.85,
  "input": "text to classify",
  "method": "llm"
}
```

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

To run tests:

```bash
uv run pytest
```

## License

MIT
