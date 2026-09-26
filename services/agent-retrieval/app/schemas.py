from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1, description="The search query text")
    top_k: int = Field(default=5, gt=0, le=50)


class ClassificationRetrievalRequest(BaseModel):
    """Structured retrieval by document structure (Purpose Group tag)
    rather than embedding similarity — an exact filter, optionally
    ranked by textual relevance to `query` when the filter alone would
    match more chunks than `limit` allows."""

    chapters: list[int] = Field(
        default_factory=list,
        description="Optional chapter restriction. Leave empty to search "
        "the whole corpus — occupancy-specific override provisions are "
        "scattered across chapters, not confined to any fixed subset.",
    )
    purpose_group: int | None = Field(default=None, ge=1, le=8)
    query: str | None = Field(
        default=None,
        description="Free text used only to rank matches (BM25) when the "
        "classification filter alone matches more than `limit` chunks — "
        "does not affect which chunks pass the filter, only their order.",
    )
    limit: int = Field(default=50, gt=0, le=300)


class ChunkResponse(BaseModel):
    id: str
    text: str
    rrf_score: float
    rerank_score: float
    found_by: list[str]
    metadata: dict | None = None
