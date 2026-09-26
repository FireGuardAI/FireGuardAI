from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    api_title: str = Field(default="FireGuard Compliance Agent")
    api_version: str = Field(default="0.1.0")
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"])

    retrieval_service_url: str = Field(default="http://agent-retrieval:8001")
    retrieval_top_k: int = Field(default=5, gt=0)
    # 4, not 3: found via the Sunrise Supermarket fixture that a table
    # chunk answering a topic sometimes just says "see Reg. X" — the
    # actual defining text for Reg. X exists in the corpus, often on an
    # adjacent page, but top_k=3 doesn't always reach it. One extra
    # chunk per topic meaningfully raises the odds a cross-referenced
    # clause and the table pointing to it both land in the same
    # retrieval, without materially growing the prompt.
    topic_retrieval_top_k: int = Field(
        default=4, gt=0, description="Chunks fetched per audit-checklist topic (see audit_topics.py)"
    )
    # 60s, not 10s: agent-retrieval runs as a single uvicorn worker doing
    # synchronous embedding/BM25/rerank work per request, so the ~13
    # concurrent per-topic requests one audit now fires queue up behind
    # each other — a request near the back of that queue can genuinely
    # take longer than 10s to even start, well before it does any real
    # work (confirmed via agent-retrieval's own logs showing 200 OK on
    # requests the client had already given up on).
    retrieval_timeout_seconds: float = Field(default=60.0, gt=0)
    retrieval_max_retries: int = Field(default=3, ge=0)

    gemini_api_key: str
    gemini_model_name: str = Field(default="gemini-1.5-flash")
    # 90s, not 30s: the audit prompt now carries ~10 topics' worth of
    # retrieved regulation text (multi-topic retrieval) and requires a
    # structured 10-check JSON response — genuinely slower than the old
    # single-query/5-chunk prompt this default was originally tuned for.
    # 180s: the occupancy-specific Chapter 6 context (up to 25 more
    # chunks) plus "enumerate every requirement you find" pushes genuine
    # successful calls close to or past 90s now — a too-short timeout
    # doesn't just fail faster, it wastes Gemini's free-tier daily quota
    # on retries for calls that would have succeeded given more time.
    gemini_timeout_seconds: float = Field(default=180.0, gt=0)
    gemini_max_retries: int = Field(default=3, ge=0)

    audit_rate_limit: str = Field(default="10/minute")

    log_level: str = Field(default="INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
