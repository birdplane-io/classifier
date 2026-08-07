"""Main FastAPI application."""
import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI
from app.routes import health, classify
from app.config import Config

# Load and validate configuration
try:
    Config.validate()
except ValueError as e:
    raise RuntimeError(f"Configuration error: {e}")

app = FastAPI(title="Classifier API", version="1.0.0")

# Create v1 router
v1_routes = [
    health.router,
    classify.router,
]

for router in v1_routes:
    app.include_router(router, prefix="/v1")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Classifier API",
        "docs": "/docs",
        "classifier": os.getenv("CLASSIFIER_TYPE", "llm").lower(),
    }
