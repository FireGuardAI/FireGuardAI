import sqlite3
from pathlib import Path

from src.config import settings
from src.exceptions import SparseIndexError
from src.logger import get_logger
from src.pdf_processor import DocumentChunk

logger = get_logger(__name__)


class SparseIndexBuilder:
    def __init__(self, db_path: str | None = None):
        self._db_path = Path(db_path or settings.bm25_index_path)

    def build_and_save(self, chunks: list[DocumentChunk]) -> None:
        if not chunks:
            logger.warning("No chunks provided; skipping FTS5 index build")
            return

        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self._db_path)
            try:
                conn.execute("DROP TABLE IF EXISTS chunks_fts")
                pg_columns = ", ".join(f"pg_{g} UNINDEXED" for g in range(1, 9))
                # tokenize='porter unicode61': without a stemmer, a query for
                # "hospital" does not match a stored "hospitals" at all (FTS5
                # does exact-token matching by default) — confirmed this broke
                # a real retrieval attempt (a production-style query matched
                # 99 unrelated chunks and excluded the one genuinely relevant
                # chunk, which only ever appears in its plural form). Porter
                # wraps unicode61 and reduces both query and indexed terms to
                # a common stem, so singular/plural and simple suffix
                # variants match without needing an exact literal hit.
                conn.execute(
                    f"""
                    CREATE VIRTUAL TABLE chunks_fts USING fts5(
                        chunk_id UNINDEXED,
                        source UNINDEXED,
                        page UNINDEXED,
                        chapter UNINDEXED,
                        {pg_columns},
                        text,
                        tokenize = 'porter unicode61'
                    )
                    """
                )
                pg_placeholders = ", ".join("?" * 8)
                conn.executemany(
                    f"INSERT INTO chunks_fts "
                    f"(chunk_id, source, page, chapter, {', '.join(f'pg_{g}' for g in range(1, 9))}, text) "
                    f"VALUES (?, ?, ?, ?, {pg_placeholders}, ?)",
                    [
                        (
                            c.chunk_id,
                            c.source,
                            c.page_number,
                            c.chapter if c.chapter is not None else 0,
                            *(1 if g in c.purpose_groups else 0 for g in range(1, 9)),
                            c.text,
                        )
                        for c in chunks
                    ],
                )
                conn.commit()
            finally:
                conn.close()
            logger.info(
                f"FTS5 inverted index built at {self._db_path} "
                f"({len(chunks)} rows)"
            )
        except Exception as exc:
            raise SparseIndexError(str(exc)) from exc

    def query(self, query_text: str, n_results: int = 5) -> list[dict]:
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
                (query_text, n_results),
            )
            columns = [d[0] for d in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            conn.close()
