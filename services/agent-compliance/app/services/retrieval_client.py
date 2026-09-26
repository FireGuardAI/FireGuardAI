import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.exceptions import RetrievalClientError
from app.logger import get_logger

logger = get_logger(__name__)


class _RetryableRetrievalError(Exception):
    """Internal signal for tenacity to retry on — never raised past
    get_relevant_chunks(), which converts it to RetrievalClientError."""


class RetrievalClient:
    def __init__(self):
        self._base_url = settings.retrieval_service_url.rstrip("/")
        self._timeout = settings.retrieval_timeout_seconds
        logger.info(f"RetrievalClient targeting {self._base_url}")

    async def health_check(self) -> dict:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(f"{self._base_url}/health")
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            raise RetrievalClientError(
                f"Could not reach retrieval agent at {self._base_url}: {exc}"
            ) from exc

    @retry(
        retry=retry_if_exception_type(_RetryableRetrievalError),
        stop=stop_after_attempt(settings.retrieval_max_retries),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
        reraise=True,
    )
    async def _post_retrieve(self, query: str, top_k: int) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/api/v1/retrieve",
                    json={"query": query, "top_k": top_k},
                )
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            raise _RetryableRetrievalError(str(exc)) from exc

        if response.status_code >= 500:
            raise _RetryableRetrievalError(
                f"retrieval agent returned {response.status_code}"
            )
        if response.status_code >= 400:
            raise RetrievalClientError(
                f"Retrieval agent rejected request: "
                f"{response.status_code} {response.text}"
            )

        return response.json()

    async def get_relevant_chunks(
        self, query: str, top_k: int | None = None
    ) -> list[dict]:
        try:
            return await self._post_retrieve(query, top_k or settings.retrieval_top_k)
        except _RetryableRetrievalError as exc:
            raise RetrievalClientError(
                f"Retrieval agent unreachable after "
                f"{settings.retrieval_max_retries} attempts: {exc}"
            ) from exc

    @retry(
        retry=retry_if_exception_type(_RetryableRetrievalError),
        stop=stop_after_attempt(settings.retrieval_max_retries),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
        reraise=True,
    )
    async def _post_retrieve_by_classification(
        self, chapters: list[int], purpose_group: int | None, limit: int, query: str | None
    ) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/api/v1/retrieve/by-classification",
                    json={
                        "chapters": chapters,
                        "purpose_group": purpose_group,
                        "limit": limit,
                        "query": query,
                    },
                )
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            raise _RetryableRetrievalError(str(exc)) from exc

        if response.status_code >= 500:
            raise _RetryableRetrievalError(
                f"retrieval agent returned {response.status_code}"
            )
        if response.status_code >= 400:
            raise RetrievalClientError(
                f"Retrieval agent rejected classification request: "
                f"{response.status_code} {response.text}"
            )

        return response.json()

    async def get_chunks_by_classification(
        self,
        purpose_group: int | None,
        limit: int = 40,
        chapters: list[int] | None = None,
        query: str | None = None,
    ) -> list[dict]:
        """Structured fetch of every chunk tagged for the given Purpose
        Group — see agent-retrieval's /api/v1/retrieve/by-classification.
        `chapters` defaults to the whole corpus (not just Chapter 6):
        occupancy-specific override provisions are scattered across
        chapters, not confined to a fixed subset. `query`, typically a
        description of the building, only affects ranking when the
        Purpose Group filter alone matches more than `limit` chunks."""
        try:
            return await self._post_retrieve_by_classification(
                chapters or [], purpose_group, limit, query
            )
        except _RetryableRetrievalError as exc:
            raise RetrievalClientError(
                f"Retrieval agent unreachable after "
                f"{settings.retrieval_max_retries} attempts: {exc}"
            ) from exc
