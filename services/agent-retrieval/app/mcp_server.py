"""MCP server exposing this service's retrieval AND corpus-introspection
capabilities as tools/resources for the agentic compliance loop, over
Streamable HTTP.

Runs as a SEPARATE process from the existing REST app (app/main.py), on
its own port, in the same container/image — same underlying data
(ChromaDB + the FTS5 index), reused service classes, no duplicated
search logic. This is a deliberate simplification of the original plan's
"corpus" server as its own component: it's the same SQLite/Chroma data
either way, and splitting it into a second container would mean a
second set of DB connections to the same files for no operational
benefit. The MCP tool names below keep the two responsibilities
(ranked search vs. raw structural introspection) distinct even though
they're one process.

Entry point: `python -m app.mcp_server` (see docker-compose.yml's
`agent-retrieval-mcp` service).
"""
from mcp.server.mcpserver import MCPServer

from app.config import settings
from app.logger import get_logger
from app.services.dense_search import DenseSearchService
from app.services.hybrid_fusion import reciprocal_rank_fusion
from app.services.reranker import RerankerService
from app.services.sparse_search import SparseSearchService

logger = get_logger(__name__)

server = MCPServer(
    name="fireguard-retrieval",
    version=settings.api_version,
    instructions=(
        "Search and corpus-introspection tools for the CIDA/DEV/14 fire "
        "regulation corpus. Use semantic_search for a natural-language "
        "question about a specific requirement. Use classification_search "
        "when you already know a building's Purpose Group and want every "
        "regulation chunk explicitly tagged for it. Use get_chunks_near "
        "when a chunk's text references another clause by number (e.g. "
        "'See Reg. 7.2(a)') and you want that clause's actual text instead "
        "of re-running a vague semantic search and hoping it's included."
    ),
)

_dense: DenseSearchService | None = None
_sparse: SparseSearchService | None = None
_reranker: RerankerService | None = None


def _ensure_ready() -> None:
    global _dense, _sparse, _reranker
    if _dense is None:
        _dense = DenseSearchService()
    if _sparse is None:
        _sparse = SparseSearchService()
    if _reranker is None:
        _reranker = RerankerService()


@server.tool(
    name="semantic_search",
    description=(
        "Hybrid dense+sparse search with cross-encoder reranking. Give it "
        "a specific, self-contained question or requirement description — "
        "not a bare keyword. Returns the top_k most relevant chunks with "
        "their source page."
    ),
)
def semantic_search(query: str, top_k: int = 5) -> list[dict]:
    _ensure_ready()
    dense_results = _dense.search(query, top_k=settings.dense_top_k)
    sparse_results = _sparse.search(query, top_k=settings.sparse_top_k)
    fused = reciprocal_rank_fusion(dense_results, sparse_results)
    candidates = fused[: settings.rerank_candidate_k]
    reranked = _reranker.rerank(query, candidates)
    return [
        {
            "id": r["id"],
            "text": r["text"],
            "page": (r.get("metadata") or {}).get("page"),
            "rerank_score": r["rerank_score"],
        }
        for r in reranked[:top_k]
    ]


@server.tool(
    name="classification_search",
    description=(
        "Exact structural filter — NOT a ranked search. Returns every "
        "chunk explicitly tagged for the given Purpose Group (optionally "
        "narrowed to specific chapter numbers; call corpus_list_chapters "
        "first if unsure which chapters exist). Use this to find "
        "occupancy-specific override provisions a generic semantic query "
        "might not surface. Check corpus_list_purpose_groups_present "
        "first — some Purpose Groups have zero explicitly-tagged chunks "
        "even though real relevant content exists in the corpus another "
        "way (e.g. under a different heading)."
    ),
)
def classification_search(purpose_group: int, chapters: list[int] | None = None, limit: int = 40) -> list[dict]:
    _ensure_ready()
    results = _sparse.search_by_classification(chapters or [], purpose_group, limit)
    return [{"id": r["id"], "text": r["text"], "page": r["metadata"]["page"]} for r in results]


@server.tool(
    name="get_chunk",
    description="Fetch one specific chunk's full text by its id, e.g. to re-read a chunk returned earlier in this conversation.",
)
def get_chunk(chunk_id: str) -> dict | None:
    _ensure_ready()
    return _sparse.get_chunk_by_id(chunk_id)


@server.tool(
    name="get_chunks_near",
    description=(
        "Fetch the chunks on nearby pages of the SAME source document as "
        "the given chunk_id. Use this when a chunk's text references "
        "another clause by number (e.g. 'See Reg. 7.2(a)') to fetch that "
        "clause's actual defining text, which is often a page or two "
        "away, instead of retrying semantic_search with a different "
        "phrasing and hoping it happens to surface."
    ),
)
def get_chunks_near(chunk_id: str, page_radius: int = 2) -> list[dict]:
    _ensure_ready()
    return _sparse.get_chunks_near(chunk_id, page_radius)


@server.tool(
    name="corpus_list_chapters",
    description=(
        "List every chapter number actually present in the regulation "
        "corpus, with a representative first page for each. Use this "
        "before classification_search to decide which chapters are worth "
        "restricting to, instead of assuming a fixed list — different "
        "occupancy types' override provisions live in different, "
        "sometimes surprising chapters (confirmed: a hospital's "
        "compartment override is in the Structural chapter, not the "
        "Special Uses chapter a cinema's seating rules live in)."
    ),
)
def corpus_list_chapters() -> list[dict]:
    _ensure_ready()
    return _sparse.list_chapters()


@server.tool(
    name="corpus_list_purpose_groups_present",
    description=(
        "Which Purpose Group numbers (1-8) have at least one explicitly-"
        "tagged chunk in the corpus. A Purpose Group missing from this "
        "list doesn't mean it has no regulation content — it means "
        "classification_search won't find anything by tag for it, so "
        "prefer semantic_search instead for that Purpose Group."
    ),
)
def corpus_list_purpose_groups_present() -> list[int]:
    _ensure_ready()
    return _sparse.list_purpose_groups_present()


if __name__ == "__main__":
    logger.info(f"Starting {server.name} MCP server (Streamable HTTP) on 0.0.0.0:{settings.mcp_port}")
    import uvicorn

    uvicorn.run(
        server.streamable_http_app(host="0.0.0.0"),
        host="0.0.0.0",
        port=settings.mcp_port,
    )
