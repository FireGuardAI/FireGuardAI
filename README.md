# FireGuard AI

Fire-safety compliance auditing platform: upload a building description
(text or PDF), get a fire-code compliance report against the applicable
regulations, with an AI-generated executive summary.

## Architecture

```
frontend (React, :3000)
    │
    ▼
api-gateway (:8090 → container :8080)  ── postgres (:5433)
    │
    ├──▶ agent-intake      (:8004)  Groq — extracts structured building details
    ├──▶ agent-compliance  (:8002)  Gemini — checklist-driven compliance audit
    └──▶ agent-report      (:8003)  Groq/Gemini — executive summary

agent-orchestrator (:8020)  ── postgres (:5433, audit_tool_trace)
    │  Gemini agentic loop — an alternative to agent-compliance's fixed
    │  checklist: investigates via MCP tool calls instead of a
    │  pre-computed query list. Talks to the *-mcp sidecars below,
    │  not the REST services directly.
    ├──▶ agent-retrieval-mcp (:8011)
    ├──▶ agent-intake-mcp    (:8014)
    └──▶ agent-report-mcp    (:8013)

agent-retrieval (:8001) + agent-retrieval-mcp (:8011)
    │  Hybrid search (dense + sparse) over the regulation corpus
    ▼
chromadb (:8000)  +  SQLite FTS5 sparse index
    ▲
    │  one-shot indexing job
  ingest  (services/vector-store/raw_documents/*.pdf → chromadb + FTS5)
```

Each backend service lives under `services/<name>/` with its own
`app/`, `docker/Dockerfile`, `requirements.txt`, and `.env.example`. The
frontend lives at `frontend/`. Every service keeps its own
`docker-compose.yml` too (for standalone/legacy use), but the root
`docker-compose.yml` in this directory is what actually brings up the
whole stack — one shared network, real `depends_on` chains, no
`external: true` guessed network names.

## Prerequisites

- Docker + Docker Compose v2 (`docker compose version`)
- API keys: a [Groq](https://console.groq.com/keys) key (intake, report)
  and a [Gemini](https://aistudio.google.com/apikey) key (compliance,
  report fallback, orchestrator)

## First-time setup

1. **Root env file** — shared Postgres credentials and the frontend's
   build-time API URL:
   ```
   cp .env.example .env
   ```
   Edit `.env` and set a real `POSTGRES_PASSWORD`.

2. **Per-service env files** — every service needs its own `.env`:
   ```
   cp services/agent-compliance/.env.example   services/agent-compliance/.env
   cp services/agent-intake/.env.example       services/agent-intake/.env
   cp services/agent-report/.env.example       services/agent-report/.env
   cp services/agent-retrieval/.env.example    services/agent-retrieval/.env
   cp services/agent-orchestrator/.env.example services/agent-orchestrator/.env
   cp services/api-gateway/.env.example        services/api-gateway/.env
   cp services/vector-store/.env.example       services/vector-store/.env
   cp frontend/.env.example                    frontend/.env
   ```
   Then fill in, at minimum:
   - `services/agent-compliance/.env` → `GEMINI_API_KEY`
   - `services/agent-intake/.env` → `GROQ_API_KEY`
   - `services/agent-report/.env` → `GROQ_API_KEY`, `GEMINI_API_KEY`
   - `services/agent-orchestrator/.env` → `GEMINI_API_KEY`
   - `services/api-gateway/.env` → `JWT_SECRET`, `INTERNAL_API_KEY`,
     `POSTGRES_PASSWORD` (must match the root `.env`), `UPLOAD_ENCRYPTION_KEY`,
     `SIGNING_SECRET`, `API_KEYS` — see the comments in that file for how
     each is derived.

   `agent-orchestrator`'s and `api-gateway`'s `DATABASE_URL` /
   `POSTGRES_*` values are actually overridden by the root
   `docker-compose.yml` from the root `.env` at container-start time, so
   the copies inside their own `.env` files only matter if you ever run
   those services' individual `docker-compose.yml` standalone.

3. **Place the regulation corpus** — put the source PDF(s) to be indexed
   into `services/vector-store/raw_documents/`.

## Bringing the stack up

```
docker compose up -d --build
```

First run needs the regulation corpus indexed before retrieval/compliance
checks will find anything:

```
docker compose --profile ingest run --rm ingest
```

Re-run `ingest` any time `raw_documents/` changes.

Check everything is healthy:

```
docker compose ps
```

Then open the app: **http://localhost:3000**

## Individual service endpoints (for direct testing)

| Service | URL | Purpose |
|---|---|---|
| frontend | http://localhost:3000 | the app |
| api-gateway | http://localhost:8090 | REST front door (auth, uploads, billing) |
| agent-intake | http://localhost:8004/health | building-detail extraction |
| agent-compliance | http://localhost:8002/health | checklist-driven audit |
| agent-report | http://localhost:8003/health | executive summary drafting |
| agent-retrieval | http://localhost:8001/health | hybrid regulation search |
| agent-orchestrator | http://localhost:8020/health | agentic-loop audit (`POST /api/v1/audit`) |
| chromadb | http://localhost:8000 | vector store |
| chromadb-ui | http://localhost:3001 | browse the vector store |
| postgres | localhost:5433 | shared database |

## Bringing the stack down

```
docker compose down
```

Add `-v` to also drop the Postgres volume (loses all audit/account data —
do not do this in anything but a throwaway dev environment).

## Rebuilding after code changes

```
docker compose up -d --build <service-name>
```

e.g. `docker compose up -d --build agent-compliance`.

## Repository layout

```
fireguard-monorepo/
├── docker-compose.yml          ← brings up the whole stack (this file)
├── .env.example                ← shared Postgres creds + frontend build URL
├── services/
│   ├── agent-compliance/       Gemini checklist-driven compliance engine
│   ├── agent-intake/           Groq building-detail extraction + PDF intake
│   ├── agent-report/           Groq/Gemini executive-summary drafting
│   ├── agent-retrieval/        Hybrid (dense+sparse) regulation search
│   ├── agent-orchestrator/     Gemini agentic-loop audit (MCP-based)
│   ├── api-gateway/            Auth, billing, upload handling, Postgres
│   └── vector-store/           ChromaDB + FTS5 index, PDF ingestion job
└── frontend/                   React app
```
