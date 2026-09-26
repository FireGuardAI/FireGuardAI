import sqlite3
from pathlib import Path

from app.config import settings
from app.exceptions import SparseSearchError
from app.logger import get_logger

logger = get_logger(__name__)

# Filtered out of BM25 match queries — without this, a query built from
# real prose (e.g. a building's raw description) is dominated by "and",
# "the", "a", "with", which appear in nearly every chunk and drown out
# the few rare, meaningful words (e.g. "compartment", "ward") that would
# actually distinguish a relevant chunk from an irrelevant one, both for
# which chunks match at all and for how bm25() ranks them.
_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "in", "on", "at", "to", "for",
    "with", "by", "is", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "it", "its", "as", "from", "not",
    "no", "which", "who", "whom", "their", "they", "he", "she", "we",
    "you", "your", "our", "i", "if", "then", "than", "so", "but",
    "because", "about", "into", "over", "under", "after", "before",
    "between", "during", "per", "each", "every", "any", "all", "both",
    "other", "such", "only", "just", "more", "most", "some", "without",
    "within", "up", "down", "out", "off", "one", "two", "three", "four",
}


class SparseSearchService:
    def __init__(self, db_path: str | None = None):
        self._db_path = Path(db_path or settings.sparse_db_path)
        if not self._db_path.exists():
            raise SparseSearchError(
                f"Sparse index not found at {self._db_path} — has "
                f"fireguard-vector-store's ingestion run yet?"
            )
        logger.info(f"SparseSearchService ready ({self._db_path})")

    def count(self) -> int:
        try:
            conn = sqlite3.connect(self._db_path)
            try:
                return conn.execute("SELECT COUNT(*) FROM chunks_fts").fetchone()[0]
            finally:
                conn.close()
        except Exception as exc:
            raise SparseSearchError(str(exc)) from exc

    @staticmethod
    def _build_match_query(query: str) -> str:
        seen: set[str] = set()
        terms: list[str] = []
        for w in query.split():
            if not w.isalnum() or w.lower() in _STOPWORDS or w.lower() in seen:
                continue
            seen.add(w.lower())
            terms.append(w)
        if not terms:
            return ""
        return " OR ".join(f'"{t}"' for t in terms)

    def search(self, query: str, top_k: int = 20) -> list[dict]:
        match_query = self._build_match_query(query)
        if not match_query:
            return []

        try:
            conn = sqlite3.connect(self._db_path)
            try:
                cursor = conn.execute(
                    """
                    SELECT chunk_id, source, page, text, bm25(chunks_fts) AS score
                    FROM chunks_fts
                    WHERE chunks_fts MATCH ?
                    ORDER BY score
                    LIMIT ?
                    """,
                    (match_query, top_k),
                )
                rows = cursor.fetchall()
            finally:
                conn.close()
        except Exception as exc:
            raise SparseSearchError(str(exc)) from exc

        return [
            {
                "id": chunk_id,
                "text": text,
                "metadata": {"source": source, "page": page},
                "score": score,
                "source": "sparse",
            }
            for chunk_id, source, page, text, score in rows
        ]

    def search_by_classification(
        self,
        chapters: list[int],
        purpose_group: int | None,
        limit: int = 50,
        query: str | None = None,
    ) -> list[dict]:
        """Exact structured filter by document chapter/Purpose Group,
        parsed from the regulation's own headings at ingestion time — not
        a similarity search. Used to fetch every occupancy-specific
        override provision for a building's Purpose Group without a
        hand-authored topic per occupancy type.

        `chapters` is normally left empty (the whole corpus is searched):
        occupancy-specific overrides aren't confined to a fixed subset of
        chapters (a hospital's compartment override lives in Chapter 3,
        its ward-alarm requirement in Chapter 4, a cinema's seating rules
        in Chapter 6) — hard-coding which chapters to search just means
        the next occupancy type's override lives in a chapter nobody
        thought to include. Pass `chapters` only to narrow deliberately.

        Whether an untagged chunk (not explicitly tagged for ANY Purpose
        Group) counts as a match depends on scope: within a `chapters`
        restriction, untagged content is included as likely
        generally-applicable within that narrow section (e.g. untagged
        prose inside a small "Special Uses" chapter). Across the WHOLE
        corpus, that same inclusive rule would match nearly every chunk
        in the document — most ordinary prose never restates a Purpose
        Group — burying the handful of chunks that actually matter under
        thousands of irrelevant ones. So with no `chapters` restriction,
        only chunks EXPLICITLY tagged for this Purpose Group match; there
        is no untagged fallback.

        `query` is currently UNUSED, deliberately — an earlier version
        used it as a hard MATCH filter and a BM25 tie-break, but testing
        against a real fixture showed both make things worse, not better,
        because this corpus's FTS5 index had no stemmer at the time (a
        query term like "hospital" didn't match a stored "hospitals").
        The index now uses a Porter stemmer (see sparse_index.py), which
        removes that specific failure mode — re-enabling query-based
        ranking here is a reasonable follow-up, but out of scope for the
        MCP migration this parameter was kept for; still unused for now
        so behavior doesn't change as a side effect of an unrelated fix."""
        conditions: list[str] = []
        params: list = []

        if chapters:
            conditions.append(f"chapter IN ({', '.join('?' * len(chapters))})")
            params.extend(chapters)

        order_by: list[str] = []
        if purpose_group is not None:
            if chapters:
                pg_columns = [f"pg_{g}" for g in range(1, 9) if g != purpose_group]
                pg_match_expr = f"(pg_{purpose_group} = 1 OR ({' + '.join(pg_columns)}) = 0)"
                conditions.append(pg_match_expr)
                order_by = [f"({pg_match_expr}) = 0"]  # exact-PG-match rows first
            else:
                conditions.append(f"pg_{purpose_group} = 1")

        if not conditions:
            return []

        order_clause = f"ORDER BY {', '.join(order_by)}" if order_by else ""

        try:
            conn = sqlite3.connect(self._db_path)
            try:
                cursor = conn.execute(
                    f"""
                    SELECT chunk_id, source, page, text
                    FROM chunks_fts
                    WHERE {' AND '.join(conditions)}
                    {order_clause}
                    LIMIT ?
                    """,
                    (*params, limit),
                )
                rows = cursor.fetchall()
            finally:
                conn.close()
        except Exception as exc:
            raise SparseSearchError(str(exc)) from exc

        return [
            {
                "id": chunk_id,
                "text": text,
                "metadata": {"source": source, "page": page},
                "score": None,
                "source": "classification",
            }
            for chunk_id, source, page, text in rows
        ]

    def get_chunk_by_id(self, chunk_id: str) -> dict | None:
        """Exact single-chunk lookup, no ranking involved. Used by the
        agentic loop's cross-reference-following tool (get_chunks_near)
        and directly when the model already knows a specific chunk_id
        from a prior result and wants its full text again."""
        conn = sqlite3.connect(self._db_path)
        try:
            row = conn.execute(
                "SELECT chunk_id, source, page, chapter, text FROM chunks_fts WHERE chunk_id = ?",
                (chunk_id,),
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return None
        chunk_id, source, page, chapter, text = row
        return {
            "id": chunk_id,
            "text": text,
            "metadata": {"source": source, "page": page, "chapter": chapter},
        }

    def get_chunks_near(self, chunk_id: str, page_radius: int = 1) -> list[dict]:
        """Fetch every chunk within `page_radius` pages of the given
        chunk's page, same source document — for following a cross-
        reference spotted in a chunk's own text (e.g. "See Reg. 7.2(a)")
        instead of re-running a vague semantic search and hoping a wider
        top_k happens to include the referenced clause. Confirmed this
        session that the referenced clause is often the immediately
        preceding or following page."""
        anchor = self.get_chunk_by_id(chunk_id)
        if anchor is None:
            return []
        source = anchor["metadata"]["source"]
        page = anchor["metadata"]["page"]

        conn = sqlite3.connect(self._db_path)
        try:
            rows = conn.execute(
                """
                SELECT chunk_id, source, page, chapter, text FROM chunks_fts
                WHERE source = ? AND page BETWEEN ? AND ? AND chunk_id != ?
                ORDER BY page
                """,
                (source, page - page_radius, page + page_radius, chunk_id),
            ).fetchall()
        finally:
            conn.close()
        return [
            {
                "id": cid,
                "text": text,
                "metadata": {"source": src, "page": pg, "chapter": ch},
            }
            for cid, src, pg, ch, text in rows
        ]

    def list_chapters(self) -> list[dict]:
        """Distinct (chapter number, representative page) pairs actually
        present in the index — the real corpus structure, replacing the
        hardcoded chapter-number knowledge that used to live in
        audit_topics.py and main.py's classification call sites. Chapter
        0 (untagged/front-matter) is excluded; titles aren't stored at
        ingestion time today, so callers get numbers and a sample page to
        anchor on, not prose titles."""
        conn = sqlite3.connect(self._db_path)
        try:
            rows = conn.execute(
                "SELECT chapter, MIN(page) FROM chunks_fts WHERE chapter > 0 GROUP BY chapter ORDER BY chapter"
            ).fetchall()
        finally:
            conn.close()
        return [{"chapter": chapter, "first_page": first_page} for chapter, first_page in rows]

    def list_purpose_groups_present(self) -> list[int]:
        """Which Purpose Group numbers (1-8) actually have at least one
        explicitly-tagged chunk in the index — lets the agent loop check
        "is this PG worth querying at all" before spending a tool call on
        one the ingestion tagger never found (e.g. PG8/car-parks, which
        this session found has zero explicitly-tagged chunks despite
        having real dedicated regulation content reachable another way)."""
        conn = sqlite3.connect(self._db_path)
        try:
            counts = []
            for g in range(1, 9):
                n = conn.execute(f"SELECT COUNT(*) FROM chunks_fts WHERE pg_{g} = 1").fetchone()[0]
                if n > 0:
                    counts.append(g)
        finally:
            conn.close()
        return counts
