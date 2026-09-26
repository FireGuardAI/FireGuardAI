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
    mcp_call_timeout_seconds: float = Field(default=60.0, gt=0)

    gemini_api_key: str
    gemini_model_name: str = Field(default="gemini-3.5-flash")
    gemini_timeout_seconds: float = Field(default=180.0, gt=0)
    gemini_max_retries: int = Field(default=3, ge=0)

    # Hard budget enforced by the ORCHESTRATOR, not the model — an
    # unbounded tool-calling loop is not viable at free-tier daily quota.
    max_loop_turns: int = Field(default=6, gt=0)
    max_tool_calls: int = Field(default=24, gt=0)

    database_url: str = Field(
        default="postgresql://fireguard:fireguard@postgres:5432/fireguard"
    )

    log_level: str = Field(default="INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
