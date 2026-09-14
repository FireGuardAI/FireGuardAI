from src.embedding_service import EmbeddingService
from src.logger import get_logger
from src.pdf_processor import PDFProcessor
from src.sparse_index import SparseIndexBuilder
from src.vector_repository import VectorRepository

logger = get_logger(__name__)


class IngestPipeline:
    def __init__(
        self,
        pdf_processor: PDFProcessor,
        embedding_service: EmbeddingService,
        vector_repo: VectorRepository,
        sparse_index_builder: SparseIndexBuilder,
    ):
        self._pdf_processor = pdf_processor
        self._embedding_service = embedding_service
        self._vector_repo = vector_repo
        self._sparse_index_builder = sparse_index_builder

    def run(self, pdf_path: str, doc_name: str) -> None:
        chunks = self._pdf_processor.process(pdf_path, doc_name)
        if not chunks:
            logger.warning(f"No chunks extracted from {doc_name}; skipping")
            return

        embeddings = self._embedding_service.embed([c.text for c in chunks])
        self._vector_repo.upsert_chunks(chunks, embeddings)
        self._sparse_index_builder.build_and_save(chunks)
        logger.info(f"✅ Ingestion complete for {doc_name}")
