# fireguard-agent-intake

The front door of the FireGuard platform — validates and sanitizes raw
user input before anything else in the system sees it. Checks for
prompt-injection/malicious payloads, verifies the request is actually
fire-safety-related, and normalizes messy free text ("5 story office")
into structured `BuildingContext`-shaped JSON for downstream services.

## Build status

- [x] **Step 1** — FastAPI skeleton, config/logger/exceptions, `/health`,
      Dockerized + joined to `fireguard-vector-store`'s Docker network
- [x] **Step 2** — Intake engine (Groq integration, retry + defensive parsing), `/health/groq`
- [ ] Step 3 — `/api/v1/intake` endpoint
- [ ] Step 4 — Production hardening (pre-filter layer, rate limiting, tests)

## Prerequisites

- A free Groq API key from https://console.groq.com/keys

## Step 1 — Run locally

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env
# edit .env and set GROQ_API_KEY (required — the app won't start without it)

uvicorn app.main:app --reload --port 8004
```

Test it:
```bash
curl.exe http://localhost:8004/health
```
Expected:
```json
{"status":"ok","service":"FireGuard Intake Agent"}
```

## Step 1 — Run with Docker

```powershell
Copy-Item .env.example .env
# edit .env and set GROQ_API_KEY
docker compose up -d --build
```

Test it:
```powershell
curl.exe http://localhost:8004/health
docker ps   # fireguard-agent-intake should show (healthy)
```

If it fails with a "network not found" error, see the same
troubleshooting note in `fireguard-agent-retrieval`'s README — your
`fireguard-vector-store` folder name needs to match what's in
`docker-compose.yml`'s `networks:` section.

Port `8004` — `8000` is ChromaDB, `8001` is `fireguard-agent-retrieval`,
`8002` is `fireguard-agent-compliance` (`8003` is `fireguard-agent-report`).

## Step 2 — Intake engine (Groq)

`app/services/intake_engine.py` — the reference doc's `AsyncGroq` usage
was already correct (unlike `fireguard-agent-report`'s original blocking
sync client bug), but had no retry logic and no defensive response
parsing. Both added here: Groq gets `GROQ_MAX_RETRIES` attempts
(exponential backoff), and malformed/schema-mismatched JSON raises a
clean `IntakeResponseParsingError` instead of an uncaught crash.

```powershell
docker compose up -d --build
curl.exe http://localhost:8004/health/groq
```

Expected:
```json
{"status":"ok","model":"llama-3.1-8b-instant"}
```

Makes one real (tiny) Groq API call — don't poll it tightly.
