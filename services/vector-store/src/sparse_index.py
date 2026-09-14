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
                conn.execute(
                    """
                    CREATE VIRTUAL TABLE chunks_fts USING fts5(
                        chunk_id UNINDEXED,
                        source UNINDEXED,
                        page UNINDEXED,
                        text
                    )
                    """
                )
                conn.executemany(
                    "INSERT INTO chunks_fts (chunk_id, source, page, text) "
                    "VALUES (?, ?, ?, ?)",
                    [
                        (c.chunk_id, c.source, c.page_number, c.text)
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
