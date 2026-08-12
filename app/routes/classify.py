"""Classify endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.classifiers import ClassificationInvalidResponse, ClassificationUnavailable
from app.models import ClassificationResponse, ClassifyRequest
from app.service import ClassificationService

router = APIRouter(tags=["classify"])


def get_classification_service(request: Request) -> ClassificationService:
    """Resolve the lifespan-owned service from application state."""

    return request.app.state.classification_service


@router.post("/classify", response_model=ClassificationResponse)
def classify(
    request: ClassifyRequest,
    service: ClassificationService = Depends(get_classification_service),
) -> ClassificationResponse:
    """Classify transcript text in FastAPI's synchronous worker pool."""

    try:
        return service.classify(request.text)
    except ClassificationUnavailable as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Classification backend is unavailable",
        ) from error
    except ClassificationInvalidResponse as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Classification backend returned an invalid response",
        ) from error
