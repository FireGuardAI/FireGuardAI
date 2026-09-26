import dataclasses
import re
from dataclasses import dataclass

import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import settings
from src.exceptions import PDFProcessingError
from src.logger import get_logger

logger = get_logger(__name__)

_TABLE_TITLE_RE = re.compile(r"TABLE\s*\d+", re.IGNORECASE)
# Regulatory tables in this document continue onto the very next page with
# no heading of their own (e.g. Table 8's Purpose-Group rows on p.158
# follow its column headers on p.157); this caps how many consecutive
# unheaded pages get folded into one table so a run of ordinary pages
# that just happen to contain other tables can't merge unbounded.
_MAX_CONTINUATION_PAGES = 5

_CHAPTER_RE = re.compile(r"\bCHAPTER\s+(\d+)\b", re.IGNORECASE)
_PURPOSE_GROUP_RE = re.compile(r"Purpose\s+Group\s+(\d)\b", re.IGNORECASE)


@dataclass(frozen=True)
class DocumentChunk:
    text: str
    source: str
    page_number: int
    chunk_id: str
    # Classification metadata used for structured (non-semantic) retrieval
    # of occupancy-specific provisions — see agent-retrieval's
    # /api/v1/retrieve/by-classification. chapter is the physical chapter
    # this chunk's page falls under (None if before the first "CHAPTER n"
    # heading); purpose_groups are the Purpose Group numbers (1-8)
    # explicitly named in the chunk's own text.
    #
    # Known limitation: the back-of-book Tables appendix (Table 1-18)
    # doesn't repeat "CHAPTER n" headings, so those chunks inherit
    # whichever chapter heading appeared last before the appendix started
    # rather than the chapter that actually governs each table (e.g.
    # Table 5 substantively belongs to Chapter 2). This doesn't matter for
    # what chapter-tagging is actually used for — scoping the Chapter 6
    # "Special Uses" retrieval to Chapter 6's own prose pages, which DO
    # carry their own heading — but it means chapter tags on appendix
    # tables shouldn't be trusted for anything else without fixing this.
    chapter: int | None = None
    purpose_groups: tuple[int, ...] = ()


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
            page_chapters = self._map_pages_to_chapters(document)

            # Table-aware chunks first (see _extract_table_chunks docstring
            # for why plain per-page splitting destroys multi-page tables).
            # These are ADDED alongside the prose chunks below, not instead
            # of them — some duplication between a clean table chunk and
            # the same content's jumbled prose fragments is harmless.
            chunks.extend(self._extract_table_chunks(document, doc_name))

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

        chunks = [self._tag_classification(chunk, page_chapters) for chunk in chunks]

        logger.info(f"Extracted {len(chunks)} chunks from {doc_name}")
        return chunks

    @staticmethod
    def _map_pages_to_chapters(document) -> dict[int, int | None]:
        mapping: dict[int, int | None] = {}
        current_chapter: int | None = None
        for page_number, page in enumerate(document, start=1):
            match = _CHAPTER_RE.search(page.get_text())
            if match:
                current_chapter = int(match.group(1))
            mapping[page_number] = current_chapter
        return mapping

    @staticmethod
    def _tag_classification(
        chunk: DocumentChunk, page_chapters: dict[int, int | None]
    ) -> DocumentChunk:
        purpose_groups = tuple(sorted({int(g) for g in _PURPOSE_GROUP_RE.findall(chunk.text)}))
        return dataclasses.replace(
            chunk,
            chapter=page_chapters.get(chunk.page_number),
            purpose_groups=purpose_groups,
        )

    def _extract_table_chunks(self, document, doc_name: str) -> list[DocumentChunk]:
        """Detects tables per page via PyMuPDF's find_tables() and merges
        a table with no title of its own into the previous page's table,
        so a multi-page table (column headers on one page, a specific
        row — e.g. "7 Storage" — on the next) becomes ONE chunk with its
        headers intact, instead of two chunks neither of which is useful
        alone. A page with a genuine "TABLE n" heading always starts a
        fresh table; a page whose table has no heading text above it
        continues whatever table was open from the immediately preceding
        page (real-world PDF tables split across many differently-shaped
        page fragments, so column-count matching is deliberately not
        required — same-page-adjacency plus the absence of a new title is
        the reliable signal here).

        Continuation is ONLY allowed onto a sequence that itself started
        from a genuine "TABLE n" heading. Many pages throughout the main
        regulation chapters (not just the Tables appendix) use a
        "Label | Reg. N | description" three-column layout for ordinary
        clause text, which find_tables() also detects as a "table" —
        these have no heading of their own either, but they are NOT
        related multi-page data tables, just adjacent unrelated clauses
        that happen to share a layout. Letting an untitled table become
        "pending" fuel for the next untitled table to continue onto (the
        original bug here) glued a Purpose Group listing on p.97 to
        several unrelated fire-pump regulations many pages later, none
        of which had anything to do with each other."""
        table_chunks: list[DocumentChunk] = []
        pending_rows: list[list[str | None]] | None = None
        pending_start_page: int | None = None
        pending_pages_spanned = 0
        pending_is_titled = False
        # A running counter, not the page number, disambiguates chunk_ids —
        # more than one table can start on the same page (e.g. Table 5(IV)
        # ends and Table 5(V) begins further down p.152), which would
        # otherwise collide on "{doc_name}_table_p152" twice.
        table_index = 0

        def flush() -> None:
            nonlocal pending_rows, pending_start_page, pending_pages_spanned, pending_is_titled, table_index
            if pending_rows:
                table_chunks.append(
                    DocumentChunk(
                        text=self._rows_to_markdown(pending_rows),
                        source=doc_name,
                        page_number=pending_start_page,
                        chunk_id=f"{doc_name}_table_{table_index}_p{pending_start_page}",
                    )
                )
                table_index += 1
            pending_rows = None
            pending_start_page = None
            pending_pages_spanned = 0
            pending_is_titled = False

        def emit_standalone(rows: list[list[str | None]], page_number: int) -> None:
            """An untitled table with nothing legitimate to continue —
            emitted as its own single-page chunk, but never held open as
            'pending', so it can't bait a later untitled table into
            merging with it."""
            nonlocal table_index
            table_chunks.append(
                DocumentChunk(
                    text=self._rows_to_markdown(rows),
                    source=doc_name,
                    page_number=page_number,
                    chunk_id=f"{doc_name}_table_{table_index}_p{page_number}",
                )
            )
            table_index += 1

        for page_number, page in enumerate(document, start=1):
            try:
                found_tables = page.find_tables().tables
            except Exception as exc:
                logger.warning(f"Table detection failed on page {page_number}: {exc}")
                flush()
                continue

            if not found_tables:
                flush()
                continue

            for table in found_tables:
                rows = table.extract()
                if not rows:
                    continue
                above_text = page.get_text(clip=fitz.Rect(0, 0, page.rect.width, table.bbox[1]))
                is_new_table = bool(_TABLE_TITLE_RE.search(above_text))

                if is_new_table:
                    flush()
                    pending_rows = rows
                    pending_start_page = page_number
                    pending_pages_spanned = 1
                    pending_is_titled = True
                elif (
                    pending_rows is not None
                    and pending_is_titled
                    and pending_pages_spanned < _MAX_CONTINUATION_PAGES
                ):
                    pending_rows = pending_rows + rows
                    pending_pages_spanned += 1
                else:
                    flush()
                    emit_standalone(rows, page_number)

        flush()
        return table_chunks

    @staticmethod
    def _rows_to_markdown(rows: list[list[str | None]]) -> str:
        def clean(cell: str | None) -> str:
            return (cell or "").replace("\n", " ").strip()

        lines = ["| " + " | ".join(clean(cell) for cell in row) + " |" for row in rows]
        col_count = len(rows[0])
        lines.insert(1, "| " + " | ".join(["---"] * col_count) + " |")
        return "\n".join(lines)
