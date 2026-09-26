"""FastAPI front door for the agentic compliance loop. Same external
request shape as the old fireguard-agent-compliance's POST /api/v1/audit
(so the gateway's cutover in a later phase is a URL change, not a
contract change), plus a new GET /api/v1/audit/{audit_id}/trace for the
observability requirement — every MCP tool call this audit made, in
order, with arguments and results.
"""
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.agent_loop import AgentLoop
from app.config import settings
from app.logger import get_logger
from app.mcp_toolbox import MCPToolbox
from app.schemas import AuditRequest, ComplianceResponse
from app.scoring import score_audit
from app.trace import trace_store

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


agent_loop: AgentLoop | None = None


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": settings.api_title}


@app.post("/api/v1/audit", response_model=ComplianceResponse)
@limiter.limit(settings.audit_rate_limit)
async def run_audit(request: Request, audit_request: AuditRequest) -> ComplianceResponse:
    if agent_loop is None:
        raise HTTPException(status_code=503, detail="Agent loop not initialized")

    if not audit_request.building_details and not audit_request.raw_text and not audit_request.raw_description:
        raise HTTPException(
            status_code=422,
            detail="Provide either building_details, raw_description, or raw_text",
        )

    audit_id = str(uuid.uuid4())
    toolbox = MCPToolbox()

    try:
        await toolbox.connect()

        building_details = audit_request.building_details
        raw_description = audit_request.raw_description

        if building_details is None:
            # No pre-extracted facts given — EXTRACT step: one direct,
            # deterministic call to the intake tool, not something the
            # model decides whether to do.
            t0 = time.monotonic()
            extract_result = await toolbox.call(
                "extract_building_details",
                {"raw_text": audit_request.raw_text or audit_request.raw_description},
            )
            latency_ms = int((time.monotonic() - t0) * 1000)
            await trace_store.record(
                audit_id=audit_id,
                turn_number=0,
                tool_name="extract_building_details",
                arguments={"raw_text": "<omitted, see intake trace>"},
                result_summary=extract_result.raw_text[:2000] if extract_result.raw_text else "",
                is_error=extract_result.is_error,
                latency_ms=latency_ms,
            )
            if extract_result.is_error:
                raise HTTPException(status_code=502, detail=f"Extraction failed: {extract_result.raw_text}")
            building_details = extract_result.data
            raw_description = building_details.pop("raw_description", None) if isinstance(building_details, dict) else None

        result = await agent_loop.run(audit_id, building_details, raw_description, toolbox)

        overall_status, compliance_score = score_audit(result.detailed_checks)

        report_result = await toolbox.call(
            "draft_executive_summary",
            {
                "overall_status": overall_status,
                "compliance_score": compliance_score,
                "checks": [c.model_dump() for c in result.detailed_checks],
                "summary": result.summary,
            },
        )
        await trace_store.record(
            audit_id=audit_id,
            turn_number=result.loop_turns_used + 1,
            tool_name="draft_executive_summary",
            arguments={},
            result_summary=report_result.raw_text[:2000] if report_result.raw_text else "",
            is_error=report_result.is_error,
            latency_ms=0,
        )

        executive_summary_markdown = None
        report_generated_by = None
        if not report_result.is_error and isinstance(report_result.data, dict):
            executive_summary_markdown = report_result.data.get("executive_summary_markdown")
            report_generated_by = report_result.data.get("generated_by")

        return ComplianceResponse(
            audit_id=audit_id,
            overall_status=overall_status,
            compliance_score=compliance_score,
            detailed_checks=result.detailed_checks,
            summary=result.summary,
            executive_summary_markdown=executive_summary_markdown,
            report_generated_by=report_generated_by,
            loop_turns_used=result.loop_turns_used,
            tool_calls_used=result.tool_calls_used,
            terminated_by=result.terminated_by,
        )
    finally:
        await toolbox.close()


@app.get("/api/v1/audit/{audit_id}/trace")
async def get_audit_trace(audit_id: str) -> dict:
    trace = await trace_store.get_trace(audit_id)
    if not trace:
        raise HTTPException(status_code=404, detail="No trace found for this audit_id")
    return {"audit_id": audit_id, "tool_calls": trace}


@app.on_event("startup")
async def on_startup() -> None:
    global agent_loop
    logger.info(f"{settings.api_title} v{settings.api_version} starting up")
    await trace_store.connect()
    agent_loop = AgentLoop()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await trace_store.close()
