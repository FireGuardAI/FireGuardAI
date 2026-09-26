"""FastAPI application entry point.

Grows as each build step wires in a new piece — the Groq intake engine
(Step 2), the /api/v1/intake and /api/v1/intake/document endpoints
(Step 3), production hardening (Step 4). See README.md's build-status
checklist for what's done.
"""
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.exceptions import (
    GuardrailRejection,
    IntakeEngineError,
    IntakeResponseParsingError,
    PdfExtractionError,
)
from app.logger import get_logger
from app.schemas import RawBuildingInput, SanitizedBuildingDetails
from app.services.intake_engine import IntakeEngine
from app.services.pdf_extraction import extract_text

logger = get_logger(__name__)

app = FastAPI(title=settings.api_title, version=settings.api_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Loaded once at startup (see on_startup below), never per-request.
intake_engine: IntakeEngine | None = None


def _raise_for_guardrail(exc: GuardrailRejection) -> None:
    status_code = 400 if exc.reason == "unsafe_input" else 422
    raise HTTPException(status_code=status_code, detail=str(exc)) from exc


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


@app.post("/api/v1/intake", response_model=SanitizedBuildingDetails)
@limiter.limit(settings.intake_rate_limit)
async def intake_text(request: Request, body: RawBuildingInput) -> SanitizedBuildingDetails:
    if intake_engine is None:
        raise HTTPException(status_code=503, detail="Intake engine not initialized")

    try:
        details = await intake_engine.process_input(body.raw_prompt)
    except GuardrailRejection as exc:
        _raise_for_guardrail(exc)
    except IntakeResponseParsingError as exc:
        raise HTTPException(
            status_code=502, detail=f"Groq returned an unusable response: {exc}"
        ) from exc
    except IntakeEngineError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return details.model_copy(update={"raw_description": body.raw_prompt})


@app.post("/api/v1/intake/document", response_model=SanitizedBuildingDetails)
@limiter.limit(settings.document_rate_limit)
async def intake_document(request: Request, file: UploadFile = File(...)) -> SanitizedBuildingDetails:
    if intake_engine is None:
        raise HTTPException(status_code=503, detail="Intake engine not initialized")

    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=415, detail="A PDF document is required")

    contents = await file.read(settings.upload_max_bytes + 1)
    if len(contents) > settings.upload_max_bytes:
        raise HTTPException(status_code=413, detail="Uploaded document is too large")
    if not contents:
        raise HTTPException(status_code=422, detail="Uploaded document is empty")

    try:
        raw_text = extract_text(contents)
    except PdfExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        details = await intake_engine.process_input(raw_text)
    except GuardrailRejection as exc:
        _raise_for_guardrail(exc)
    except IntakeResponseParsingError as exc:
        raise HTTPException(
            status_code=502, detail=f"Groq returned an unusable response: {exc}"
        ) from exc
    except IntakeEngineError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return details.model_copy(update={"raw_description": raw_text})


@app.on_event("startup")
async def on_startup() -> None:
    global intake_engine
    logger.info(f"{settings.api_title} v{settings.api_version} starting up")
    intake_engine = IntakeEngine()
