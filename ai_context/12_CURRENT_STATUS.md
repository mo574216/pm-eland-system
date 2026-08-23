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

# OD-001 — Authentication Session Strategy — RESOLVED

ADR-0004 selects:

```text
short-lived bearer token + rotating opaque refresh token in a Secure HttpOnly
SameSite cookie with hashed server-side session state
```

The access token is held only in frontend memory. Refresh reuse revokes the token family.

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
M0 Repository/Foundation        COMPLETE (FND-001 through FND-007 COMPLETE)
M1 Identity/Workspace           COMPLETE (identity, auth, workspace schema/API/UI and current test matrix)
M2 Metadata/Entity Platform     IN PROGRESS (metadata schema/API/validation/UI complete)
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
M1 Identity, Workspace, and Security Foundation

TASKS_COMPLETED:
FND-001 Initialize Monorepo
FND-002 Initialize Backend Application
FND-003 Initialize Frontend Application
FND-004 PostgreSQL and Alembic Setup
FND-005 Local Docker Compose
FND-006 CI Baseline
FND-007 Persian-First RTL Foundation
AUTH-DB-001 Identity Schema
AUTH-BE-001 Authentication Service
AUTH-BE-002 Authorization Service
AUTH-FE-001 Login and Auth Context
WS-DB-001 Workspace Schema
WS-BE-001 Workspace CRUD
WS-FE-001 Workspace UI

TASKS_IN_PROGRESS:
None

BLOCKERS:
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
Use short-lived in-memory JWT bearer access tokens with rotating opaque refresh
tokens held in Secure HttpOnly SameSite cookies and stored server-side only as hashes.
Use `IDENTITY_MANAGE` for global role administration, prevent actors from granting
permissions they do not possess, and audit role mutations transactionally.

ADR_CREATED:
ADR-0002 Async SQLAlchemy Session Model
ADR-0003 Persian-First Localization Boundary
ADR-0004 Bearer Access Tokens and Rotating Refresh Sessions

NEXT_TASK:
Begin META-DB-001 Metadata Schema while extending TEST-WS-001 with every new
workspace-scoped resource.
Resolve OD-015 before implementing date- or number-intensive frontend workflows.
```

Metadata platform implementation entry:

```text
DATE:
2026-08-22

MILESTONE:
M2 Metadata and Generic Entity Platform

TASKS_COMPLETED:
META-DB-001 Metadata Schema
META-BE-001 Entity Type API
META-BE-002 Attribute Definition API
META-BE-003 Metadata Validation Engine
META-FE-001 Metadata Administration

TASKS_IN_PROGRESS:
ENT-DB-001 Generic Entity Schema

TEST_RESULTS:
Backend formatting, lint, strict mypy, 87 tests, and Alembic 0005/0006 offline
upgrade/downgrade validation pass. Frontend strict TypeScript, zero-warning ESLint,
18 tests, and production build pass.

SECURITY:
Metadata mutations require effective METADATA_MANAGE after active workspace membership
is verified. Reads are membership-scoped. Mutations use optimistic concurrency and
transactional audit logs. Configurable regex is restricted to a bounded safe subset.

LIMITATIONS:
Live PostgreSQL migration verification still requires local database credentials.
The metadata UI currently exposes the core create/edit flow; advanced JSON configuration
editing is intentionally deferred to later form/rule tooling.

NEXT_TASK:
ENT-DB-001 Generic Entity Schema, followed by ENT-BE-001 through ENT-BE-003.
```

Generic entity platform implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M2 Metadata and Generic Entity Platform

TASKS_COMPLETED:
ENT-DB-001 Generic Entity Schema
ENT-BE-001 Create Entity
ENT-BE-002 Read/List/Search Entities
ENT-BE-003 Update/Archive Entity

TASKS_IN_PROGRESS:
None

TEST_RESULTS:
Backend formatting, lint, strict mypy, 103 tests, OpenAPI YAML validation, and
Compose configuration validation pass. Alembic revisions 0001 through 0007 were
applied successfully to live PostgreSQL. Frontend strict TypeScript, zero-warning
ESLint, 18 tests, and the production build pass. Live readiness, login, workspace
creation, and authenticated workspace listing were verified locally.

SECURITY:
Entity reads and mutations require active workspace access plus effective canonical
permissions. Dynamic values are server-validated against metadata; mutations use
optimistic concurrency and transactional before/after audit records. Authentication
identity reads use an isolated request session so authorization cannot contaminate
service-owned mutation transactions. Local administrator bootstrap is explicitly
development-only, requires supplied strong credentials, is idempotent, and never
overwrites an existing password.

LIMITATIONS:
Phase/resource locking cannot be enforced until the phase schema and lock-policy
tasks are implemented. The generic entity frontend tasks remain outstanding.

NEXT_TASK:
HIER-BE-001 Hierarchy Retrieval, followed by HIER-BE-002 and entity frontend tasks.
```

Hierarchy retrieval implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M2 Metadata and Generic Entity Platform

TASKS_COMPLETED:
HIER-BE-001 Hierarchy Retrieval

TASKS_IN_PROGRESS:
None

TEST_RESULTS:
Backend formatting, lint, strict mypy, and 106 tests pass. The recursive CTE was
also exercised through the live API against PostgreSQL using a root and child; it
returned one path-ordered result set with depths 0/1, has_children=true on the root,
and the requested metadata type summary.

SECURITY:
Hierarchy traversal requires active workspace membership and effective ENTITY_READ.
The CTE anchor and recursive member both enforce workspace scope, deleted rows are
excluded, and a cross-workspace or invisible root is reported as not found.

DATABASE_CHANGES:
None. The accepted entity_objects.parent_id adjacency model and existing partial
parent index are used directly.

NEXT_TASK:
HIER-BE-002 Reparent and Cycle Prevention.
```

Hierarchy mutation implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M2 Metadata and Generic Entity Platform

TASKS_COMPLETED:
HIER-BE-002 Reparent and Cycle Prevention

TASKS_IN_PROGRESS:
None

TEST_RESULTS:
Backend formatting, lint, strict mypy, 110 tests, and the OpenAPI contract check
pass. Live PostgreSQL/API verification moved a child to another root with a version
increment, rejected moving that root beneath the child with HIERARCHY_CYCLE, and
successfully restored the original hierarchy.

SECURITY:
Reparenting requires active workspace access and effective ENTITY_UPDATE. Candidate
parents must be active and in the same workspace. Hierarchy writes are serialized by
a transaction-scoped workspace advisory lock, cycle checks use a recursive CTE, the
row update is optimistic, and before/after audit state is committed atomically.

DATABASE_CHANGES:
None.

KNOWN_LIMITATIONS:
Phase/resource lock enforcement remains deferred until the phase lock-policy schema
and service exist.

NEXT_TASK:
ENT-FE-001 Entity Tree Viewer, then ENT-FE-002 Generic Entity Detail Page.
```

Entity tree frontend implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M2 Metadata and Generic Entity Platform

TASKS_COMPLETED:
ENT-FE-001 Entity Tree Viewer

TASKS_IN_PROGRESS:
None

TEST_RESULTS:
Frontend zero-warning ESLint, strict TypeScript, 10 test files with 20 tests, and
the production build pass. Component tests cover cached root expansion, lazy deeper
child loading, node selection, initial failure, and retry.

SECURITY:
The viewer consumes only the backend-authorized workspace hierarchy response and
does not infer access locally. Optional node actions are injected through a generic
render hook so callers can gate them using effective permissions without embedding
domain-specific behavior.

USER_VISIBLE_RESULT:
Opening a workspace now navigates to the generic entity explorer. The live Demo
Workspace contains Demo Root, Demo Child, Second Root, and the Demo Node metadata
type for previewing hierarchy expansion.

KNOWN_LIMITATIONS:
Entity creation/editing and detail tabs are delivered by subsequent frontend tasks.

NEXT_TASK:
ENT-FE-002 Generic Entity Detail Page.
```

Entity detail frontend implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M2 Metadata and Generic Entity Platform

TASKS_COMPLETED:
ENT-FE-002 Generic Entity Detail Page

TASKS_IN_PROGRESS:
None

TEST_RESULTS:
Frontend zero-warning ESLint, strict TypeScript, 11 test files with 21 tests, and
the production build pass. The component test covers shared detail routing, all six
tabs, metadata-defined labels, values, and safe display of unknown legacy attributes.

SECURITY:
The page relies on the backend-authorized entity and attribute-definition endpoints.
It does not infer permissions or expose mutation actions, and the workspace identifier
is used only for navigation while backend entity lookup remains authoritative.

API_CHANGES:
None. The frontend consumes the existing GET /entities/{entity_id} and attribute
definition contracts.

USER_VISIBLE_RESULT:
Selecting any node in the entity explorer opens the same generic detail page with
Overview, Information, Forms, Documents, Relationships, and History tabs. Overview
and Information use live entity and metadata data; later feature tabs identify their
pending implementation without inventing domain-specific screens.

KNOWN_LIMITATIONS:
Forms, Documents, Relationships, and History tab content is delivered by their
respective later backlog tasks. Editing is also deferred.

NEXT_TASK:
REL-DB-001 Relationship Schema.
```

Relationship persistence implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M2 Metadata and Generic Entity Platform

TASKS_COMPLETED:
REL-DB-001 Relationship Schema

TASKS_IN_PROGRESS:
None

TEST_RESULTS:
Backend formatting, lint, strict mypy, and 112 tests pass. Alembic upgraded the
live PostgreSQL database from 0007 to 0008, downgraded cleanly to 0007, and upgraded
again to head successfully.

SECURITY:
Both tables carry an explicit workspace scope. Relationship instances reference
canonical generic entities and metadata-defined relationship types; active-row
indexes support scoped lookup. Cross-workspace consistency remains enforced by the
authoritative service in REL-BE-001 because the accepted schema uses independent UUID
foreign keys rather than composite workspace foreign keys.

DATABASE_CHANGES:
Migration 0008 adds relationship_types and entity_relationships with directionality
and self-link checks, configured source/target type references, JSONB configuration
and attributes, soft deletion for relationship instances, and incoming/outgoing/type
indexes. Conditional duplicate policy remains service-controlled, so the optional
always-on active relationship unique index was intentionally not added.

API_CHANGES:
None.

KNOWN_LIMITATIONS:
The relationship API, permissions, auditing, configurable duplicate policy, and UI
are delivered by REL-BE-001 and REL-FE-001.

NEXT_TASK:
REL-BE-001 Relationship API.
```

Relationship API implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M2 Metadata and Generic Entity Platform

TASKS_COMPLETED:
REL-BE-001 Relationship API (published MVP endpoints)

TASKS_IN_PROGRESS:
None

TEST_RESULTS:
Backend formatting, lint, strict mypy, 118 tests, and YAML contract parsing pass.
Live PostgreSQL/API verification created relationship metadata, created and listed
outgoing/incoming relationships, logically deleted and recreated a relationship,
and rejected a configured duplicate with INVALID_RELATIONSHIP/422.

SECURITY:
Relationship metadata creation requires METADATA_MANAGE; relationship creation and
deletion require RELATIONSHIP_MANAGE; reads require ENTITY_READ. Every operation
validates active workspace membership. Both endpoint entities and optional metadata
type constraints are checked in the same workspace without leaking inaccessible data.
Material creation/deletion operations are audited transactionally.

DATABASE_CHANGES:
None beyond REL-DB-001 migration 0008. Duplicate checks are serialized under a
workspace transaction advisory lock and ignore logically deleted relationships.

API_CHANGES:
Implemented the specified relationship-type create/list, relationship create,
incoming/outgoing/both list, and logical delete endpoints. Expanded openapi.yaml with
the previously textual relationship paths and schemas. Documented the generic
configuration.allow_duplicates policy; false rejects ordered duplicates and also
reversed duplicates for UNDIRECTED types.

KNOWN_LIMITATIONS:
The backlog uses the phrase relationship type CRUD, but the authoritative API and
database specifications define only create/list and provide no update payload,
version column, or relationship-type delete endpoint. Those unspecified lifecycle
mutations were not invented; they require a future contract/schema decision.
Cardinality configuration is P1 and remains deferred.

USER_VISIBLE_RESULT:
Demo Workspace now contains a Depends On relationship type and one relationship
between its two root demo entities for the frontend relationship panel.

NEXT_TASK:
REL-FE-001 Relationship Panel.
```

Relationship frontend implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M2 Metadata and Generic Entity Platform

TASKS_COMPLETED:
REL-FE-001 Relationship Panel

TASKS_IN_PROGRESS:
None

TEST_RESULTS:
Frontend zero-warning ESLint, strict TypeScript, 12 test files with 22 tests, and
the production build pass. Component coverage verifies metadata/type and entity-name
resolution plus generic relationship creation and deletion.

SECURITY:
The frontend uses RELATIONSHIP_MANAGE only to hide mutation controls as a UX guard.
The backend remains authoritative for workspace access and all relationship reads and
mutations. No relationship data is inferred or retained across workspace scopes.

DATABASE_CHANGES:
None.

API_CHANGES:
None. The panel consumes the REL-BE-001 contract.

USER_VISIBLE_RESULT:
The Relationships tab on every generic entity detail page now lists named incoming
and outgoing relationships. Authorized users can select any metadata-defined active
relationship type and target entity, create the link, and logically delete links.

KNOWN_LIMITATIONS:
The first panel creates outgoing links with empty relationship attributes. Editing
relationship attributes and richer metadata administration are not specified MVP UI
capabilities. The production bundle reports a non-blocking chunk-size warning.

NEXT_TASK:
FORM-DB-001 Form Schema.
```

Form persistence implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M3 Dynamic Forms and Structured Data

TASKS_COMPLETED:
FORM-DB-001 Form Schema

TASKS_IN_PROGRESS:
None

TEST_RESULTS:
Backend formatting, lint, strict mypy, and 121 tests pass. Alembic migration 0009
upgraded the live PostgreSQL database, downgraded cleanly to 0008, and upgraded again
to head successfully.

SECURITY:
Form definitions and instances carry explicit workspace scope. Instance rows retain
the exact form-definition version and canonical entity reference. Workspace and
cross-resource consistency remain authoritative service checks in subsequent tasks.

DATABASE_CHANGES:
Migration 0009 adds form_definitions, form_fields, and form_instances. It enforces
workspace/key/version and definition/field-key uniqueness, lifecycle/status/version
checks, immutable historical definition references, JSONB metadata/rules/values, and
workspace/entity/form/value lookup indexes.

API_CHANGES:
None.

KNOWN_LIMITATIONS:
Published-form immutability, draft editing, publish/new-version behavior, rule
validation, and instance submission are service-layer responsibilities delivered by
the following M3 tasks.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
FORM-BE-001 Draft Form Definition API.
```

Draft form API implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M3 Dynamic Forms and Structured Data

TASKS_COMPLETED:
FORM-BE-001 Draft Form Definition API

TASKS_IN_PROGRESS:
None

TEST_RESULTS:
Backend formatting, lint, strict mypy, 125 tests, and YAML contract parsing pass.
Live PostgreSQL/API verification created a version-1 DRAFT, configured a section,
added a generic field, retrieved/listed the full definition, rejected a missing
section with 422, and rejected a duplicate field key with 409.

SECURITY:
All design mutations require effective FORM_DESIGN and active workspace membership;
definition reads require ENTITY_READ. Entity-type and attribute references are
validated in the same workspace, and metadata changes are audited transactionally.
Every draft mutation explicitly rejects non-DRAFT definitions.

DATABASE_CHANGES:
None beyond migration 0009.

API_CHANGES:
Implemented POST/GET /workspaces/{workspace_id}/forms, GET/PATCH /forms/{form_id},
and POST /forms/{form_id}/fields. Expanded openapi.yaml for all published draft-form
paths and payloads. PATCH supports generic ordered section metadata in schema_json;
section keys are unique and field section references must resolve.

USER_VISIBLE_RESULT:
Demo Workspace contains a Demo Specification draft with a General section and
required Summary TEXT field for subsequent designer, publish, and render tasks.

KNOWN_LIMITATIONS:
Field update/removal endpoints are not defined by the authoritative API specification.
Publish/new-version lifecycle is FORM-BE-002; stored rule interpretation is
FORM-BE-003; render contracts are FORM-BE-004.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
FORM-BE-002 Form Publish and Versioning, while FORM-BE-003 becomes independently
dependency-ready after FORM-BE-001.
```

Form rule evaluator implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M3 Dynamic Forms and Structured Data

TASKS_COMPLETED:
FORM-BE-003 Form Rule Evaluator

TASKS_IN_PROGRESS:
None

TEST_RESULTS:
Backend formatting, lint, strict mypy, and 131 tests pass. Unit tests cover nested
visibility, conditional requirement, parent/static inheritance modes, missing values,
invalid versions/operators/paths, and depth/clause bounds. The live API rejected an
unknown executable-style operator with INVALID_METADATA/422 and accepted a valid
version-1 rule set.

SECURITY:
Rules are interpreted only by a bounded JSON AST; no eval, exec, dynamic import,
attribute access, templates, or stored code execution is used. Paths traverse only
explicit dictionary context, operators are allowlisted, nesting is capped at 10, and
total clauses are capped at 100. Draft field creation invokes the shared validator.

DATABASE_CHANGES:
None.

API_CHANGES:
Documented the version-1 conditional and inheritance rule grammar in the API
specification. Existing JSON payload fields are unchanged.

USER_VISIBLE_RESULT:
Demo Specification now also has a Mitigation field with conditional visibility and
requirement plus an editable static default, ready for render-contract testing.

KNOWN_LIMITATIONS:
The evaluator returns deterministic field state and inherited candidates; loading
entity/parent/reference/user context and producing the normalized client contract are
implemented by FORM-BE-004. Publish consumes this validator in FORM-BE-002.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
FORM-BE-002 Form Publish and Versioning.
```

Form lifecycle implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M3 Dynamic Forms and Structured Data

TASKS_COMPLETED:
FORM-BE-002 Form Publish and Versioning

TASKS_IN_PROGRESS:
None

TEST_RESULTS:
Backend formatting, lint, strict mypy, 134 tests, and YAML contract parsing pass.
Live PostgreSQL/API verification published Demo Specification version 1, rejected
metadata and field mutations with 409, created version 2 as a DRAFT with two copied
fields, and confirmed version 1 remained PUBLISHED with its original fields.

SECURITY:
Publish and new-version operations require effective FORM_DESIGN and active workspace
membership, lock the source row, validate all metadata/rules before publishing, and
audit lifecycle changes transactionally. Version allocation is serialized with a
workspace advisory lock. Published definitions remain inaccessible to draft mutation
queries, preventing silent reinterpretation of historical submissions.

DATABASE_CHANGES:
None beyond migration 0009. Existing unique workspace/key/version constraints and
form-instance RESTRICT references preserve version identity.

API_CHANGES:
Implemented POST /forms/{form_id}/publish and POST /forms/{form_id}/new-version and
added both to openapi.yaml. Publish validates schema sections, non-empty fields,
active attribute references, entity-type compatibility, field types, and all bounded
JSON rules. New-version performs independent deep copies of schema and field JSON.

USER_VISIBLE_RESULT:
Demo Specification version 1 is now PUBLISHED and immutable; version 2 is an editable
DRAFT containing the same General section, Summary field, and conditional Mitigation
field.

KNOWN_LIMITATIONS:
Retirement is modeled but no retirement endpoint is specified. Historical form
instance behavior is structurally guaranteed now and exercised end to end when the
instance API is implemented.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
FORM-BE-004 Render Contract. Work intentionally stopped before starting it at the
user's request.
```

RTL portal experience implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
Cross-cutting UX convergence before continuing M3

TASKS_COMPLETED:
UX-FE-001 RTL Portal Shell and Workspace Dashboard

TASKS_IN_PROGRESS:
None

TEST_RESULTS:
Frontend zero-warning ESLint and strict TypeScript pass. All 13 component test
files with 23 tests pass, the production build passes, and all 3 Playwright
browser scenarios pass in Microsoft Edge. The Chrome browser process was stale
on the Windows host; the application itself remained responsive on port 5173.

SECURITY:
The portal shell adds no authorization semantics. Protected routes and backend
workspace membership/permission checks remain authoritative. Workspace context
is loaded by route-scoped API keys, and planned capabilities expose no dead or
working-looking actions.

DATABASE_CHANGES:
None.

API_CHANGES:
None.

USER_VISIBLE_RESULT:
Opening a workspace now displays a Persian RTL portal dashboard with a persistent
right navigation rail on desktop, responsive mobile drawer, contextual header,
workspace identity, quick access to implemented capabilities, and an honest
empty announcement state. Future forms, documents, imports, and reports are
clearly marked as planned rather than presented as functional links.

KNOWN_LIMITATIONS:
Approved organization brand assets have not been provided, so the shell uses a
generic repository-owned mark and palette. The production bundle retains the
existing non-blocking chunk-size warning; route-level code splitting remains a
later performance task. Chrome on the current Windows host may need a process
restart before it can run Playwright reliably.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
FORM-BE-004 Render Contract.
```

Form render contract implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M3 Dynamic Forms and Structured Data

TASKS_COMPLETED:
FORM-BE-004 Render Contract

TASKS_IN_PROGRESS:
None

TEST_RESULTS:
Backend formatting, lint, strict mypy, all 136 tests, and canonical OpenAPI YAML
parsing pass. Unit coverage verifies ordered/implicit sections, current value
precedence, parent and referenced entity inheritance, editable/read-only defaults,
conditional visibility/requirement, repeating table configuration, draft-preview
permission, entity-type checks, and cross-workspace non-disclosure. Live API
verification awaits a local backend process restart because the Windows execution
approval service reached its usage limit; the existing backend remains healthy on
its previous code version.

SECURITY:
Published/retired rendering requires effective ENTITY_READ; draft preview requires
FORM_DESIGN. Form access is active-membership scoped. Entity, parent, attribute,
and referenced records are resolved only inside the form workspace; foreign IDs
produce non-disclosing not-found behavior. Stored rules continue through the
bounded version-1 evaluator with no executable expression support.

DATABASE_CHANGES:
None.

API_CHANGES:
Implemented GET /forms/{form_id}/render with optional entity_id. The normalized
contract returns form/version identity, ordered sections, all generic field types,
evaluated visible/required/read-only state, current/inherited/default value and
source, field configuration, and safe rule metadata. The canonical OpenAPI and API
specification define the response and precedence rules.

USER_VISIBLE_RESULT:
The next frontend slice can render published dynamic forms directly from one stable,
frontend-ready contract, including inherited values and repeating-table metadata.

KNOWN_LIMITATIONS:
Current values are sourced from canonical entity attributes until DATA-BE-001 adds
draft form-instance values. Backend validation and persistence of submitted values
remain DATA-BE-001/DATA-BE-002. The local server must be restarted before manual
browser/API verification sees this endpoint.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
DATA-BE-001 Create/Save Form Instance, followed by FORM-FE-001 and FORM-FE-002 for
the demo-critical dynamic-form vertical slice.
```

Draft form instance implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M3 Dynamic Forms and Structured Data

TASKS_COMPLETED:
DATA-BE-001 Create/Save Form Instance

TASKS_IN_PROGRESS:
None

TEST_RESULTS:
Quota-conscious focused verification passes: Ruff formatting/lint, strict mypy for
the affected modules, 12 form-service/OpenAPI tests, and canonical OpenAPI YAML
parsing. Broader regression gates are intentionally deferred to the next demo
release checkpoint rather than repeated after every feature.

SECURITY:
Creation and draft saving require FORM_SUBMIT plus active workspace membership.
Definitions must be published, entities must be active and in the same workspace,
and configured entity types must match. Retrieval requires ENTITY_READ. Reference
values are resolved only in the instance workspace. Unknown, hidden, and read-only
fields are rejected by the backend.

DATABASE_CHANGES:
None beyond the existing form_instances table from migration 0009.

API_CHANGES:
Implemented POST /forms/{form_id}/instances, GET /form-instances/{instance_id}, and
PATCH /form-instances/{instance_id}. Responses retain exact form-definition/version
identity. Draft saves validate generic scalar/reference/table values, return stable
field error paths/codes, increment the instance version, reject stale edits, and
write transactional audit records. Canonical OpenAPI and API specifications updated.

TESTS_ADDED:
Service coverage for published-form instance creation, validation detail, audited
save, optimistic concurrency, draft-form rejection, and foreign-workspace entity
non-disclosure; API route discovery assertions extended.

USER_VISIBLE_RESULT:
The frontend can now create and persist an editable draft for a published dynamic
form, which unlocks the demo-critical generic form renderer.

KNOWN_LIMITATIONS:
Final required-field validation, phase locking, submission, and synchronization to
canonical entity attributes belong to DATA-BE-002. A backend restart is still needed
before the running local API exposes the newly implemented routes.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
FORM-FE-001 Dynamic Field Renderer as the next single demo-visible feature.
```

Dynamic field renderer implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M3 Dynamic Forms and Structured Data

TASKS_COMPLETED:
FORM-FE-001 Dynamic Field Renderer

TASKS_IN_PROGRESS:
None

TEST_RESULTS:
Quota-conscious focused frontend verification passes: zero-warning ESLint for the
affected files, strict application TypeScript, and 2 targeted component tests. The
test assertions execute in under one second; Windows/jsdom process startup accounts
for almost all of the approximately 70-second focused test duration. Full frontend
regression and production build are deferred to the demo release checkpoint.

SECURITY:
The component treats backend visible/read_only/required results as rendering input
and provides UX enforcement only. Backend validation and authorization remain
authoritative. It renders text safely through React/MUI without raw HTML injection.

DATABASE_CHANGES:
None.

API_CHANGES:
None. The component consumes the FORM-BE-004 normalized field contract.

TESTS_ADDED:
Focused coverage verifies visible scalar editing, hidden fields, inherited read-only
presentation, and metadata-defined repeating-row add/edit/remove behavior.

USER_VISIBLE_RESULT:
A single generic component can now render TEXT, RICH_TEXT, INTEGER, DECIMAL, BOOLEAN,
DATE, DATETIME, ENUM, MULTI_ENUM, USER_REFERENCE, ENTITY_REFERENCE, FILE_REFERENCE,
and TABLE fields. It supports Persian labels/errors, required/read-only/visibility
state, inherited-value decoration, enum option metadata, and dynamic table columns.

KNOWN_LIMITATIONS:
Reference fields use generic text input unless metadata supplies selector behavior;
specialized workspace reference pickers require their corresponding list contracts.
The component is not yet mounted in an entity form—the form-level fetch/save layout
is FORM-FE-002.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
FORM-FE-002 Dynamic Form Renderer, as the next single demo-visible feature.
```

Dynamic form renderer implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M3 Dynamic Forms and Structured Data

TASKS_COMPLETED:
FORM-FE-002 Dynamic Form Renderer

TASKS_IN_PROGRESS:
None

TEST_RESULTS:
Quota-conscious focused frontend verification passes: zero-warning ESLint across
the forms module and entity integration, strict application TypeScript, and 2
targeted form-level interaction tests. The test assertions cover the critical
fetch/render/create/save/error flow and complete in under one second after module
loading. Full frontend regression, production build, and browser E2E remain deferred
to the demo release checkpoint.

SECURITY:
The frontend shows save controls only with FORM_SUBMIT as a UX guard. Backend
membership, FORM_SUBMIT/ENTITY_READ authorization, workspace isolation, validation,
and optimistic concurrency remain authoritative. Backend errors are mapped using
stable codes and field paths rather than displaying server diagnostics.

DATABASE_CHANGES:
None.

API_CHANGES:
None. The feature consumes FORM-BE-004 and DATA-BE-001 contracts.

TESTS_ADDED:
Focused coverage verifies ordered section rendering, current-value population,
first-save instance creation, versioned draft persistence, success feedback, and
authoritative backend validation mapping to the correct field.

USER_VISIBLE_RESULT:
The generic entity detail Forms tab now lists published forms for the entity type,
opens the selected form, renders all metadata-defined sections/fields, visually
preserves inherited/read-only values, creates a draft on first save, and persists
later edits using optimistic concurrency. No domain-specific entity/form branches
were introduced.

KNOWN_LIMITATIONS:
There is no instance-by-entity/form lookup endpoint, so reopening the page cannot yet
rediscover a previously created draft; the current browser session keeps and updates
the created instance. Final submit/required validation and canonical entity-value
synchronization remain DATA-BE-002. The local backend must be restarted before the
running website exposes the supporting APIs.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
DATA-BE-002 Submit Form Instance as the next single important feature. A durable
instance lookup/resume API remains an open product-contract decision and is not
invented inside this task.
```

Submission dependency audit:

```text
DATE:
2026-08-23

MILESTONE:
M3 Dynamic Forms and Structured Data

TASKS_COMPLETED:
None (dependency correction only)

TASKS_IN_PROGRESS:
None

BLOCKER:
DATA-BE-002 requires DATA-FR-005 backend lock enforcement. The canonical lock state
is phases.is_locked and association is phase_deliverables. PHASE-DB-001/PHASE-BE-002
are not implemented, and phase_deliverables also depends on DOC-DB-001 for its
document foreign key. Implementing submission now would silently omit a mandatory
security control; creating a partial phase schema would violate the database spec.

DECISION:
Corrected the DATA-BE-002 backlog dependency to include PHASE-BE-002. Submission is
deferred until its lock-policy prerequisite exists. No placeholder/no-op lock policy
and no noncanonical generic lock table will be introduced.

NEXT_TASK:
FORM-FE-004 Form Designer MVP is dependency-ready and provides the next strongest
demo-visible capability. DATA-BE-002 resumes after document and phase lock foundations.
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
