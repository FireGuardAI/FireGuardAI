"""Centralized, type-safe application configuration.

Same pattern as the other three repos. groq_api_key has NO default —
Pydantic raises a validation error at startup if it's missing, which is
the desired fail-fast behavior (not a crash on the first request).
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # API metadata
    api_title: str = Field(default="FireGuard Intake Agent")
    api_version: str = Field(default="0.1.0")
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"])

    # Groq LLM connection (Step 2) — required, no default
    groq_api_key: str
    groq_model_name: str = Field(default="llama-3.1-8b-instant")
    groq_timeout_seconds: float = Field(default=10.0, gt=0)
    groq_max_retries: int = Field(default=3, ge=0)

    # Production hardening (Step 4)
    intake_rate_limit: str = Field(default="20/minute")

    # Observability
    log_level: str = Field(default="INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
