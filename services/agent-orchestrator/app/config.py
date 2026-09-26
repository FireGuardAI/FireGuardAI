from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    api_title: str = Field(default="FireGuard Compliance Orchestrator")
    api_version: str = Field(default="0.1.0")
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"])

    # MCP server URLs (see each service's app/mcp_server.py) — every
    # capability the agent loop can call is one of these, no bespoke REST
    # contract per capability.
    retrieval_mcp_url: str = Field(default="http://agent-retrieval-mcp:8011/mcp")
    intake_mcp_url: str = Field(default="http://agent-intake-mcp:8014/mcp")
    report_mcp_url: str = Field(default="http://agent-report-mcp:8013/mcp")
    mcp_connect_timeout_seconds: float = Field(default=15.0, gt=0)
    # Every Gemini call is wrapped in asyncio.wait_for (see agent_loop.py)
    # but MCP tool calls originally had no timeout of their own at all —
    # confirmed this session: a shadow-mode run hung well past the 400s
    # client timeout with no error ever logged, meaning the actual stall
    # was somewhere in an MCP call, not Gemini. 60s, not something
    # tighter, because agent-retrieval runs as a single worker doing
    # synchronous embedding/BM25/rerank work (documented in its own
    # config) — a request queued behind others can legitimately take a
    # while to even start.
    mcp_call_timeout_seconds: float = Field(default=60.0, gt=0)

    gemini_api_key: str
    gemini_model_name: str = Field(default="gemini-3.5-flash")
    # 300s, not 180s: the improved batching guidance (see prompts.py) now
    # routinely produces 20+ retrieved chunks worth of accumulated context
    # by the time the force-finalize call runs — confirmed this session,
    # a Zenith Tower finalize call with that much context hit a bare
    # asyncio.TimeoutError at 180s. Same reasoning as every other timeout
    # bump made across this project: too-short doesn't just fail faster,
    # it wastes a whole audit's accumulated tool-call budget on a retry.
    gemini_timeout_seconds: float = Field(default=300.0, gt=0)
    gemini_max_retries: int = Field(default=3, ge=0)

    # Hard budget enforced by the ORCHESTRATOR, not the model — see
    # agent_loop.py. Not optional: an unbounded tool-calling loop is not
    # viable at free-tier daily quota (confirmed repeatedly this project
    # ran into the 20-req/day ceiling with a single call per audit; a
    # loop that runs unchecked would exhaust it in one or two audits).
    #
    # These two limits are NOT interchangeable and were conflated when
    # first set: max_loop_turns bounds Gemini API calls (one per turn —
    # this is the actual quota cost), while max_tool_calls only bounds
    # how many tool invocations happen total, and Gemini's parallel
    # function calling lets many tool calls land in a SINGLE turn. Traced
    # directly across three separate shadow-mode runs (Sunrise, Zenith,
    # Willow): every one hit tool_calls_used == 24/24 while
    # loop_turns_used was only 4/6 — the tool-call ceiling was binding
    # while a third of the turn (quota) budget sat unused. That gap is
    # the direct, measured cause of the new loop covering fewer topics
    # than the old hardcoded checklist despite costing LESS quota per
    # audit than the old checklist's ~15-27 pre-computed queries would
    # suggest. Raising max_tool_calls alone costs zero extra Gemini
    # calls — it only lets the same turns batch in more searches before
    # stopping.
    max_loop_turns: int = Field(default=6, gt=0)
    max_tool_calls: int = Field(default=60, gt=0)

    database_url: str = Field(
        default="postgresql://fireguard:fireguard@postgres:5432/fireguard"
    )

    audit_rate_limit: str = Field(default="10/minute")

    log_level: str = Field(default="INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
