"""FastAPI application entry point.

Grows as each build step wires in a new piece — the Groq intake engine
(Step 2), the /api/v1/intake endpoint (Step 3), production hardening
(Step 4). See README.md's build-status checklist for what's done.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.exceptions import IntakeEngineError
from app.logger import get_logger
from app.services.intake_engine import IntakeEngine

logger = get_logger(__name__)

app = FastAPI(title=settings.api_title, version=settings.api_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Loaded once at startup (see on_startup below), never per-request.
intake_engine: IntakeEngine | None = None


@app.get("/health")
async def health() -> dict:
    """Basic liveness check — confirms the API process itself is up.
    Does NOT check Groq; that gets /health/groq."""
    return {"status": "ok", "service": settings.api_title}


@app.get("/health/groq")
async def health_groq() -> dict:
    """Makes one real (minimal) Groq API call. Not polled automatically —
    call it manually."""
    if intake_engine is None:
        raise HTTPException(status_code=503, detail="Intake engine not initialized")
    try:
        await intake_engine.self_check()
    except IntakeEngineError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "ok", "model": settings.groq_model_name}


@app.on_event("startup")
async def on_startup() -> None:
    global intake_engine
    logger.info(f"{settings.api_title} v{settings.api_version} starting up")
    intake_engine = IntakeEngine()
