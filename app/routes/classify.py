"""Classify endpoint."""
from fastapi import APIRouter
from pydantic import BaseModel
from app.classifier import classify as classify_func

router = APIRouter(tags=["classify"])


class ClassifyRequest(BaseModel):
    """Request model for classify endpoint."""
    data: str


class ClassifyResponse(BaseModel):
    """Response model for classify endpoint."""
    result: str
    confidence: float
    input: str


@router.post("/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest):
    """Classify input data."""
    result = classify_func(request.data)
    return ClassifyResponse(**result)
