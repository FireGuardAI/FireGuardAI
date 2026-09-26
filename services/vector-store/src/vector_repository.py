import chromadb

from src.config import settings
from src.exceptions import VectorStoreConnectionError
from src.logger import get_logger
from src.pdf_processor import DocumentChunk

logger = get_logger(__name__)


class VectorRepository:
    def __init__(self, collection_name: str):
        try:
            self._client = chromadb.HttpClient(
                host=settings.chroma_host, port=settings.chroma_port
            )
            self._collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as exc:
            raise VectorStoreConnectionError(
                f"Could not connect to ChromaDB at "
                f"{settings.chroma_host}:{settings.chroma_port}: {exc}"
            ) from exc

    def upsert_chunks(
        self, chunks: list[DocumentChunk], embeddings: list[list[float]]
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings length mismatch")
        if not chunks:
            logger.warning("No chunks to upsert; skipping")
            return

        self._collection.upsert(
            ids=[c.chunk_id for c in chunks],
            embeddings=embeddings,
            documents=[c.text for c in chunks],
            metadatas=[self._metadata_for(c) for c in chunks],
        )
        logger.info(f"Upserted {len(chunks)} chunks into vector store")

    def query(self, query_text: str, n_results: int = 5) -> dict:
        return self._collection.query(query_texts=[query_text], n_results=n_results)

    @staticmethod
    def _metadata_for(chunk: DocumentChunk) -> dict:
        metadata: dict = {
            "source": chunk.source,
            "page": chunk.page_number,
            "chapter": chunk.chapter if chunk.chapter is not None else 0,
        }
        for group in range(1, 9):
            metadata[f"pg_{group}"] = group in chunk.purpose_groups
        return metadata
