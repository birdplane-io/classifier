"""Main FastAPI application."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.classifier import create_classification_service
from app.config import Settings, get_settings
from app.routes import classify, health
from app.service import ClassificationService


def create_app(
    *,
    settings: Settings | None = None,
    service: ClassificationService | None = None,
) -> FastAPI:
    """Create an application whose classifier is owned by its lifespan."""

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.classification_service = service or (
            create_classification_service(settings or get_settings())
        )
        yield

    application = FastAPI(
        title="Classifier API",
        version="1.0.0",
        lifespan=lifespan,
    )
    application.include_router(health.router, prefix="/v1")
    application.include_router(classify.router, prefix="/v1")

    @application.get("/")
    async def root() -> dict[str, str]:
        return {"message": "Classifier API", "docs": "/docs"}

    return application


app = create_app()
