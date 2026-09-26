"""In-memory PDF-to-text extraction for the /api/v1/intake/document route.

The uploaded file is never written to disk — pypdf reads it straight out
of the bytes we already have in memory, and nothing here retains a copy
after the request completes.
"""
import io

from pypdf import PdfReader

from app.config import settings
from app.exceptions import PdfExtractionError


def extract_text(pdf_bytes: bytes) -> str:
    # pypdf raises a variety of exception types (ValueError, KeyError,
    # PdfReadError, ...) for malformed PDFs depending on which structure
    # is broken — this is a trust boundary for arbitrary user uploads, so
    # anything it throws gets turned into our own PdfExtractionError.
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        if reader.is_encrypted:
            raise PdfExtractionError("Encrypted/password-protected PDFs are not supported")
        pages = reader.pages[: settings.document_max_pages]
    except PdfExtractionError:
        raise
    except Exception as exc:
        raise PdfExtractionError(f"Could not read PDF: {exc}") from exc
    chunks: list[str] = []
    for page in pages:
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            raise PdfExtractionError(f"Failed to extract text from a page: {exc}") from exc
        if text.strip():
            chunks.append(text)

    combined = "\n".join(chunks).strip()
    if not combined:
        raise PdfExtractionError(
            "No extractable text found in the PDF (it may be a scanned image with no text layer)"
        )

    return combined[: settings.document_max_chars]
