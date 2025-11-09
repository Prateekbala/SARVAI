# SARVAI — Universal AI Memory Layer (MVP)

SARVAI is a local-first, multi-modal memory infrastructure for AI applications. It provides persistent, searchable, and compressed memory for text, images, PDFs, and audio so agents and models can remember and reason over a user's data across sessions.

This repository contains the SARVAI MVP: a FastAPI backend (PostgreSQL + pgvector, MinIO), a Next.js frontend, basic ingestion and vector search, and a roadmap for multi-modal and web-aware RAG functionality.

## Key features

- Multi-modal ingestion (text, image, PDF, audio)
- Vector embeddings and semantic search (pgvector)
- File storage via MinIO (S3-compatible)
- RAG-ready APIs for context-aware Q&A
- Local-first design (privacy-friendly) with optional web augmentation

## Project goals

SARVAI aims to be the foundational memory layer for AI systems: a unified persistent memory that is multi-modal, personal, and evolves over time (clustering and compression planned in later phases).

## Tech stack

- Backend: Python, FastAPI, async/await, Pydantic, SQLAlchemy
- Database: PostgreSQL with pgvector extension
- Object storage: MinIO (S3-compatible)
- Embeddings: sentence-transformers (all-MiniLM-L6-v2 by default)
- Frontend: Next.js 14, TypeScript, Tailwind CSS
- Dev environment: Docker Compose for local development

## Repository layout

Top-level layout (relevant folders/files):

```
backend/
  requirements.txt
  app/
    config.py
    database.py
    api/
    models/
    schemas/
    services/
frontend/
  package.json
  app/
docker-compose.yml
Goals.txt
sarvai_short_prompt.md
```

## Quick start (local development)

Prerequisites:

- Docker & Docker Compose
- Python 3.11+ (for optional direct backend runs)
- Node 18+ / pnpm or npm (for frontend development)

1. Clone the repository

```bash
git clone https://github.com/<your-org>/SARVAI.git
cd SARVAI
```

2. Copy environment files and configure (example `.env` values are described below)

```bash
cp backend/.env.example backend/.env
# edit backend/.env as needed
```

3. Start basic services with Docker Compose (Postgres + MinIO)

```bash
docker compose up -d
```

4. Backend (inside a Python virtualenv) — optional if using Docker

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# run migrations (if configured) and start FastAPI
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Frontend

```bash
cd frontend
npm install
npm run dev
# or: pnpm install && pnpm dev
```

Now open the frontend (usually http://localhost:3000) and the API docs at http://localhost:8000/docs.

## Environment variables (important)

Example variables used by the project (set these in `backend/.env`):

```
DATABASE_URL=postgresql://user:password@localhost:5432/sarvai
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=sarvai
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
OPENAI_API_KEY=sk-xxx  # optional
BRAVE_API_KEY=xxx  # for web search (optional)
```

Ensure the Postgres instance has the `pgvector` extension installed (the provided docker image `pgvector/pgvector` includes it).

## API overview

The project follows a versioned API pattern under `/api/v1`. Example endpoints planned or implemented in the MVP:

- POST `/api/v1/remember/text` — ingest plain text (chunks & embeddings)
- POST `/api/v1/remember/image` — upload image (MinIO) + OCR + embeddings
- POST `/api/v1/remember/pdf` — upload PDF + extract text + embeddings
- POST `/api/v1/remember/audio` — upload audio + transcription + embeddings
- GET `/api/v1/search?q={query}` — semantic search across memories
- POST `/api/v1/ask` — RAG-style Q&A endpoint (builds context + queries an LLM)
- GET `/api/v1/memories` — list stored memories

FastAPI automatic docs are available at `/docs` (Swagger UI) when the backend is running.

## Database & embeddings

- The schema uses a `memories` table and an `embeddings` table (embedding vectors stored via `pgvector`).
- Default embedding model: `sentence-transformers/all-MiniLM-L6-v2` (fast). You can replace this with a higher-quality model such as `all-mpnet-base-v2` if needed.

## Testing

- Backend: add pytest-based unit tests under `backend/tests/` (recommended). Run with:

```bash
cd backend
pytest -q
```

- Frontend: use the project's chosen test runner (Vitest / Jest) depending on `package.json` configuration.

## Development workflow

- Use the provided Docker Compose to run Postgres and MinIO locally.
- Develop the backend with `uvicorn --reload` and the frontend with `npm run dev`.
- Keep environment-specific secrets out of the repository; use `.env` files or a secrets manager.

## Security and privacy notes

- SARVAI is designed to be local-first. When running locally, data and embeddings remain under your control (Postgres + MinIO instances). If you enable any cloud services or third-party APIs (OpenAI, Brave, etc.), review their policies and never commit API keys to the repository.
- Validate and sanitize file uploads and limit file sizes as defined in project guidelines.

## Roadmap & next phases

Planned improvements (see `sarvai_short_prompt.md` and `Goals.txt`):

- Cross-modal linking and episodic memory compression
- Web-aware memory and web search integration
- Improved clustering and neural compression for long-term scaling
- Authentication, multi-user isolation, and production deployment

