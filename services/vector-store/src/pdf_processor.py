from dataclasses import dataclass

import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import settings
from src.exceptions import PDFProcessingError
from src.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class DocumentChunk:
    text: str
    source: str
    page_number: int
    chunk_id: str


class PDFProcessor:

    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size or settings.chunk_size,
            chunk_overlap=chunk_overlap or settings.chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )

    def process(self, pdf_path: str, doc_name: str) -> list[DocumentChunk]:
        logger.info(f"Processing PDF: {doc_name} ({pdf_path})")
        try:
            document = fitz.open(pdf_path)
        except Exception as exc:
            raise PDFProcessingError(f"Failed to open {pdf_path}: {exc}") from exc

        chunks: list[DocumentChunk] = []
        try:
            for page_number, page in enumerate(document, start=1):
                page_text = page.get_text().strip()
                if not page_text:
                    continue

                for idx, split_text in enumerate(self._splitter.split_text(page_text)):
                    chunks.append(
                        DocumentChunk(
                            text=split_text,
                            source=doc_name,
                            page_number=page_number,
                            chunk_id=f"{doc_name}_p{page_number}_{idx}",
                        )
                    )
        finally:
            document.close()

        logger.info(f"Extracted {len(chunks)} chunks from {doc_name}")
        return chunks
