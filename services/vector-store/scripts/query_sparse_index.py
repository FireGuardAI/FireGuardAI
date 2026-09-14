import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import settings


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python scripts/query_sparse_index.py "your query"')
        sys.exit(1)

    query_text = sys.argv[1]
    db_path = Path(settings.bm25_index_path)
    if not db_path.exists():
        print(f"No index found at {db_path} — run ingestion first.")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(
            """
            SELECT chunk_id, source, page, text, bm25(chunks_fts) AS score
            FROM chunks_fts
            WHERE chunks_fts MATCH ?
            ORDER BY score
            LIMIT 5
            """,
            (query_text,),
        )
        rows = cursor.fetchall()
        if not rows:
            print("No matches.")
            return
        for chunk_id, source, page, text, score in rows:
            preview = text[:150].replace("\n", " ")
            print(f"[{score:.3f}] {chunk_id} (p.{page}, {source})\n  {preview}...\n")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
