from sentence_transformers import SentenceTransformer

from src.config import settings
from src.exceptions import EmbeddingGenerationError
from src.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    def __init__(self, model_name: str | None = None):
        self._model_name = model_name or settings.embedding_model_name
        logger.info(f"Loading embedding model: {self._model_name}")
        self._model = SentenceTransformer(self._model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            embeddings = self._model.encode(
                texts,
                batch_size=settings.embedding_batch_size,
                show_progress_bar=False,
            )
            return embeddings.tolist()
        except Exception as exc:
            raise EmbeddingGenerationError(str(exc)) from exc
