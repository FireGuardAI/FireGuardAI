from pathlib import Path

from src.embedding_service import EmbeddingService
from src.ingest_pipeline import IngestPipeline
from src.logger import get_logger
from src.pdf_processor import PDFProcessor
from src.sparse_index import SparseIndexBuilder
from src.vector_repository import VectorRepository

logger = get_logger(__name__)


def main() -> None:
    pipeline = IngestPipeline(
        pdf_processor=PDFProcessor(),
        embedding_service=EmbeddingService(),
        vector_repo=VectorRepository(collection_name="fire_safety_regulations"),
        sparse_index_builder=SparseIndexBuilder(),
    )

    pdf_path = "raw_documents/fire-regulations.pdf"
    if not Path(pdf_path).exists():
        logger.error(f"PDF not found at {pdf_path} — nothing to ingest")
        return

    pipeline.run(pdf_path=pdf_path, doc_name="fire-regulations")


if __name__ == "__main__":
    main()
