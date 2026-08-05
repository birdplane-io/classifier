"""Classify endpoint."""
import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.classifier import classify as classify_func

router = APIRouter(tags=["classify"])


class ClassifyRequest(BaseModel):
    """Request model for classify endpoint."""
    data: str


class ClassifyResponse(BaseModel):
    """Response model for classify endpoint."""
    classification: dict[str, Any] | None = None
    method: str
    error: str | None = None


@router.post("/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest):
    """
    Classify input data.

    Uses the classifier specified by CLASSIFIER_TYPE environment variable.

    For LLM classifier, returns the full structured classification from the LLM
    including recording_format, subject_domain, scientific_content, evidence_profile, etc.

    For Embedding classifier, returns a simplified classification.

    Example LLM response:
    ```
    {
      "classification": {
        "recording_format": {...},
        "subject_domain": {...},
        "scientific_content": {...},
        ...
      },
      "method": "llm"
    }
    ```
    """
    classifier_type = os.getenv("CLASSIFIER_TYPE", "llm").lower()
    
    try:
        result = classify_func(request.data)

        # Extract classification and method
        classification = result.pop("classification", result)
        method = result.pop("method", classifier_type)
        error = result.pop("error", None)

        return ClassifyResponse(
            classification=classification,
            method=method,
            error=error,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Classification failed: {str(e)}",
        )
    except NotImplementedError as e:
        raise HTTPException(
            status_code=501,
            detail=f"Not implemented: {str(e)}",
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error during classification: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}",
        )
