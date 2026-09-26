"""FastAPI front door for the agentic compliance loop."""
from fastapi import FastAPI

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(title=settings.api_title, version=settings.api_version)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": settings.api_title}
