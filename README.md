# GeeBOT / Agent AI Chatbot

Production-style AI/RAG chatbot built with Django, FastAPI, React, Haystack v2, PostgreSQL, and pgvector.

The project combines:

- JWT-based authentication
- streamed AI responses via SSE
- document upload and retrieval (RAG)
- per-user document isolation
- pgvector semantic search
- Haystack Agent architecture
- Dockerized local and production environments

The goal of the project was not only to “build a chatbot”, but to explore real-world engineering problems related to Retrieval-Augmented Generation systems, streaming UX, ownership isolation, deployment, and AI system reliability.

---

# Overview

GeeBOT is a multi-service AI assistant architecture where:

- Django owns authentication, persistence, and REST APIs
- FastAPI handles low-latency streaming responses
- PostgreSQL + pgvector stores embeddings
- Haystack v2 powers retrieval and agent workflows
- React renders a streamed chat interface

The application supports:

- real-time streamed chat responses
- document ingestion and semantic retrieval
- quiz generation/evaluation
- conversation history
- multi-user ownership isolation
- markdown/code rendering
- Docker-based deployment

---

# Key Features

## Authentication & Security

- JWT authentication (SimpleJWT)
- refresh token support
- protected REST endpoints
- per-user ownership filtering
- document isolation
- streaming auth validation
- upload size/extension validation

---

## Streaming Chat

- Server-Sent Events (SSE)
- incremental streamed responses
- micro-batching for smoother rendering
- auto-scroll support
- stable markdown rendering
- graceful streaming cleanup

---

## RAG / AI Features

- document upload:
  - PDF
  - TXT
  - DOCX
  - Markdown

- Haystack v2 Agent architecture

- pgvector semantic retrieval

- metadata-based filtering

- per-user retrieval isolation

- quiz generation/evaluation

- file-targeted retrieval

- heuristic query planning

---

## UI / UX

- responsive mobile layout
- streamed markdown rendering
- code block rendering
- conversation sidebar
- document sidebar
- chat history
- long-response stability

---

# Tech Stack

## Frontend

- React
- Vite
- Axios
- EventSource (SSE)
- Markdown rendering

## Backend

### Django REST Framework

- authentication
- conversations/messages API
- document upload
- ownership validation

### FastAPI

- SSE streaming endpoint
- JWT validation
- rate limiting
- streaming orchestration

---

## AI / Retrieval

- Haystack v2
- OpenAI
- SentenceTransformers
- pgvector
- PostgreSQL

---

## Infrastructure

- Docker Compose
- nginx
- Azure VM deployment
- PostgreSQL 16
- pgvector extension

---

# Architecture

```text
React Frontend
    ↓
Django REST API
    ├── Auth
    ├── Conversations
    ├── Documents
    └── Messages

React Frontend
    ↓
FastAPI SSE Endpoint
    ↓
Haystack Agent Runtime
    ├── Planner
    ├── Retriever
    ├── Tools
    └── OpenAI Generator

PostgreSQL + pgvector
    └── Vector storage
```

---

# RAG Pipeline

Current retrieval flow:

```text
User Question
    ↓
Planner / Query Heuristics
    ↓
Embedding Generation
    ↓
pgvector Retrieval
    ↓
Metadata Filtering
    ↓
Top-K Chunks
    ↓
LLM Response Generation
```

The project intentionally explores real-world RAG challenges such as:

- chunking strategy
- retrieval ranking
- semantic mismatch
- metadata filtering
- multilingual retrieval
- page structure loss
- exact lookup vs semantic retrieval
- full-document summarization limitations
- retrieval grounding

---

# Security & Ownership

The system implements:

- user-scoped conversations
- user-scoped document retrieval
- ownership validation in all major endpoints
- JWT issuer/audience validation
- rate limiting
- markdown HTML sanitization
- removal of unsafe raw HTML rendering

---

# Automated Tests

Focused regression/security tests were added for:

- conversation ownership isolation
- message ownership isolation
- rename permissions
- authenticated access validation
- document access isolation
- upload authentication
- streaming auth validation

Current test suite:

```text
12 passing tests
```

The project intentionally uses:

- targeted automated regression tests
- manual end-to-end testing

instead of excessive mocked unit tests.

---

# Manual Testing

Manual E2E test reports cover:

- streaming stability
- auto-scroll behavior
- markdown rendering
- retrieval quality
- multilingual retrieval
- conversation flow
- authentication/session handling
- mobile layout behavior

Test reports are available under:

```text
docs/
```

---

# Deployment

The application supports:

## Local Development

- Docker Compose
- hot reload frontend/backend
- PostgreSQL + pgvector
- local SSE streaming

## Production Deployment

- nginx reverse proxy
- gunicorn
- uvicorn
- Docker Compose production setup
- Azure VM deployment

---

# Known Limitations

Current known tradeoffs/limitations:

- retrieval heuristics are complex and still evolving
- semantic retrieval is stronger than exact page lookup
- full-book summarization requires dedicated pipelines
- EventSource auth has browser limitations
- ingestion/indexing is asynchronous
- no background worker queue yet
- no production-grade structured logging yet

---

# What I Learned

This project became a practical exploration of production AI/RAG engineering.

Key lessons included:

- retrieval quality matters more than the LLM itself
- chunking and metadata design are critical
- RAG systems fail in subtle ways
- semantic retrieval differs from exact lookup
- ownership/security in AI systems is important
- streaming UX requires careful buffering/state handling
- AI systems need both manual and automated testing

---

# Future Improvements

Planned future improvements:

- background ingestion workers
- structured logging
- healthchecks
- CI/CD
- async ingestion pipeline
- improved retrieval ranking
- page-aware PDF retrieval
- configurable model routing
- service separation between lightweight APIs and heavy AI runtime

---

# Local Development

## Start development environment

```bash
docker compose up --build
```

## Run backend tests

```bash
docker compose exec django pytest
```

---

# Interview Pitch

> “I built a multi-service AI assistant where Django owns auth/data, FastAPI owns low-latency streaming, pgvector stores embeddings, Haystack handles retrieval/tools, and React renders a streamed chat UX.”

# Documentation

Additional technical documentation:

- [Architecture Overview](ARCHITECTURE.md)
- [Manual Test Reports](docs/)
