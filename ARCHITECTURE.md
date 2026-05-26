# Architecture

This document describes the high-level architecture of the GeeBOT / Agent AI Chatbot project.

The system is designed as a multi-service AI application focused on:

- streamed AI responses
- Retrieval-Augmented Generation (RAG)
- per-user document isolation
- semantic retrieval with pgvector
- production-style backend separation

---

# High-Level Architecture

```text id="c0n25y"
                    ┌────────────────────┐
                    │   React Frontend   │
                    │   (Vite + Axios)   │
                    └─────────┬──────────┘
                              │
          ┌───────────────────┴───────────────────┐
          │                                       │
          ▼                                       ▼

┌────────────────────┐              ┌────────────────────┐
│     Django API     │              │   FastAPI SSE API  │
│  Auth / CRUD API   │              │  Streaming Service │
└─────────┬──────────┘              └─────────┬──────────┘
          │                                   │
          ▼                                   ▼

┌────────────────────┐              ┌────────────────────┐
│    PostgreSQL      │              │ Haystack Runtime   │
│    App Database    │              │ Planner / Agent    │
└─────────┬──────────┘              │ Retriever / Tools  │
          │                         └─────────┬──────────┘
          │                                   │
          └──────────────┬────────────────────┘
                         ▼

               ┌──────────────────┐
               │ pgvector Storage │
               │ Document Chunks  │
               │ Embeddings       │
               └──────────────────┘
```

---

# Service Responsibilities

## React Frontend

Main responsibilities:

- chat interface
- streaming response rendering
- markdown rendering
- mobile UI
- conversation management
- document sidebar
- auth session bootstrap
- SSE connection management

Important frontend areas:

```text id="hnc5ri"
AuthContext.jsx
ChatBot.jsx
useChatStream.js
apiClient.js
```

---

# Django REST API

Django acts as the primary data/authentication service.

Responsibilities:

- JWT authentication
- refresh tokens
- conversation CRUD
- message persistence
- document upload
- ownership validation
- OpenAPI documentation

Main apps:

```text id="77k8ra"
users/
chat/
```

Important endpoints:

```text id="llm9m0"
/api/v1/conversations/
/api/v1/messages/
/api/v1/upload/
/api/v1/documents/
```

---

# FastAPI Streaming Service

FastAPI handles low-latency streaming responses separately from Django.

Responsibilities:

- SSE streaming
- JWT validation
- stream buffering
- rate limiting
- AI runtime orchestration

Main endpoint:

```text id="s1n0nm"
/chat-stream/
```

Important concepts:

- EventSource streaming
- incremental token rendering
- micro-batching
- keepalive handling
- graceful stream termination

---

# PostgreSQL + pgvector

The project uses PostgreSQL for:

- application data
- conversations
- messages
- uploaded document metadata

pgvector is used for:

- vector embeddings
- semantic similarity search
- retrieval filtering

The system stores:

```text id="bx0tv7"
- embeddings
- chunk metadata
- corpus information
- namespace isolation
- file hashes
```

---

# Haystack Runtime

The Haystack runtime is the core AI/RAG orchestration layer.

Responsibilities:

- retrieval
- query planning
- tool orchestration
- embedding workflows
- prompt construction
- quiz generation/evaluation

Main architecture components:

```text id="c8z4pc"
Planner
Execution Plan
Retriever
Tools
OpenAI Generator
```

---

# RAG Architecture

## Document Ingestion

Uploaded files go through:

```text id="ly6ev6"
upload
→ parsing
→ cleaning
→ chunking
→ embedding generation
→ pgvector storage
```

Supported formats:

```text id="qcyqgm"
PDF
TXT
DOCX
Markdown
```

---

## Retrieval Flow

Current retrieval flow:

```text id="5l1ccz"
User Question
    ↓
Planner Heuristics
    ↓
Retrieval Strategy Selection
    ↓
Embedding Generation
    ↓
pgvector Search
    ↓
Metadata Filtering
    ↓
Top-K Chunks
    ↓
Prompt Injection
    ↓
LLM Response
```

---

# Query Planning

The project uses a heuristic-based planner system.

The planner attempts to classify:

- conceptual questions
- API/component lookup
- troubleshooting
- architecture questions
- quiz generation
- file-targeted retrieval

Example query types:

```text id="qbby3u"
comparison
guide_how_to
architecture_workflow
troubleshooting
component_api
conceptual
```

---

# User Isolation Model

A major design goal was preventing cross-user document leakage.

The retrieval layer uses metadata filters:

```text id="4e8f98"
meta.corpus
meta.namespace
meta.user_id
meta.file_sha256
```

User documents are isolated through:

```text id="hn0ng3"
namespace = user:<id>
```

This filtering is enforced during retrieval.

---

# Streaming Architecture

The system uses Server-Sent Events (SSE).

Flow:

```text id="wru0y5"
Frontend EventSource
    ↓
FastAPI /chat-stream/
    ↓
Haystack Runtime
    ↓
Incremental chunks
    ↓
Frontend streamed rendering
```

Important streaming features:

- buffering
- incremental rendering
- newline normalization
- requestAnimationFrame batching
- graceful cleanup
- completion markers

---

# Security Design

Implemented protections include:

- JWT authentication
- issuer/audience validation
- ownership filtering
- protected endpoints
- upload restrictions
- rate limiting
- markdown sanitization

Known security tradeoffs:

- EventSource query token limitations
- localStorage token storage
- uploaded file trust boundary

---

# Deployment Architecture

## Local Development

Docker Compose services:

```text id="1ebqzg"
frontend
django
fastapi
postgres
```

---

## Production Deployment

Production deployment currently uses:

- nginx reverse proxy
- gunicorn
- uvicorn
- Docker Compose
- Azure VM

nginx proxies:

```text id="h77p31"
/api/
/chat-stream/
```

---

# Testing Strategy

The project intentionally combines:

## Automated Tests

Focused regression/security tests:

- auth
- permissions
- ownership isolation
- streaming auth
- document access

---

## Manual E2E Testing

Manual testing validates:

- streaming UX
- retrieval quality
- markdown rendering
- mobile behavior
- conversation flows
- token/session handling

---

# Current Technical Debt

Known technical debt areas:

- heuristic-heavy retrieval logic
- limited structured logging
- no async background ingestion queue
- page-aware PDF retrieval missing
- no CI/CD yet
- no dedicated worker services yet

---

# Future Architecture Improvements

Planned future improvements:

```text id="9xw6bn"
- background workers
- service separation
- async ingestion
- CI/CD
- structured logging
- page-aware retrieval
- configurable model routing
- lightweight API containers
- separate AI runtime containers
```

---

# Design Philosophy

The project intentionally prioritizes:

- explainable architecture
- real-world RAG experimentation
- ownership/security
- streaming UX
- production-style separation of concerns

The goal was not only to build a chatbot, but to understand where AI/RAG systems fail and how retrieval systems behave in real engineering scenarios.
