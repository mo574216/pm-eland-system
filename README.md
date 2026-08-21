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
00_PROJECT_CONTEXT.md
01_ARCHITECTURE_RULES.md
02_SYSTEM_REQUIREMENTS.md
03_DATABASE_SPECIFICATION.md
04_API_SPECIFICATION.md
05_BACKEND_SPECIFICATION.md
06_FRONTEND_SPECIFICATION.md
07_AI_AGENT_ROLES.md
08_TASK_BACKLOG.md
09_TEST_SPECIFICATION.md
10_DEPLOYMENT_GUIDE.md
11_SECURITY_SPECIFICATION.md
12_CURRENT_STATUS.md
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

The first accepted decision is:

```text
ADR-0001-metadata-driven-domain-model.md
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
08_TASK_BACKLOG.md
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
00_PROJECT_CONTEXT.md
01_ARCHITECTURE_RULES.md
07_AI_AGENT_ROLES.md
12_CURRENT_STATUS.md
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
NOT STARTED
```

See:

```text
12_CURRENT_STATUS.md
```
