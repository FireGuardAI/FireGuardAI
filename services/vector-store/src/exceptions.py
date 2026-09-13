class FireGuardError(Exception):
    """Base exception for the FireGuard vector store domain."""


class PDFProcessingError(FireGuardError):
    """Raised when a PDF cannot be parsed or chunked."""


class VectorStoreConnectionError(FireGuardError):
    """Raised when the ChromaDB connection fails."""


class EmbeddingGenerationError(FireGuardError):
    """Raised when embedding generation fails."""


class SparseIndexError(FireGuardError):
    """Raised when the BM25 sparse index cannot be built or saved."""
