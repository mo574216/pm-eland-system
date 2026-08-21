# Current Project Status

**File:** `12_CURRENT_STATUS.md`  
**Status:** Informational / Operational  
**System:** Metadata-Driven Enterprise Architecture Management Platform  
**Version:** 1.0  
**Audience:** Project owner, AI coding agents, architects, developers, QA, security reviewers

---

# 1. Purpose

This document provides the current operational state of the project.

It is intended to answer:

- What has already been defined?
- What is implementation-ready?
- What remains undecided?
- What should agents build next?
- Which assumptions are provisional?
- What must not be silently invented?

This file is informational.

It SHALL NOT override normative documents such as:

```text
01_ARCHITECTURE_RULES.md
02_SYSTEM_REQUIREMENTS.md
03_DATABASE_SPECIFICATION.md
04_API_SPECIFICATION.md
05_BACKEND_SPECIFICATION.md
06_FRONTEND_SPECIFICATION.md
09_TEST_SPECIFICATION.md
11_SECURITY_SPECIFICATION.md
```

---

# 2. Project Summary

The platform is a:

> **Metadata-driven enterprise architecture and project knowledge platform with configurable hierarchy, dynamic structured forms, document versioning, safe Excel/CSV import, phase locking, review, reporting, and audit.**

The system is intentionally domain-agnostic.

Examples such as:

```text
Business Service
Business Process
Application
Technology Component
Stakeholder
Risk
```

are user-configured metadata and SHALL NOT be implemented as fixed domain models.

---

# 3. Architecture Status

Current state:

```text
Architecture Vision               COMPLETE
Architecture Rules                COMPLETE
System Requirements               COMPLETE
Database Specification            COMPLETE
API Specification                 COMPLETE
Backend Specification             COMPLETE
Frontend Specification            COMPLETE
AI Agent Operating Model          COMPLETE
Task Backlog                      COMPLETE
Test Specification                COMPLETE
Deployment Guide                  COMPLETE
Security Specification            COMPLETE
Current Status                    COMPLETE
```

Overall architecture status:

```text
IMPLEMENTATION-READY WITH DOCUMENTED OPEN DECISIONS
```

---

# 4. Completed Specification Package

The following implementation-grade files currently exist:

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

---

# 5. Recommended Additional Contract Files

The following machine-readable or architectural artifacts SHOULD be added before or during early implementation:

```text
contracts/openapi.yaml
contracts/error-codes.yaml
contracts/permissions.yaml
ADR/README.md
ADR/ADR-0001-metadata-driven-domain-model.md
README.md
```

These are not yet considered complete unless explicitly generated later.

---

# 6. Core Architecture Decisions Already Approved

The following decisions SHALL be treated as established unless superseded by ADR.

## 6.1 Metadata-Driven Domain Model

User-configurable enterprise concepts are stored as metadata and generic entity objects.

No domain-specific tables.

---

## 6.2 Generic Hierarchy

Hierarchy depth is arbitrary.

Primary MVP representation:

```text
entity_objects.parent_id
```

with recursive PostgreSQL CTEs.

---

## 6.3 Generic Relationships

Cross-links use:

```text
relationship_types
entity_relationships
```

---

## 6.4 Dynamic Forms

Forms are metadata-driven.

Frontend SHALL use generic renderers.

---

## 6.5 Structured Data

Canonical MVP entity dynamic properties are preferably stored in:

```text
entity_objects.attributes JSONB
```

with metadata definitions controlling valid keys/types.

The optional normalized `entity_attribute_values` model SHALL NOT be used simultaneously as a second source of truth.

---

## 6.6 Document Storage

Document binaries live in private S3-compatible object storage.

PostgreSQL stores metadata.

Document versions are append-only.

---

## 6.7 Import Safety

Every import follows:

```text
upload
→ analyze
→ map
→ validate
→ dry run
→ conflict review
→ explicit resolution
→ transactional commit
```

Silent overwrite is prohibited.

---

## 6.8 Phase Locking

Phase lock is enforced server-side.

Frontend lock state is UX only.

---

## 6.9 Audit

Material mutations produce immutable audit records.

---

## 6.10 API

Public API base path:

```text
/api/v1
```

Standard JSON envelope is defined in `04_API_SPECIFICATION.md`.

---

# 7. Current Technology Baseline

Backend:

```text
Python 3.12+
FastAPI
SQLAlchemy 2.x
Pydantic v2
Alembic
PostgreSQL 16+
Pytest
```

Frontend:

```text
React 19+
TypeScript 5+
Vite
Material UI
TanStack Query
Redux Toolkit
React Hook Form
Zod
Vitest
React Testing Library
Playwright
i18next / react-i18next
MUI Persian locale and RTL Emotion pipeline
Vazirmatn font
```

Infrastructure:

```text
Docker
Docker Compose
MinIO/S3-compatible storage
Redis
background worker
```

Kubernetes is deferred until justified.

---

# 8. MVP Scope

MVP includes:

```text
authentication
RBAC
workspace isolation
workspace membership
metadata entity types
dynamic attributes
generic entities
arbitrary hierarchy
generic relationships
dynamic forms
repeating tables
parent-prefilled values
documents
document versioning
basic preview
XLSX/CSV import
mapping
dry run
conflict handling
MERGE/REPLACE/SKIP
phase locking
basic dashboard
audit
Persian (`fa-IR`) user interface
global RTL layout
```

---

# 9. Deferred Scope

The following are not MVP blockers:

```text
enterprise SSO
advanced workflow engine
full BPMN semantic editor
Visual Paradigm semantic parsing
knowledge graph database
semantic search
AI document extraction
AI assistant
real-time collaboration
chat
budgeting
resource allocation
timesheets
mobile-native application
```

---

# 10. Known Open Decisions

The following decisions remain open and SHALL NOT be silently invented by coding agents.

# OD-001 — Authentication Session Strategy

Need final choice between:

```text
short-lived bearer token + secure refresh
or
secure HTTP-only cookie session/token model
```

Security specification defines acceptable constraints, but final implementation choice should be recorded in ADR.

---

# OD-002 — Dynamic Attribute Physical Storage

Preferred MVP:

```text
entity_objects.attributes JSONB
```

Optional alternative:

```text
entity_attribute_values
```

Current recommendation:

**Use JSONB for MVP.**

If implementation chooses otherwise, ADR required.

---

# OD-003 — Role Scope Model

Current design includes:

```text
global roles
workspace membership role
```

Still to clarify whether future permissions require:

```text
entity-level ACL
field-level ACL
```

MVP SHOULD not introduce these unless needed.

---

# OD-004 — Parent-Child Type Constraints

Current hierarchy is generic.

Open question:

Should administrators be able to configure allowed parent-child type combinations?

Example:

```text
Business Service may contain Business Process
```

Recommended:

P1 metadata feature, not required for initial generic hierarchy.

---

# OD-005 — Form Rule Representation

Need exact JSON rule schema for:

```text
visibility
required-if
inheritance
read-only conditions
```

This should be defined before implementing advanced conditional logic.

---

# OD-006 — Repeating Table Storage

MVP recommendation:

```text
nested JSON in form_instances.values_json
```

If row-level analytics become a major requirement, normalized storage may be introduced later through ADR.

---

# OD-007 — Review Workflow Depth

Current P1 review includes:

```text
comments
revision requested
resubmission
```

Open question:

Whether to add formal multi-stage approval workflow.

Not required for MVP.

---

# OD-008 — Document Office Preview Stack

Candidate:

```text
LibreOffice headless conversion to PDF
```

Need final worker/container decision.

---

# OD-009 — Malware Scanner

Recommended production P1:

```text
ClamAV
```

Final deployment integration is not yet locked.

---

# OD-010 — Search Engine

MVP:

```text
PostgreSQL search
```

OpenSearch/Elasticsearch is deferred until demonstrated need.

---

# OD-011 — Reporting Query Builder Complexity

MVP:

```text
basic server-defined KPI queries
```

P1:

metadata-driven safe query builder.

Arbitrary SQL remains prohibited.

---

# OD-012 — Multi-Tenant SaaS

Current workspace model provides logical isolation.

The project has not committed to a public multi-tenant SaaS architecture.

No billing, subscription, tenant billing, or SaaS admin model SHALL be invented.

---

# OD-013 — RPO / RTO

Illustrative deployment values:

```text
RPO 1 hour
RTO 4 hours
```

These are examples, not approved business requirements.

---

# OD-014 — AI Provider

No runtime AI provider is approved yet.

Agents SHALL NOT introduce:

```text
OpenAI
Gemini
Claude
local LLM
```

as a production dependency without an AI ADR.

---

# OD-015 — Persian Calendar and Numeral Display Policy

Persian (`fa-IR`) localization and RTL are approved and mandatory. The remaining
product decision is whether user-facing dates use the Persian (Jalali) or
Gregorian calendar and whether displayed numbers use Persian or Latin digits.

API timestamps remain ISO 8601 and numeric values remain JSON numbers regardless
of this decision. Coding agents SHALL use centralized formatters and SHALL NOT
choose a calendar or digit policy inside individual components.

This decision does not block the current foundation or identity schema. It SHALL
be resolved before date- or number-intensive end-user workflows are completed.

---

# 11. Architecture Risks to Monitor

## RISK-001 — Generic Model Becoming Too Loose

Mitigation:

- metadata validation,
- stable schema contracts,
- explicit indexes,
- controlled JSONB use.

---

## RISK-002 — JSONB Reporting Performance

Mitigation:

- GIN indexes,
- targeted generated indexes if needed,
- normalized extension via ADR only when justified.

---

## RISK-003 — Dynamic Form Complexity

Mitigation:

- normalized render contract,
- restricted deterministic rule syntax,
- no arbitrary code execution.

---

## RISK-004 — Import Complexity

Mitigation:

- staged pipeline,
- explicit matching strategies,
- mandatory dry run,
- transaction safety,
- extensive tests.

---

## RISK-005 — Permission Drift

Mitigation:

- centralized AuthorizationService,
- workspace policy,
- contract-level permission catalog.

---

## RISK-006 — Agent Architecture Drift

Mitigation:

- architecture rules,
- agent role boundaries,
- task IDs,
- ADR requirement,
- completion reports.

---

# 12. Current Milestone Status

```text
M0 Repository/Foundation        IN PROGRESS (FND-001 through FND-005 and FND-007 COMPLETE)
M1 Identity/Workspace           NOT STARTED
M2 Metadata/Entity Platform     NOT STARTED
M3 Dynamic Forms                NOT STARTED
M4 Documents/Import             NOT STARTED
M5 Workflow/Reporting           NOT STARTED
M6 Production Hardening         NOT STARTED
M7 AI Enhancements              DEFERRED
```

Architecture/documentation phase:

```text
COMPLETE
```

Latest implementation entry:

```text
DATE:
2026-08-22

MILESTONE:
M0 Repository and Engineering Foundation

TASKS_COMPLETED:
FND-001 Initialize Monorepo
FND-002 Initialize Backend Application
FND-003 Initialize Frontend Application
FND-004 PostgreSQL and Alembic Setup
FND-005 Local Docker Compose
FND-007 Persian-First RTL Foundation

TASKS_IN_PROGRESS:
FND-006 CI Baseline (implementation and local validation complete;
first hosted run failed on a Linux mypy portability issue; fix validated locally;
updated hosted run and branch protection pending)

BLOCKERS:
The Linux CI portability fix must be committed and pushed before GitHub can
execute the corrected workflow. The Persian/RTL E2E job is already active and
passed on the hosted runner.
The main branch currently has no protection rule; an administrator must require
the `Required CI Gate` status check to enforce merge blocking.

The first hosted FND-006 run failed because mypy resolved a Windows-only asyncio
symbol while checking on Linux. The test now uses a runtime capability lookup;
the exact Linux CI quality and test commands pass locally.

The in-app browser was unavailable during FND-007 verification; the repository's
Playwright suite passed in the matching official Chromium test container.

OD-015 must be resolved before date- or number-intensive UI is completed.

NEW_DECISIONS:
Use the specified React + TypeScript + Vite frontend architecture.
Use async SQLAlchemy 2.x with psycopg 3, request/job-scoped sessions,
service-owned transactions, and synchronous Alembic migrations.
Use a health-gated local Compose topology with loopback-only host ports,
externalized credentials, automatic migrations, and persistent named volumes.
Use separate least-privilege CI jobs with immutable action pins and one
aggregate required status check.
Use Persian (`fa-IR`) as the mandatory end-user language with a global RTL
layout, an i18n resource boundary, and English developer-facing contracts.
Normalize Persian search comparison values without altering canonical display text.

ADR_CREATED:
ADR-0002 Async SQLAlchemy Session Model
ADR-0003 Persian-First Localization Boundary

NEXT_TASK:
Activate and verify FND-006 on GitHub, then begin AUTH-DB-001 Identity Schema.
Resolve OD-015 before implementing date- or number-intensive frontend workflows.
```

---

# 13. Recommended Immediate Implementation Sequence

Start with:

```text
FND-001 Initialize Monorepo
FND-002 Initialize Backend
FND-003 Initialize Frontend
FND-004 PostgreSQL/Alembic
FND-005 Docker Compose
FND-006 CI Baseline
FND-007 Persian-First RTL Foundation
```

Then:

```text
AUTH
→ WORKSPACE
→ METADATA
→ ENTITY
→ HIERARCHY
```

Only after those foundations should dynamic forms, documents, and import be built.

---

# 14. First Recommended Agent Task

```text
TASK_ID: FND-001
TITLE: Initialize Monorepo
```

Owner:

```text
DevOps Agent
```

Expected output:

```text
backend/
frontend/
infrastructure/
contracts/
ADR/
ai-context/
README.md
```

No business functionality should be implemented in this task.

---

# 15. Second Recommended Agent Task

```text
TASK_ID: FND-002
TITLE: Initialize Backend Application
```

Owner:

```text
Backend Agent
```

Dependencies:

```text
FND-001
```

Expected:

```text
FastAPI startup
config
logging
request ID
health endpoints
/api/v1 router
```

---

# 16. Third Recommended Agent Task

```text
TASK_ID: FND-003
TITLE: Initialize Frontend Application
```

Owner:

```text
Frontend Agent
```

Dependencies:

```text
FND-001
```

Expected:

```text
React/Vite
TypeScript strict
MUI
TanStack Query
Redux Toolkit
routing
basic shell
```

FND-002 and FND-003 can run in parallel after repository structure is fixed.

---

# 17. Coding Agent Entry Instructions

Before any agent starts implementation, it SHALL:

1. read `00_PROJECT_CONTEXT.md`,
2. read `01_ARCHITECTURE_RULES.md`,
3. read this file,
4. read task-relevant specifications,
5. inspect repository state,
6. produce pre-implementation report.

---

# 18. Agent Assumption Rule

If an implementation detail is not specified:

Agents SHALL classify it as one of:

```text
LOW-RISK IMPLEMENTATION DETAIL
OPEN ARCHITECTURE DECISION
OPEN PRODUCT DECISION
SECURITY-SENSITIVE DECISION
```

Only low-risk implementation details may be selected autonomously.

Examples of low-risk details:

```text
helper function naming
test fixture organization
internal file splitting
```

Examples requiring escalation/ADR:

```text
changing auth model
new database
new domain table
new public API semantics
different canonical storage model
```

---

# 19. Documentation Update Rule

After implementation starts, this file SHOULD be updated whenever:

- milestone changes,
- major task completes,
- new blocker discovered,
- ADR approved,
- open decision resolved,
- architecture risk changes.

---

# 20. Status Entry Template

Use:

```text
DATE:
MILESTONE:
TASKS_COMPLETED:
TASKS_IN_PROGRESS:
BLOCKERS:
NEW_DECISIONS:
ADR_CREATED:
NEXT_TASK:
```

---

# 21. Example Future Status Entry

```text
DATE:
2026-09-01

MILESTONE:
M0

TASKS_COMPLETED:
FND-001
FND-002
FND-003

TASKS_IN_PROGRESS:
FND-004
FND-005

BLOCKERS:
None

NEW_DECISIONS:
Use async SQLAlchemy + psycopg3

ADR_CREATED:
ADR-0002-backend-db-session-model.md

NEXT_TASK:
AUTH-DB-001
```

---

# 22. Definition of Implementation Readiness

The project is considered implementation-ready because:

- [x] architecture rules exist,
- [x] system requirements exist,
- [x] database design exists,
- [x] API contract exists,
- [x] backend architecture exists,
- [x] frontend architecture exists,
- [x] agent roles exist,
- [x] executable backlog exists,
- [x] test specification exists,
- [x] deployment guidance exists,
- [x] security specification exists.

Remaining open decisions do not block foundation implementation.

---

# 23. Definition of MVP Readiness for Production

MVP SHALL NOT be considered production-ready until:

- [ ] all P0 backlog tasks complete,
- [ ] QA E2E scenario passes,
- [ ] workspace isolation verified,
- [ ] phase locking verified,
- [ ] import rollback/idempotency verified,
- [ ] document versioning verified,
- [ ] audit verified,
- [ ] security review completed,
- [ ] no unresolved critical/high security defect,
- [ ] deployment pipeline operational,
- [ ] backups configured,
- [ ] restore tested.

---

# 24. Architectural Reminder

All AI agents SHALL preserve the following invariant:

> **The platform is metadata-driven. Domain concepts are data, not code.**

A request such as:

```text
"Add Business Process support"
```

should normally mean:

```text
create/configure an entity type and metadata
```

not:

```text
create BusinessProcess model/table/page
```

---

# 25. Current Project State Summary

```text
Product concept:       STABLE
Architecture:          STABLE
MVP requirements:      DEFINED
Database contract:     DEFINED
API contract:          DEFINED
Backend architecture:  DEFINED
Frontend architecture: DEFINED
Agent workflow:        DEFINED
Testing strategy:      DEFINED
Deployment strategy:   DEFINED
Security strategy:     DEFINED
Implementation code:   IN PROGRESS (FND-001, FND-002, FND-003 COMPLETE)
Runtime AI features:   DEFERRED
```

---

# 26. Next Documentation Enhancements

Recommended next documentation artifacts:

```text
contracts/openapi.yaml
contracts/error-codes.yaml
contracts/permissions.yaml
ADR/ADR-0001-metadata-driven-domain-model.md
README.md
```

After these, implementation should begin rather than continuing architecture documentation indefinitely.

---

# 27. Related Specifications

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
```
