# Environment configuration

Copy `.env.example` to `.env`. Pydantic validates the file during application startup; `.env` is ignored by Git.

| Variable | Required | Default | Meaning |
| --- | --- | --- | --- |
| `CLASSIFIER_BACKEND` | No | `llm` | Backend selector. `lightweight` is reserved and intentionally fails startup. |
| `LLM_BASE_URL` | Yes | — | Base URL of the OpenAI-compatible LiteLLM gateway, normally ending in `/v1`. |
| `LLM_API_KEY` | Yes | — | Key accepted by the gateway. It is held as a Pydantic secret and is never response metadata. |
| `LLM_MODEL` | No | `document-classifier` | LiteLLM model or deployment name, returned in response provenance. |
| `LLM_TIMEOUT` | No | `30` | Positive request timeout in seconds. |

Example:

```env
CLASSIFIER_BACKEND=llm
LLM_BASE_URL=http://localhost:4000/v1
LLM_API_KEY=replace-me
LLM_MODEL=document-classifier
LLM_TIMEOUT=30
```

The service uses the official OpenAI client against the gateway's `base_url`. It sends one structured-output request with temperature fixed internally at zero and SDK retries disabled. Provider choice, retry policy, rate-limit handling, and fallback models are gateway concerns, so there are no service settings for provider, temperature, maximum output tokens, or fallback models.

Configuration errors fail the application lifespan before it begins serving traffic. Runtime gateway/API failures become a sanitized HTTP 503; complete upstream responses that cannot yield the exact schema become a sanitized HTTP 502.

Do not commit real keys or transcript captures. `.llm_debug/` is ignored to preserve existing local captures, but the current service does not create or persist debug responses. A formal transcript privacy and retention policy remains deferred.
