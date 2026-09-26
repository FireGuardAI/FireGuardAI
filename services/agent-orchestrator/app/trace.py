"""Persists every MCP tool call the agent loop makes, in both
directions, keyed by a correlation id (audit_id) — this is the concrete
mechanism behind "observability is a must" for the agentic migration.
Without this, a NON_COMPLIANT/NEEDS_CLARIFICATION verdict from a loop
that made a dozen tool calls with self-refined queries would be
unexplainable after the fact, which matters more here than in a typical
app: this is a compliance product, and a human auditor needs to be able
to reconstruct exactly what the model tried and why it stopped trying.

A Postgres table, not a log file, because this needs to be queryable per
audit (and, later, across audits for accuracy analysis — the same kind
of analysis this project's iteration_validation work has been doing by
hand all session). Lives in the same Postgres instance fireguard-api
already owns (report_sessions, etc.), not a new database.
"""
import json
from datetime import datetime, timezone

import asyncpg

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS audit_tool_trace (
    id BIGSERIAL PRIMARY KEY,
    audit_id UUID NOT NULL,
    turn_number INT NOT NULL,
    tool_name TEXT NOT NULL,
    arguments JSONB NOT NULL,
    result_summary TEXT,
    is_error BOOLEAN NOT NULL DEFAULT FALSE,
    latency_ms INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audit_tool_trace_audit_id ON audit_tool_trace(audit_id);
"""


class TraceStore:
    def __init__(self):
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=5)
        async with self._pool.acquire() as conn:
            await conn.execute(_CREATE_TABLE_SQL)
        logger.info("TraceStore ready (audit_tool_trace table present)")

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()

    async def record(
        self,
        audit_id: str,
        turn_number: int,
        tool_name: str,
        arguments: dict,
        result_summary: str,
        is_error: bool,
        latency_ms: int,
    ) -> None:
        if self._pool is None:
            logger.warning(f"TraceStore not connected — dropping trace record for {tool_name}")
            return
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO audit_tool_trace
                    (audit_id, turn_number, tool_name, arguments, result_summary, is_error, latency_ms, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                audit_id,
                turn_number,
                tool_name,
                json.dumps(arguments, default=str),
                result_summary[:4000],
                is_error,
                latency_ms,
                datetime.now(timezone.utc),
            )

    async def get_trace(self, audit_id: str) -> list[dict]:
        if self._pool is None:
            return []
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT turn_number, tool_name, arguments, result_summary, is_error, latency_ms, created_at
                FROM audit_tool_trace WHERE audit_id = $1 ORDER BY id
                """,
                audit_id,
            )
        return [dict(r) for r in rows]


trace_store = TraceStore()
