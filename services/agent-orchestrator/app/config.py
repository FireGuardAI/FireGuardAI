from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    api_title: str = Field(default="FireGuard Compliance Orchestrator")
    api_version: str = Field(default="0.1.0")
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"])

    database_url: str = Field(
        default="postgresql://fireguard:fireguard@postgres:5432/fireguard"
    )

    log_level: str = Field(default="INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
