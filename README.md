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

## Current Status

✅ **Week 1**: Text memory foundation (ingestion, embeddings, search)  
✅ **Week 2**: Multi-modal support (images, PDFs, audio)  
✅ **Week 3**: Advanced RAG + web search integration  
✅ **Week 4**: Authentication, personalization & production features  

**Now in production-ready state with:**
- JWT authentication
- User preferences & personalized search
- Analytics dashboard & timeline view
- Rate limiting & error handling
- Structured logging

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

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/sarvai

# MinIO (Object Storage)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=sarvai

# AI/ML
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Authentication (Week 4)
SECRET_KEY=<generate-with-openssl-rand-hex-32>
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM (Week 3)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest

# Optional APIs
OPENAI_API_KEY=sk-xxx
BRAVE_API_KEY=xxx  # for web search
```

Ensure the Postgres instance has the `pgvector` extension installed (the provided docker image `pgvector/pgvector` includes it).

## API overview

The project follows a versioned API pattern under `/api/v1`. Key endpoints:

**Authentication:**
- POST `/api/v1/users` — Create user with password
- POST `/api/v1/login` — Login and get JWT token

**Memory Management:**
- POST `/api/v1/remember/text` — Ingest plain text (chunks & embeddings)
- POST `/api/v1/remember/image` — Upload image (MinIO) + OCR + embeddings
- POST `/api/v1/remember/pdf` — Upload PDF + extract text + embeddings
- POST `/api/v1/remember/audio` — Upload audio + transcription + embeddings
- GET `/api/v1/search?q={query}` — Semantic search with personalization
- GET `/api/v1/memories` — List stored memories
- GET `/api/v1/memories/timeline` — Timeline view grouped by date

**RAG & Conversations:**
- POST `/api/v1/ask` — RAG-style Q&A endpoint (builds context + queries LLM)
- POST `/api/v1/ask/stream` — Streaming RAG responses
- GET `/api/v1/conversations` — List conversations
- POST `/api/v1/conversations` — Create conversation

**Personalization:**
- GET `/api/v1/preferences` — Get user preferences
- PUT `/api/v1/preferences` — Update preferences
- POST `/api/v1/preferences/boost/{topic}` — Boost topic in search
- POST `/api/v1/preferences/suppress/{topic}` — Suppress topic in search

**Analytics:**
- GET `/api/v1/stats/dashboard` — User statistics
- GET `/api/v1/stats/popular-searches` — Popular search queries

**Web Search:**
- POST `/api/v1/web/search` — Search and scrape web content
- POST `/api/v1/web/scrape` — Scrape specific URL

FastAPI automatic docs are available at `/docs` (Swagger UI) when the backend is running.

## Database & embeddings

- The schema uses a `memories` table and an `embeddings` table (embedding vectors stored via `pgvector`).
- Default embedding model: `sentence-transformers/all-MiniLM-L6-v2` (fast). You can replace this with a higher-quality model such as `all-mpnet-base-v2` if needed.

## Roadmap & next phases

Completed phases (see documentation in root):
- ✅ Week 1: Text memory foundation (`WEEK1_COMPLETE.md`)
- ✅ Week 2: Multi-modal support (`WEEK2_COMPLETE.md`)
- ✅ Week 3: Advanced RAG + web search (`WEEK3_COMPLETE.md`)
- ✅ Week 4: Authentication & personalization (`WEEK4_COMPLETE.md`)

Future improvements:
- Cross-modal linking and episodic memory compression
- Advanced clustering and neural compression for long-term scaling
- Multi-user collaboration features
- Production deployment guides

## Documentation

- **Quick References**: `WEEK*_QUICK_REFERENCE.md` for each phase
- **Implementation Details**: `WEEK*_IMPLEMENTATION_SUMMARY.md`
- **Installation**: `INSTALLATION_GUIDE.md`
- **Architecture**: `industry_architecture.md`, `advanced_components.md`

## Testing

Run comprehensive tests for each phase:

```bash
cd backend

# Week 1 & 2: Multi-modal
python test_multimodal.py

# Week 3: RAG & web search
python test_rag.py

# Week 4: Auth & personalization
python test_week4.py

# All endpoints
python test_all_endpoints.py
```

