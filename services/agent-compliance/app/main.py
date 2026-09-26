import asyncio

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.exceptions import ComplianceEngineError, LLMResponseParsingError, RetrievalClientError
from app.logger import get_logger
from app.middleware import RequestLoggingMiddleware
from app.schemas import AuditRequest, ComplianceResponse, ComplianceRuleCheck
from app.services.audit_topics import select_topics
from app.services.compliance_engine import ComplianceEngine
from app.services.retrieval_client import RetrievalClient

logger = get_logger(__name__)

app = FastAPI(title=settings.api_title, version=settings.api_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


retrieval_client: RetrievalClient | None = None
compliance_engine: ComplianceEngine | None = None


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": settings.api_title}


@app.get("/health/retrieval")
async def health_retrieval() -> dict:
    if retrieval_client is None:
        raise HTTPException(
            status_code=503, detail="Retrieval client not initialized"
        )
    try:
        upstream_health = await retrieval_client.health_check()
    except RetrievalClientError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "ok", "retrieval_agent": upstream_health}


@app.get("/health/gemini")
async def health_gemini() -> dict:
    if compliance_engine is None:
        raise HTTPException(
            status_code=503, detail="Compliance engine not initialized"
        )
    try:
        await compliance_engine.self_check()
    except ComplianceEngineError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "ok", "model": settings.gemini_model_name}


@app.get("/health/all")
async def health_all() -> dict:
    dependencies: dict = {}
    overall_ok = True

    if retrieval_client is None:
        dependencies["retrieval"] = {"status": "error", "detail": "not initialized"}
        overall_ok = False
    else:
        try:
            dependencies["retrieval"] = {
                "status": "ok",
                "detail": await retrieval_client.health_check(),
            }
        except RetrievalClientError as exc:
            dependencies["retrieval"] = {"status": "error", "detail": str(exc)}
            overall_ok = False

    if compliance_engine is None:
        dependencies["gemini"] = {"status": "error", "detail": "not initialized"}
        overall_ok = False
    else:
        try:
            await compliance_engine.self_check()
            dependencies["gemini"] = {"status": "ok"}
        except ComplianceEngineError as exc:
            dependencies["gemini"] = {"status": "error", "detail": str(exc)}
            overall_ok = False

    return {"status": "ok" if overall_ok else "degraded", "dependencies": dependencies}


def _dedupe_chunks(chunk_lists: list[list[dict]]) -> list[dict]:
    seen: set[str] = set()
    deduped: list[dict] = []
    for chunks in chunk_lists:
        for chunk in chunks:
            chunk_id = chunk.get("id")
            if chunk_id in seen:
                continue
            seen.add(chunk_id)
            deduped.append(chunk)
    return deduped


def _score_audit(checks: list[ComplianceRuleCheck]) -> tuple[str, float]:
    """Deterministic overall_status/compliance_score from the individual
    check verdicts — never left to the LLM's own judgment call, since
    that produced contradictory verdicts (e.g. 100% "compliant" with more
    unresolved gaps than a separate run that scored 50% "non-compliant"
    for the same building)."""
    # NOT_APPLICABLE checks are excluded from both sides of the ratio —
    # a building shouldn't score higher just because more of its
    # checklist happened not to apply to it (e.g. a low-rise building
    # skips the high-rise bundle entirely; that's not the same as
    # "meeting" those requirements).
    scored = [c for c in checks if c.status != "NOT_APPLICABLE"]
    compliant = sum(c.status == "COMPLIANT" for c in scored)
    non_compliant = sum(c.status == "NON_COMPLIANT" for c in scored)
    partial = sum(c.status == "PARTIAL" for c in scored)
    total = len(scored) or 1
    score = round(100 * (compliant + 0.5 * partial) / total, 1)

    if non_compliant:
        status = "NON_COMPLIANT"
    elif any(c.status in ("INSUFFICIENT_DATA", "NEEDS_CLARIFICATION") for c in checks):
        status = "NEEDS_REVIEW"
    else:
        status = "COMPLIANT"
    return status, score


@app.post("/api/v1/audit", response_model=ComplianceResponse)
@limiter.limit(settings.audit_rate_limit)
async def run_compliance_audit(
    request: Request, audit_request: AuditRequest
) -> ComplianceResponse:
    if retrieval_client is None or compliance_engine is None:
        raise HTTPException(status_code=503, detail="Services not initialized")

    building = audit_request.building_details
    topics = select_topics(building)
    if building.construction_status == "under_construction":
        # Construction-phase provisions (Reg. 5(31), 4(27)-4(28)) apply
        # regardless of the building's eventual occupancy classification
        # — tagging the query with "Purpose Group N <building_type>"
        # would bias retrieval toward that future occupancy's own
        # chunks instead of the universal construction-site clauses.
        topic_queries = [desc for _, desc in topics]
    else:
        # Purpose Group number included explicitly, not just building_type
        # free text: several regulation tables (Table 6/7/8/14, Reg.
        # 5(26)(a)) have a distinct row/scope per Purpose Group, and
        # without the number in the query, semantic retrieval sometimes
        # surfaces a different Purpose Group's row (e.g. Residential
        # instead of the actual Cinema/PG5 row) ahead of the one this
        # building actually needs.
        topic_queries = [
            f"{desc} for a Purpose Group {building.occupancy_purpose_group} {building.building_type} "
            f"with {building.number_of_floors} floor(s)"
            for _, desc in topics
        ]

    # Structured pull of occupancy-classification-specific provisions —
    # not a hand-written topic, so it generalizes to occupancy types no
    # one has written a bundle for yet (see audit_topics module docstring
    # and the compliance_engine prompt section this feeds). Restricted to
    # Chapters 2/3/4/6 (Means of Escape, Structural Fire Precautions,
    # Detection/Alarm, Special Uses) rather than every chapter: measured
    # directly against the live index, the untagged-content fallback that
    # makes this filter useful within a chapter (see
    # search_by_classification's docstring) matches 90-225 chunks even
    # within a SINGLE chapter — dropping the chapter restriction entirely
    # matches hundreds of chunks corpuswide with no meaningful way to
    # rank most of them, while requiring an explicit Purpose Group tag
    # instead loses the very untagged-but-relevant chunks (e.g. a
    # hospital's Chapter 3 compartment override) this mechanism exists to
    # catch. Chapters 2/3/4/6 is where occupancy-specific technical
    # overrides have actually been observed to live across every fixture
    # tested so far (Chapters 1/5/7/8 are definitions/general
    # appliances/access/maintenance — administrative or already covered
    # by the fixed CORE topics). Not ranked by query text: tried and
    # reverted (see search_by_classification's docstring) after it
    # actively excluded a genuinely relevant chunk due to the index's
    # lack of stemming ("hospital" query term vs. a stored "hospitals").
    # Exact-Purpose-Group-tagged chunks are still prioritized within the
    # `limit` ahead of untagged ones. Skipped entirely for a building
    # under construction: occupancy_purpose_group there describes what
    # the building will be on completion, not what's relevant to its
    # current construction-phase checklist.
    under_construction = building.construction_status == "under_construction"

    try:
        if under_construction:
            chunk_lists = await asyncio.gather(*(
                retrieval_client.get_relevant_chunks(query, top_k=settings.topic_retrieval_top_k)
                for query in topic_queries
            ))
            occupancy_specific_chunks = []
        else:
            chunk_lists, occupancy_specific_chunks = await asyncio.gather(
                asyncio.gather(*(
                    retrieval_client.get_relevant_chunks(query, top_k=settings.topic_retrieval_top_k)
                    for query in topic_queries
                )),
                retrieval_client.get_chunks_by_classification(
                    purpose_group=building.occupancy_purpose_group,
                    chapters=[2, 3, 4, 6],
                    limit=40,
                ),
            )
    except RetrievalClientError as exc:
        raise HTTPException(
            status_code=502, detail=f"Could not fetch regulations: {exc}"
        ) from exc

    retrieved_chunks = _dedupe_chunks(chunk_lists)
    if not retrieved_chunks:
        raise HTTPException(
            status_code=422,
            detail="No relevant fire regulations found for this building type",
        )

    try:
        assessment = await compliance_engine.analyze(
            building_info=building.model_dump(),
            retrieved_chunks=retrieved_chunks,
            topics=topics,
            occupancy_specific_chunks=occupancy_specific_chunks,
            raw_description=audit_request.raw_description,
        )
    except LLMResponseParsingError as exc:
        raise HTTPException(
            status_code=502, detail=f"Gemini returned an unusable response: {exc}"
        ) from exc
    except ComplianceEngineError as exc:
        raise HTTPException(
            status_code=503, detail=f"Compliance engine failed: {exc}"
        ) from exc

    overall_status, compliance_score = _score_audit(assessment.detailed_checks)
    return ComplianceResponse(
        overall_status=overall_status,
        compliance_score=compliance_score,
        detailed_checks=assessment.detailed_checks,
        summary=assessment.summary,
    )


@app.on_event("startup")
async def on_startup() -> None:
    global retrieval_client, compliance_engine
    logger.info(f"{settings.api_title} v{settings.api_version} starting up")
    retrieval_client = RetrievalClient()
    compliance_engine = ComplianceEngine()
