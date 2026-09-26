"""MCP server exposing intake's extraction capability as a tool for the
agentic compliance loop, over Streamable HTTP. Runs as a separate
process from the REST app (app/main.py), same image/container, own
port — see fireguard-agent-retrieval/app/mcp_server.py for why (avoids
Streamable HTTP's internal routing colliding with FastAPI's).

Deliberately does NOT expose an "ask_clarifying_question" tool: when the
orchestrator's loop lacks a fact, it re-queries the vector DB with a
refined query via the retrieval MCP server instead of surfacing a
question to a human mid-audit (see the agentic-loop plan). This server
only ever does the one-shot extraction it already did before the
migration.
"""
import base64

from mcp.server.mcpserver import MCPServer

from app.config import settings
from app.exceptions import GuardrailRejection, IntakeEngineError, IntakeResponseParsingError, PdfExtractionError
from app.logger import get_logger
from app.services.intake_engine import IntakeEngine
from app.services.pdf_extraction import extract_text

logger = get_logger(__name__)

server = MCPServer(
    name="fireguard-intake",
    version=settings.api_version,
    instructions=(
        "Extracts structured building details from raw text or a PDF. "
        "Call extract_building_details once at the start of an audit. "
        "There is no clarification tool here — if a fact is missing, "
        "resolve it by searching the regulation corpus for what's "
        "actually required, not by asking a human mid-audit."
    ),
)

_engine: IntakeEngine | None = None


def _ensure_ready() -> IntakeEngine:
    global _engine
    if _engine is None:
        _engine = IntakeEngine()
    return _engine


@server.tool(
    name="extract_building_details",
    description=(
        "Extract structured building details (occupancy, Purpose Group, "
        "height, installed systems, etc.) from a raw building description. "
        "Every fact not explicitly stated in the input is returned as "
        "null except occupancy_purpose_group and construction_status, "
        "which are always confidently inferred. Also returns the "
        "verbatim raw_description so later reasoning can cross-reference "
        "facts the structured schema has no field for yet."
    ),
)
async def extract_building_details(raw_text: str | None = None, pdf_base64: str | None = None) -> dict:
    if not raw_text and not pdf_base64:
        raise ValueError("Provide either raw_text or pdf_base64")

    if pdf_base64:
        try:
            raw_text = extract_text(base64.b64decode(pdf_base64))
        except PdfExtractionError as exc:
            raise ValueError(f"Could not extract text from the PDF: {exc}") from exc

    engine = _ensure_ready()
    try:
        details = await engine.process_input(raw_text)
    except GuardrailRejection as exc:
        raise ValueError(f"Input rejected: {exc}") from exc
    except (IntakeResponseParsingError, IntakeEngineError) as exc:
        raise ValueError(f"Extraction failed: {exc}") from exc

    result = details.model_dump()
    result["raw_description"] = raw_text
    return result


if __name__ == "__main__":
    logger.info(f"Starting {server.name} MCP server (Streamable HTTP) on 0.0.0.0:{settings.mcp_port}")
    import uvicorn

    uvicorn.run(
        server.streamable_http_app(host="0.0.0.0"),
        host="0.0.0.0",
        port=settings.mcp_port,
    )
