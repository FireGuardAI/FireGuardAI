import pickle
from pathlib import Path

from rank_bm25 import BM25Okapi

from src.config import settings
from src.exceptions import SparseIndexError
from src.logger import get_logger
from src.pdf_processor import DocumentChunk

logger = get_logger(__name__)


class SparseIndexBuilder:
    def __init__(self, index_path: str | None = None):
        self._index_path = Path(index_path or settings.bm25_index_path)

    def build_and_save(self, chunks: list[DocumentChunk]) -> None:
        if not chunks:
            logger.warning("No chunks provided; skipping BM25 index build")
            return

        try:
            documents = [c.text for c in chunks]
            tokenized_corpus = [doc.lower().split(" ") for doc in documents]
            bm25 = BM25Okapi(tokenized_corpus)

            self._index_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._index_path, "wb") as f:
                pickle.dump(
                    {
                        "bm25": bm25,
                        "documents": documents,
                        "metadatas": [
                            {"source": c.source, "page": c.page_number}
                            for c in chunks
                        ],
                    },
                    f,
                )
            logger.info(f"BM25 sparse index saved to {self._index_path}")
        except Exception as exc:
            raise SparseIndexError(str(exc)) from exc
