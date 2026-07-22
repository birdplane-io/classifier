"""Main FastAPI application."""
from fastapi import FastAPI
from app.routes import health, classify

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
    return {"message": "Classifier API", "docs": "/docs"}
