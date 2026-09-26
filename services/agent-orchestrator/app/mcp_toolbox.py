"""The orchestrator's MCP CLIENT — connects to every MCP server
(retrieval+corpus, intake, report), discovers their tools, and exposes a
single dispatch surface the agent loop calls into. This is deliberately
the ONLY place that talks MCP: the loop itself just sees Python
dicts in and out, so agent_loop.py doesn't need to know which server
owns which tool.

One MCPToolbox instance per audit request (short-lived: connect at the
start of an audit, close at the end) rather than a long-lived shared
connection pool — Streamable HTTP sessions are cheap to open and this
avoids any cross-audit state leaking between MCP server sessions.
"""
import asyncio
import json
from contextlib import AsyncExitStack
from dataclasses import dataclass

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ToolResult:
    data: dict | list | str | None
    is_error: bool
    raw_text: str


class MCPToolbox:
    def __init__(self):
        self._stack = AsyncExitStack()
        self._sessions: dict[str, ClientSession] = {}
        self._tool_owner: dict[str, str] = {}  # tool name -> server key
        self.tool_schemas: list[dict] = []  # [{"name","description","inputSchema"}]

    async def connect(self) -> None:
        servers = {
            "retrieval": settings.retrieval_mcp_url,
            "intake": settings.intake_mcp_url,
            "report": settings.report_mcp_url,
        }
        for key, url in servers.items():
            read, write = await asyncio.wait_for(
                self._stack.enter_async_context(streamable_http_client(url)),
                timeout=settings.mcp_connect_timeout_seconds,
            )
            session = await self._stack.enter_async_context(ClientSession(read, write))
            await asyncio.wait_for(session.initialize(), timeout=settings.mcp_connect_timeout_seconds)
            self._sessions[key] = session

            listed = await asyncio.wait_for(session.list_tools(), timeout=settings.mcp_connect_timeout_seconds)
            for tool in listed.tools:
                if tool.name in self._tool_owner:
                    raise RuntimeError(
                        f"Tool name collision: '{tool.name}' is exposed by both "
                        f"'{self._tool_owner[tool.name]}' and '{key}' MCP servers"
                    )
                self._tool_owner[tool.name] = key
                self.tool_schemas.append(
                    {
                        "name": tool.name,
                        "description": tool.description or "",
                        "inputSchema": tool.input_schema,
                    }
                )
        logger.info(f"MCPToolbox connected: {len(self.tool_schemas)} tools across {len(servers)} servers")

    async def close(self) -> None:
        await self._stack.aclose()

    async def call(self, name: str, arguments: dict) -> ToolResult:
        server_key = self._tool_owner.get(name)
        if server_key is None:
            return ToolResult(data=None, is_error=True, raw_text=f"Unknown tool: {name}")

        session = self._sessions[server_key]
        try:
            result = await asyncio.wait_for(
                session.call_tool(name, arguments), timeout=settings.mcp_call_timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.warning(f"MCP tool call timed out: {name} (server={server_key}, timeout={settings.mcp_call_timeout_seconds}s)")
            return ToolResult(
                data=None,
                is_error=True,
                raw_text=f"Tool call to {name} timed out after {settings.mcp_call_timeout_seconds}s — try a different query or move to another topic.",
            )
        except Exception as exc:
            return ToolResult(data=None, is_error=True, raw_text=f"{type(exc).__name__}: {exc}")

        text_parts = [p.text for p in result.content if getattr(p, "text", None)]
        raw_text = "\n".join(text_parts)

        if result.is_error:
            return ToolResult(data=None, is_error=True, raw_text=raw_text or "Tool call failed")

        data = result.structured_content
        if data is None and raw_text:
            # The tool returned a dict/list but the server didn't opt into
            # structured_output — the SDK still serializes it as a JSON
            # text part, so recover the original structure from that
            # rather than treating a real dict payload as an opaque
            # string (confirmed this happened for draft_executive_summary:
            # the call succeeded and returned real JSON, but every field
            # was silently dropped downstream until this fallback).
            try:
                data = json.loads(raw_text)
            except (json.JSONDecodeError, ValueError):
                data = raw_text
        return ToolResult(data=data, is_error=False, raw_text=raw_text)
