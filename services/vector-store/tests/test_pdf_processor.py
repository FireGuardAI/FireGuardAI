from src.pdf_processor import DocumentChunk, PDFProcessor


def test_document_chunk_is_immutable():
    chunk = DocumentChunk(text="a", source="b", page_number=1, chunk_id="b_p1_0")
    try:
        chunk.text = "changed"
        assert False, "DocumentChunk should be frozen"
    except AttributeError:
        pass


def test_pdf_processor_initializes_with_defaults():
    processor = PDFProcessor()
    assert processor is not None
