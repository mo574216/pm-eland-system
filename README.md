# Metadata-Driven Enterprise Architecture Management Platform

This repository contains the architecture and implementation contract for a configurable enterprise architecture and project knowledge platform.

## Core Principle

> **Domain concepts are data, not code.**

The system is designed so administrators can configure:

```text
entity types
attributes
hierarchies
relationships
forms
imports
phases
dashboards
```

without introducing domain-specific database tables or frontend pages.

---

## Documentation Package

Read in this order:

```text
ai_context/00_PROJECT_CONTEXT.md
ai_context/01_ARCHITECTURE_RULES.md
ai_context/02_SYSTEM_REQUIREMENTS.md
ai_context/03_DATABASE_SPECIFICATION.md
ai_context/04_API_SPECIFICATION.md
ai_context/05_BACKEND_SPECIFICATION.md
ai_context/06_FRONTEND_SPECIFICATION.md
ai_context/07_AI_AGENT_ROLES.md
ai_context/08_TASK_BACKLOG.md
ai_context/09_TEST_SPECIFICATION.md
ai_context/10_DEPLOYMENT_GUIDE.md
ai_context/11_SECURITY_SPECIFICATION.md
ai_context/12_CURRENT_STATUS.md
ai_context/13_IMPLEMENTATION_ROADMAP.md
```

Then read:

```text
contracts/
ADR/
```

---

## Machine-Readable Contracts

```text
contracts/openapi.yaml
contracts/error-codes.yaml
contracts/permissions.yaml
```

These files define shared integration boundaries.

---

## Architecture Decisions

Architecture Decision Records live in:

```text
ADR/
```

Accepted decisions include:

```text
ADR-0001-metadata-driven-domain-model.md
ADR-0002-async-sqlalchemy-session-model.md
```

---

## Recommended Technology

Backend:

```text
Python 3.12+
FastAPI
SQLAlchemy 2.x
Pydantic v2
Alembic
PostgreSQL 16+
```

Frontend:

```text
React
TypeScript
Vite
Material UI
TanStack Query
Redux Toolkit
React Hook Form
Zod
```

Infrastructure:

```text
Docker
Docker Compose
MinIO/S3-compatible storage
Redis
background workers
```

---

## Implementation Start

The implementation backlog is defined in:

```text
ai_context/08_TASK_BACKLOG.md
```

Start with:

```text
FND-001
FND-002
FND-003
FND-004
FND-005
FND-006
```

Then proceed through:

```text
AUTH
WORKSPACE
METADATA
ENTITY
HIERARCHY
FORMS
DOCUMENTS
IMPORT
PHASE
DASHBOARD
SECURITY/QA
```

---

## AI Coding Agents

Before coding, every AI agent SHALL read:

```text
ai_context/00_PROJECT_CONTEXT.md
ai_context/01_ARCHITECTURE_RULES.md
ai_context/07_AI_AGENT_ROLES.md
ai_context/12_CURRENT_STATUS.md
```

plus task-specific specifications.

Agents SHALL not silently change architecture.

---

## MVP Definition

The MVP includes:

```text
authentication
workspace isolation
metadata-defined entities
arbitrary hierarchy
generic relationships
dynamic forms
repeating tables
parent inheritance
document versioning
XLSX/CSV import
dry-run conflict resolution
phase locking
basic dashboards
audit logging
```

---

## Deferred

Not required for MVP:

```text
runtime AI
semantic search
enterprise SSO
knowledge graph database
full BPMN semantic editor
real-time collaboration
budgeting
resource scheduling
```

---

## Current Status

Architecture/documentation:

```text
COMPLETE
```

Implementation:

```text
IN PROGRESS - FND-001 through FND-005 complete
```

See:

```text
ai_context/12_CURRENT_STATUS.md
```

---

## Repository Structure

```text
backend/          FastAPI application
frontend/         React + TypeScript + Vite application
infrastructure/   Docker Compose local-development environment
contracts/        OpenAPI, error-code, and permission contracts
ADR/              Architecture Decision Records
ai_context/       Normative specifications and current status
```

## Frontend Quick Start

Requirements:

```text
Node.js 24+
npm 11+
```

From a clean clone:

```bash
cd frontend
npm ci
npm run typecheck
npm test
npm run build
npm run dev
```

The development server is available at `http://localhost:5173`. Copy `.env.example` to `.env` only when local configuration overrides are needed; never commit the resulting file or real credentials.

## Backend Quick Start

Requirements:

```text
Python 3.12+
uv
```

From a clean clone:

```bash
cd backend
uv sync --all-groups
uv run ruff format --check .
uv run ruff check .
uv run mypy app tests
uv run pytest
uv run uvicorn app.main:app --reload
```

The backend is available at `http://localhost:8000`, with health endpoints at `/health/live` and `/health/ready` and interactive API documentation at `/docs` in development.
