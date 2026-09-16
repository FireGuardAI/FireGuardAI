"""Groq-based intake/guardrail engine — analyzes raw user input for
safety, domain relevance, and normalizes it into structured fields.

Retries transient Groq failures (rate limits, network errors) with
exponential backoff via tenacity — the reference doc's AsyncGroq usage
was correct (unlike fireguard-agent-report's original blocking sync
client), but had no retry logic at all.

Response parsing is defensive: Groq's response_format={"type":
"json_object"} is a strong hint, not a guaranteed-schema-conformant
output (same caveat as the deprecated google-generativeai SDK in
fireguard-agent-compliance) — malformed JSON or a shape mismatch raises
a clean IntakeResponseParsingError instead of an uncaught crash.
"""
import asyncio
import json

from groq import AsyncGroq
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.exceptions import IntakeEngineError, IntakeResponseParsingError
from app.logger import get_logger
from app.prompts import INTAKE_SYSTEM_PROMPT
from app.schemas import SanitizedBuildingDetails

logger = get_logger(__name__)


class IntakeEngine:
    def __init__(self):
        self._client = AsyncGroq(api_key=settings.groq_api_key)
        logger.info(f"IntakeEngine ready (model={settings.groq_model_name})")

    @retry(
        stop=stop_after_attempt(settings.groq_max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def _generate(self, raw_text: str) -> str:
        response = await asyncio.wait_for(
            self._client.chat.completions.create(
                messages=[
                    {"role": "system", "content": INTAKE_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Analyze this raw input:\n{raw_text}",
                    },
                ],
                model=settings.groq_model_name,
                response_format={"type": "json_object"},
                temperature=0.0,
            ),
            timeout=settings.groq_timeout_seconds,
        )
        content = response.choices[0].message.content
        if not content or not content.strip():
            raise IntakeEngineError("Groq returned an empty completion")
        return content

    async def self_check(self) -> None:
        """Used by /health/groq — one minimal real API call."""
        try:
            await asyncio.wait_for(
                self._client.chat.completions.create(
                    messages=[
                        {"role": "user", "content": "Respond with exactly: OK"}
                    ],
                    model=settings.groq_model_name,
                    max_tokens=5,
                ),
                timeout=settings.groq_timeout_seconds,
            )
        except Exception as exc:
            raise IntakeEngineError(f"Groq self-check failed: {exc}") from exc

    @staticmethod
    def _parse_response(raw_text: str) -> SanitizedBuildingDetails:
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise IntakeResponseParsingError(
                f"Groq did not return valid JSON: {exc}"
            ) from exc

        try:
            return SanitizedBuildingDetails(**parsed)
        except ValidationError as exc:
            raise IntakeResponseParsingError(
                f"Groq's JSON didn't match the expected schema: {exc}"
            ) from exc

    async def process_input(self, raw_text: str) -> SanitizedBuildingDetails:
        try:
            raw_response = await self._generate(raw_text)
        except Exception as exc:
            raise IntakeEngineError(
                f"Groq API call failed after {settings.groq_max_retries} "
                f"attempts: {exc}"
            ) from exc

        return self._parse_response(raw_response)
