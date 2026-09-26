"""MCP server exposing report drafting as a tool for the agentic
compliance loop, over Streamable HTTP. Separate process from the REST
app (app/main.py), same image/container, own port — see
fireguard-agent-retrieval/app/mcp_server.py for why.
"""
from mcp.server.mcpserver import MCPServer

from app.config import settings
from app.exceptions import ReportEngineError
from app.logger import get_logger
from app.schemas import AuditDataInput, RuleCheckItem
from app.services.report_engine import ReportEngine

logger = get_logger(__name__)

server = MCPServer(
    name="fireguard-report",
    version=settings.api_version,
    instructions=(
        "Drafts the executive-summary markdown from a FINALIZED set of "
        "compliance checks and a deterministically-computed score. Call "
        "this once, last, after the loop has finished investigating — "
        "never before detailed_checks and the score are final, since the "
        "summary is meant to describe the finished audit, not guide it."
    ),
)

_engine: ReportEngine | None = None


def _ensure_ready() -> ReportEngine:
    global _engine
    if _engine is None:
        _engine = ReportEngine()
    return _engine


@server.tool(
    name="draft_executive_summary",
    description=(
        "Turn a finalized list of compliance checks plus the deterministic "
        "overall_status/compliance_score into an executive-summary "
        "markdown document. The score and status are inputs, not "
        "something this tool computes or can revise."
    ),
)
async def draft_executive_summary(
    overall_status: str, compliance_score: float, checks: list[dict], summary: str
) -> dict:
    engine = _ensure_ready()
    audit_data = AuditDataInput(
        overall_status=overall_status,
        compliance_score=compliance_score,
        detailed_checks=[RuleCheckItem(**c) for c in checks],
        summary=summary,
    )
    try:
        report_md, generated_by = await engine.generate_report(audit_data)
    except ReportEngineError as exc:
        raise ValueError(
            f"Report generation failed (primary: {exc.primary_error}, "
            f"fallback: {exc.fallback_error})"
        ) from exc
    return {"executive_summary_markdown": report_md, "generated_by": generated_by}


if __name__ == "__main__":
    logger.info(f"Starting {server.name} MCP server (Streamable HTTP) on 0.0.0.0:{settings.mcp_port}")
    import uvicorn

    uvicorn.run(
        server.streamable_http_app(host="0.0.0.0"),
        host="0.0.0.0",
        port=settings.mcp_port,
    )
