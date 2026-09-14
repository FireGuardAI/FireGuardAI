# fireguard-vector-store

Production-grade ChromaDB vector store for the FireGuard fire-safety research
platform. Hybrid dense (embedding) + sparse (BM25) retrieval over CIDA/NFPA
regulation documents.

## Architecture

```
src/
├── config.py            # Centralized, validated settings (Pydantic)
├── logger.py            # Structured logging
├── exceptions.py        # Domain-specific exceptions
├── pdf_processor.py      # PDF -> DocumentChunk (SRP)
├── embedding_service.py  # Text -> dense vectors (SRP)
├── vector_repository.py  # ChromaDB access (Repository pattern)
├── sparse_index.py       # BM25 sparse index (SRP)
└── ingest_pipeline.py     # Orchestrator (Facade, dependency-injected)
main.py                   # Composition root
```

Each module has a single responsibility and depends on `config.settings`
rather than hardcoded values. `main.py` is the only place concrete classes
are wired together, so every component can be unit-tested in isolation with
mocks.

## Setup

```bash
cp .env.example .env
# edit .env if you need non-default values

docker compose up -d chromadb
```

Wait for the container to report `(healthy)`:

```bash
docker ps
```

> Note: the `chromadb/chroma` image ships without curl/python/wget, so the
> healthcheck uses a bash-native `/dev/tcp` TCP probe instead of an external
> binary. Its persist path is `/data` (not `/chroma/chroma`), which is why
> the volume is mounted to `./data/chromadb:/data`.

## Caching (avoid re-downloading on every build/run)

- **pip packages** (torch, transformers, etc.) are cached via a Docker
  BuildKit cache mount (`RUN --mount=type=cache,target=/root/.cache/pip`
  in `docker/Dockerfile.ingest`). This persists across rebuilds even when
  `requirements.txt` changes, so wheels already downloaded once are never
  re-fetched.
- **The embedding model** (~90MB, `all-MiniLM-L6-v2`) is cached by
  bind-mounting `./data/hf_cache` to `/app/.cache/huggingface` inside the
  `ingest` container. Without this, every `docker compose --profile ingest
  up` would re-download it, since the container filesystem is ephemeral.
- `torch` is pinned to a **CPU-only** wheel (`torch==2.4.1+cpu` via
  `--extra-index-url https://download.pytorch.org/whl/cpu`) — otherwise
  `sentence-transformers` pulls in ~2.5GB of unused NVIDIA/CUDA libraries.

## Ingest a document

Drop a PDF into `raw_documents/`, then:

```bash
docker compose --profile ingest up --build
```

Or locally (without Docker), after `pip install -r requirements.txt`:

```bash
python main.py
```

## Running tests

```bash
pip install pytest
pytest tests/
```

## Linting / formatting

```bash
pip install ruff black mypy
ruff check .
black --check .
mypy src/
```
