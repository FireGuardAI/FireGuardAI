"""The agentic loop itself — replaces compliance_engine.analyze()'s
single "dump everything into one prompt" call with a real tool-calling
conversation. See app/prompts.py for the system prompt and
app/mcp_toolbox.py for how tool calls actually get dispatched.

Termination is always one of:
1. The model calls submit_audit — normal completion.
2. The orchestrator hits its turn/tool-call budget (settings.max_loop_turns
   / settings.max_tool_calls) and forces a structured-output finalization
   call with no tools available — guaranteed termination regardless of
   model behavior. This budget is enforced in Python, never left to the
   model to decide, because an unbounded loop is not viable at Gemini's
   free-tier daily quota (see config.py's comment on this).
"""
import asyncio
import json
import time

from google import genai
from google.genai import types
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.logger import get_logger
from app.mcp_toolbox import MCPToolbox
from app.prompts import build_agent_system_prompt
from app.schemas import ComplianceRuleCheck
from app.trace import trace_store

logger = get_logger(__name__)

SUBMIT_AUDIT_TOOL = {
    "name": "submit_audit",
    "description": (
        "Finalize the audit with your complete list of checks and a "
        "narrative summary. Call this exactly once, only when you are "
        "genuinely done investigating."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "detailed_checks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "rule_clause": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": [
                                "COMPLIANT",
                                "NON_COMPLIANT",
                                "PARTIAL",
                                "INSUFFICIENT_DATA",
                                "NEEDS_CLARIFICATION",
                                "NOT_APPLICABLE",
                            ],
                        },
                        "finding": {"type": "string"},
                        "recommendation": {"type": "string"},
                    },
                    "required": ["rule_clause", "status", "finding"],
                },
            },
            "summary": {"type": "string"},
        },
        "required": ["detailed_checks", "summary"],
    },
}


class _FinalAudit(BaseModel):
    detailed_checks: list[ComplianceRuleCheck]
    summary: str


def _tool_declarations(toolbox: MCPToolbox) -> types.Tool:
    decls = [
        types.FunctionDeclaration(
            name=t["name"], description=t["description"], parameters_json_schema=t["inputSchema"]
        )
        for t in toolbox.tool_schemas
    ]
    decls.append(
        types.FunctionDeclaration(
            name=SUBMIT_AUDIT_TOOL["name"],
            description=SUBMIT_AUDIT_TOOL["description"],
            parameters_json_schema=SUBMIT_AUDIT_TOOL["inputSchema"],
        )
    )
    return types.Tool(function_declarations=decls)


class AgentLoopResult(BaseModel):
    detailed_checks: list[ComplianceRuleCheck]
    summary: str
    loop_turns_used: int
    tool_calls_used: int
    terminated_by: str


class AgentLoop:
    def __init__(self):
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model_name = settings.gemini_model_name

    @retry(
        stop=stop_after_attempt(settings.gemini_max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _generate(self, contents: list, config: types.GenerateContentConfig):
        return await asyncio.wait_for(
            self._client.aio.models.generate_content(
                model=self._model_name, contents=contents, config=config
            ),
            timeout=settings.gemini_timeout_seconds,
        )

    async def run(self, audit_id: str, building_details: dict, raw_description: str | None, toolbox: MCPToolbox) -> AgentLoopResult:
        tool_config = types.GenerateContentConfig(
            system_instruction=build_agent_system_prompt(),
            tools=[_tool_declarations(toolbox)],
        )

        seed_text = f"[BUILDING DETAILS]\n{json.dumps(building_details, indent=2, default=str)}\n"
        if raw_description:
            seed_text += f"\n[ORIGINAL DESCRIPTION]\n{raw_description}\n"
        seed_text += "\nBegin your investigation. Call corpus_list_chapters and corpus_list_purpose_groups_present first if it would help you plan."

        contents: list[types.Content] = [
            types.Content(role="user", parts=[types.Part(text=seed_text)])
        ]

        seen_calls: set[tuple[str, str]] = set()
        tool_calls_used = 0
        turn = 0

        while turn < settings.max_loop_turns:
            turn += 1
            response = await self._generate(contents, tool_config)
            candidate = response.candidates[0]
            if candidate.content is None or not candidate.content.parts:
                # Blocked/empty turn (e.g. safety filter, MAX_TOKENS with
                # no content) — nudge and retry rather than crashing on
                # the None the SDK returns in this case.
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part(text="Your last response was empty. Continue investigating with your tools, or call submit_audit to finish.")],
                    )
                )
                continue
            contents.append(candidate.content)

            function_calls = [p.function_call for p in candidate.content.parts if p.function_call]
            if not function_calls:
                # Model returned plain text instead of calling a tool —
                # nudge it back toward the loop contract rather than
                # silently ending the audit on a stray text turn.
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part(text="Continue investigating with your tools, or call submit_audit to finish.")],
                    )
                )
                continue

            response_parts = []
            for call in function_calls:
                if call.name == "submit_audit":
                    final = _FinalAudit(**call.args)
                    return AgentLoopResult(
                        detailed_checks=final.detailed_checks,
                        summary=final.summary,
                        loop_turns_used=turn,
                        tool_calls_used=tool_calls_used,
                        terminated_by="model_submitted",
                    )

                dedup_key = (call.name, json.dumps(call.args, sort_keys=True, default=str))
                tool_calls_used += 1
                t0 = time.monotonic()

                if dedup_key in seen_calls:
                    result_summary = "DUPLICATE CALL — you already tried this exact query. Refine it or move to a different topic."
                    is_error = True
                    payload = {"error": result_summary}
                else:
                    seen_calls.add(dedup_key)
                    tool_result = await toolbox.call(call.name, dict(call.args))
                    is_error = tool_result.is_error
                    payload = tool_result.data if not is_error else {"error": tool_result.raw_text}
                    result_summary = tool_result.raw_text[:2000] if tool_result.raw_text else json.dumps(payload, default=str)[:2000]

                latency_ms = int((time.monotonic() - t0) * 1000)
                await trace_store.record(
                    audit_id=audit_id,
                    turn_number=turn,
                    tool_name=call.name,
                    arguments=dict(call.args),
                    result_summary=result_summary,
                    is_error=is_error,
                    latency_ms=latency_ms,
                )

                response_parts.append(
                    types.Part(function_response=types.FunctionResponse(name=call.name, response={"result": payload}))
                )

                if tool_calls_used >= settings.max_tool_calls:
                    break

            contents.append(types.Content(role="user", parts=response_parts))

            if tool_calls_used >= settings.max_tool_calls:
                logger.warning(f"audit {audit_id}: tool-call budget ({settings.max_tool_calls}) exhausted, forcing finalization")
                break

        return await self._force_finalize(audit_id, contents, turn, tool_calls_used)

    async def _force_finalize(self, audit_id: str, contents: list, turns_used: int, tool_calls_used: int) -> AgentLoopResult:
        """Guaranteed termination path: no tools offered, structured
        output required, so the model MUST return a valid final audit
        from whatever it has gathered so far — this is what makes the
        turn/tool-call budget a real hard stop rather than a suggestion."""
        finalize_config = types.GenerateContentConfig(
            system_instruction=(
                build_agent_system_prompt()
                + "\n\nYou have used your entire tool-call budget for this audit. "
                "Finalize NOW using only what you have already gathered above — "
                "mark anything you didn't get to resolve as INSUFFICIENT_DATA."
            ),
            response_mime_type="application/json",
            response_schema=_FinalAudit,
        )
        contents.append(
            types.Content(role="user", parts=[types.Part(text="Finalize your audit now with the submit_audit schema.")])
        )
        response = await self._generate(contents, finalize_config)
        final: _FinalAudit = response.parsed
        return AgentLoopResult(
            detailed_checks=final.detailed_checks,
            summary=final.summary,
            loop_turns_used=turns_used,
            tool_calls_used=tool_calls_used,
            terminated_by="budget_exhausted",
        )
