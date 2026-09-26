import asyncio
import json

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.exceptions import ComplianceEngineError, LLMResponseParsingError
from app.logger import get_logger
from app.prompts import COMPLIANCE_SYSTEM_PROMPT
from app.schemas import ComplianceAssessment
from app.services.audit_topics import render_checklist

logger = get_logger(__name__)


class ComplianceEngine:
    def __init__(self):
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model_name = settings.gemini_model_name
        self._generation_config = types.GenerateContentConfig(
            system_instruction=COMPLIANCE_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=ComplianceAssessment,
        )
        logger.info(f"ComplianceEngine ready (model={self._model_name})")

    @retry(
        stop=stop_after_attempt(settings.gemini_max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _generate(self, prompt: str):
        return await asyncio.wait_for(
            self._client.aio.models.generate_content(
                model=self._model_name,
                contents=prompt,
                config=self._generation_config,
            ),
            timeout=settings.gemini_timeout_seconds,
        )

    async def self_check(self) -> None:
        try:
            await self._client.aio.models.generate_content(
                model=self._model_name,
                contents="Respond with exactly: OK",
            )
        except Exception as exc:
            raise ComplianceEngineError(f"Gemini self-check failed: {exc}") from exc

    async def analyze(
        self,
        building_info: dict,
        retrieved_chunks: list[dict],
        topics: list[tuple[str, str]],
        occupancy_specific_chunks: list[dict] | None = None,
        raw_description: str | None = None,
    ) -> ComplianceAssessment:
        context_str = "\n\n".join(
            f"--- Chunk (Page {c.get('metadata', {}).get('page')}) ---\n{c['text']}"
            for c in retrieved_chunks
        )

        occupancy_section = ""
        if occupancy_specific_chunks:
            occupancy_context_str = "\n\n".join(
                f"--- Chunk (Page {c.get('metadata', {}).get('page')}) ---\n{c['text']}"
                for c in occupancy_specific_chunks
            )
            occupancy_section = f"""
[OCCUPANCY-SPECIFIC REGULATION CONTEXT — Chapters 2/3/4/6, this building's Purpose Group]
This section was NOT selected by a hand-written topic — it is every
regulation chunk across Means of Escape, Structural Fire Precautions,
Detection/Alarm, and Special Uses tagged (or, within this scope,
untagged-and-likely-general) for this building's occupancy
classification, ranked by relevance to this specific building.
Identify EVERY distinct regulatory requirement in it that is relevant to
the stated Building Details (ignore requirements for a clearly different
occupancy sub-type, e.g. skip kitchen/car-park clauses for a cinema) and
add ONE ADDITIONAL check per requirement to detailed_checks, AFTER the
fixed checklist items above, citing the specific Reg./Table clause. Do
not force these into the fixed checklist topics — they are separate,
additional checks.
{occupancy_context_str}
"""

        raw_description_section = ""
        if raw_description:
            raw_description_section = f"""
[ORIGINAL BUILDING DESCRIPTION — as written by the user]
Building Details above is a structured extraction and may not capture
every fact — cross-reference this original text too. If it states a
fact relevant to a check (fixed or additional) that Building Details
doesn't have a field for, use it rather than treating that fact as
unknown.
{raw_description}
"""

        prompt = f"""
[AUDIT CHECKLIST for this building — produce exactly one check per topic, in order]
{render_checklist(topics)}

[BUILDING DETAILS]
{json.dumps(building_info, indent=2)}
{raw_description_section}
[FIRE REGULATION CONTEXT]
{context_str}
{occupancy_section}
Perform a complete compliance check.
"""

        try:
            response = await self._generate(prompt)
        except Exception as exc:
            # str(exc) is empty for a bare asyncio.TimeoutError (raised by
            # the wait_for in _generate when Gemini doesn't respond within
            # gemini_timeout_seconds) — always include the exception type
            # so a timeout doesn't surface as an unexplained blank message.
            detail = str(exc) or f"timed out after {settings.gemini_timeout_seconds}s"
            raise ComplianceEngineError(
                f"Gemini API call failed after {settings.gemini_max_retries} "
                f"attempts ({type(exc).__name__}): {detail}"
            ) from exc

        result = response.parsed
        if result is None:
            raw_preview = (response.text or "")[:500]
            raise LLMResponseParsingError(
                f"Gemini did not return a schema-conformant response "
                f"(raw text preview: {raw_preview!r})"
            )
        return result
