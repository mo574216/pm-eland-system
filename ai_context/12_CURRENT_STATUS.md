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

Form designer MVP implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M3 Dynamic Forms and Structured Data

TASKS_COMPLETED:
FORM-FE-004 Form Designer MVP

TASKS_IN_PROGRESS:
None

SUMMARY:
Added a Persian RTL workspace form designer for creating generic draft forms,
adding ordered sections and fields, configuring options, required/read-only
behavior and inheritance metadata, and previewing the backend render contract.

FILES_CHANGED:
Frontend form types/API, form designer page and focused test, dynamic form preview,
workspace route/navigation/dashboard, and Persian localization.

DATABASE_CHANGES:
None.

API_CHANGES:
None. The UI consumes the existing FORM-BE-001 and FORM-BE-004 contracts.

TESTS_ADDED:
One focused interaction test proving an administrator can select a draft and add
a metadata-defined ordered section through the authoritative form API.

TEST_RESULTS:
Quota-conscious focused gates pass: zero-warning ESLint for all affected frontend
modules, strict application TypeScript, and the focused FormDesignerPage test
(1 test passed). Broad regression/build gates remain deferred to the demo checkpoint.

SECURITY_IMPACT:
No authorization authority moved to the frontend. The designer only invokes the
existing backend-authorized, workspace-isolated form and metadata endpoints.

KNOWN_LIMITATIONS:
Field editing/removal and drag-and-drop ordering are not exposed by the current
draft-form contract. Publishing and creating a new version remain FORM-FE-005.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
FORM-FE-005 Publish/New Version UI, the next dependency-ready demo-visible feature.
```

Publish/new-version UI implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M3 Dynamic Forms and Structured Data

TASKS_COMPLETED:
FORM-FE-005 Publish/New Version UI

TASKS_IN_PROGRESS:
None

SUMMARY:
Added lifecycle controls to publish draft form definitions through an explicit
immutability confirmation and to copy published definitions into a newly selected
draft version for continued design.

FILES_CHANGED:
Frontend form API, form designer lifecycle UI, Persian localization, focused form
designer tests, and current status documentation.

DATABASE_CHANGES:
None.

API_CHANGES:
None. The UI consumes the existing FORM-BE-002 publish and new-version endpoints.

TESTS_ADDED:
Focused interaction coverage for publish confirmation and creating/selecting a
new draft version, alongside the existing draft-section designer test.

TEST_RESULTS:
Quota-conscious focused gates pass: zero-warning ESLint for affected modules,
strict application TypeScript, and 3 FormDesignerPage interaction tests.

SECURITY_IMPACT:
Frontend controls are UX only. FORM_DESIGN authorization, workspace isolation,
validation, audit, and published-definition immutability remain backend enforced.

KNOWN_LIMITATIONS:
The list currently displays stable lifecycle codes with version numbers; richer
localized lifecycle filters and history comparison are deferred UI enhancements.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
Housekeeping and dependency audit for the next P0 M4 document/import slice.
```

Document schema implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M4 Documents and Import

TASKS_COMPLETED:
DOC-DB-001 Document Schema

TASKS_IN_PROGRESS:
None

SUMMARY:
Added the generic logical-document and immutable document-version persistence
model, including private object keys, checksums, scan/preview states, version
identity, current-version linkage, and workspace/entity ownership metadata.

FILES_CHANGED:
Document ORM models and exports, Alembic revision 0010, focused schema-contract
tests, and current status documentation.

DATABASE_CHANGES:
Revision 0010 creates documents and document_versions, their constraints and
indexes, then adds the circular current-version foreign key safely. The local
PostgreSQL database migrated successfully from 0009 to 0010 (head).

API_CHANGES:
None.

TESTS_ADDED:
Two schema-contract tests covering workspace/entity ownership, current-version
linkage, immutable version numbering, unique object keys, JSON metadata, and
storage-state constraints.

TEST_RESULTS:
Focused Ruff and strict mypy checks pass; 2 schema tests pass; Alembic upgrade to
0010 completes against local PostgreSQL and reports 0010 as head.

SECURITY_IMPACT:
Binary data remains outside PostgreSQL. The schema stores only private object
identifiers and security workflow state; it introduces no public storage access
or client credentials. API authorization remains future document-service work.

KNOWN_LIMITATIONS:
Schema alone cannot enforce that current_version_id belongs to the same logical
document; the document service must set it transactionally from a locked version
record belonging to that document. Storage IO starts with DOC-BE-001.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
DOC-BE-001 Storage Provider Abstraction.
```

Storage provider abstraction implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M4 Documents and Import

TASKS_COMPLETED:
DOC-BE-001 Storage Provider Abstraction

TASKS_IN_PROGRESS:
None

SUMMARY:
Added the async StorageProvider boundary and a MinioStorageProvider adapter for
private uploads, deletion, existence checks, bucket initialization, and bounded
presigned upload/download access. Added validated environment configuration and
a factory that unwraps credentials only when constructing the adapter.

FILES_CHANGED:
Backend storage service, settings, MinIO dependency/lock, focused storage tests,
one production-settings fixture, and current status documentation.

DATABASE_CHANGES:
None.

API_CHANGES:
None.

TESTS_ADDED:
Focused coverage verifies private-bucket operations, exact object scoping,
five-minute URL expiry, rejection of unsafe path shapes before IO, missing-secret
failure, and the maximum expiry bound.

TEST_RESULTS:
Focused Ruff and strict mypy checks pass; 12 storage/config/security tests pass;
the frozen dependency lock resolves successfully using the repository-local cache.

SECURITY_IMPACT:
Buckets remain private, URLs are limited to 60–900 seconds, object keys reject
absolute/traversal shapes, secrets use SecretStr and are never returned by the
adapter, and provider failures expose stable non-sensitive messages.

KNOWN_LIMITATIONS:
The adapter is unit-tested against a faithful client fake; live MinIO integration
is deferred until deployment services are available. Authorization must occur in
the document service before requesting any presigned URL.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
DOC-BE-002 Upload First Document Version.
```

First document-version upload implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M4 Documents and Import

TASKS_COMPLETED:
DOC-BE-002 Upload First Document Version

TASKS_IN_PROGRESS:
None

SUMMARY:
Added the authenticated multipart upload endpoint and transactional document
service that creates a logical document plus immutable version 1, stores the
binary under a server-generated private key, computes SHA-256, marks scanning
pending, sets the current version, and emits a workspace-scoped audit record.

FILES_CHANGED:
Document API/dependency/schema/repository/service, router/application injection,
file-policy settings and errors, document model type alignment, multipart
dependency/lock, focused service/OpenAPI tests, and current status documentation.

DATABASE_CHANGES:
No new migration. DOC-DB-001 revision 0010 is consumed. The ORM file-size type
was aligned with the migration's BIGINT definition.

API_CHANGES:
Implemented the already-published POST /api/v1/entities/{entity_id}/documents
multipart contract with its canonical 202 success envelope.

TESTS_ADDED:
Focused tests cover permission-before-IO, workspace/entity ownership, extension
and MIME pairing, PDF spoof detection, actual-size limits, safe generated keys,
checksum/version/current linkage, audit emission, and orphan cleanup after a
database failure. Generated OpenAPI multipart/202 behavior is also asserted.

TEST_RESULTS:
Focused Ruff and strict mypy checks pass; 9 combined document schema, storage,
upload-service, and OpenAPI tests pass. The dependency lock includes and installs
python-multipart successfully.

SECURITY_IMPACT:
The backend is authoritative for permission and workspace scope. Original names
never influence object paths; unsafe filenames, disallowed extension/MIME pairs,
oversized/empty files, and obvious signature mismatches are rejected before IO.
Audit state excludes object keys and checksums. Failed persistence triggers
best-effort private-object cleanup.

KNOWN_LIMITATIONS:
Deep malware analysis remains DOC-BE-006. Signature checks are deliberately
lightweight and do not replace quarantined scanning. Live MinIO integration is
still deferred to deployment-service availability.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
DOC-BE-003 Add Document Version.
```

Immutable document-version upload implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M4 Documents and Import

TASKS_COMPLETED:
DOC-BE-003 Add Document Version

TASKS_IN_PROGRESS:
None

SUMMARY:
Added multipart upload of subsequent immutable versions. The service locks the
accessible active logical document, allocates the next number, stores a new
private object, preserves every previous row/object, advances the current pointer
transactionally, and audits the before/after version identity.

FILES_CHANGED:
Document repository/service/API/schema, canonical and narrative API contracts,
focused service/OpenAPI tests, and current status documentation.

DATABASE_CHANGES:
None. Existing DOC-DB-001 uniqueness and foreign-key constraints are consumed.

API_CHANGES:
Added POST /api/v1/documents/{document_id}/versions as multipart file plus optional
comment, returning the canonical 202 document/version/scan-status envelope. The
previously missing endpoint is now recorded in contracts/openapi.yaml and the API
specification.

TESTS_ADDED:
Focused coverage proves row-lock use, monotonically allocated version 2, untouched
version 1 identity/object key, current pointer advancement, comment persistence,
audit before/after state, and generated multipart OpenAPI behavior.

TEST_RESULTS:
Focused Ruff and strict mypy checks pass; 10 combined document schema, storage,
upload/version-service, and OpenAPI tests pass; canonical OpenAPI YAML parses.

SECURITY_IMPACT:
Active membership and DOCUMENT_UPLOAD are enforced before storage access; locked
allocation prevents concurrent silent overwrite; every version uses a new
server-generated key; all first-upload file security checks are reused.

KNOWN_LIMITATIONS:
Version history retrieval is implemented with the upcoming document panel/API
work. Malware and preview state processing remain separate backlog tasks.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
DOC-BE-004 Download Access, while document metadata/history reads required by the
frontend panel will be added with the smallest contract-aligned read slice.
```

Authorized document download implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M4 Documents and Import

TASKS_COMPLETED:
DOC-BE-004 Download Access

TASKS_IN_PROGRESS:
None

SUMMARY:
Added authorized exact-version download access through a private, short-lived
presigned URL. Version lookup is membership-scoped, DOCUMENT_READ is authoritative,
and configured scan policy is evaluated before any object-storage URL is generated.

FILES_CHANGED:
Document repository/service/API/schema, scan-policy settings and stable exception,
canonical/narrative API contracts, focused service/OpenAPI tests, and status docs.

DATABASE_CHANGES:
None.

API_CHANGES:
Added GET /api/v1/document-versions/{version_id}/download returning url and
expires_at in the canonical success envelope. The route is recorded in both API
contracts with 403/404/422 behavior.

TESTS_ADDED:
Focused coverage proves inaccessible versions, missing DOCUMENT_READ, and PENDING
scan status never generate storage access; CLEAN versions generate a URL for only
their exact object with the configured ten-minute expiry.

TEST_RESULTS:
Focused Ruff and strict mypy checks pass; 11 combined document schema, storage,
upload/version/download, and OpenAPI tests pass; canonical OpenAPI YAML parses.

SECURITY_IMPACT:
Private-bucket access is generated only after membership, permission, and scan
checks. Cross-workspace identifiers are hidden as not found. Default quarantine
permits only CLEAN objects, and presigned expiry remains bounded to 5–15 minutes.

KNOWN_LIMITATIONS:
Uploads remain PENDING until DOC-BE-006 supplies malware-state transitions. The
default policy intentionally prevents downloading unscanned content.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
DOC-FE-001 Document Panel with the contract-aligned document metadata/history read
slice, prioritized as the next demo-visible feature. DOC-BE-005 remains required
before DOC-FE-002 preview UI.
```

Document panel and metadata/history read implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M4 Documents and Import

TASKS_COMPLETED:
DOC-FE-001 Document Panel
Supporting contract-aligned document metadata/history read slice

TASKS_IN_PROGRESS:
None

SUMMARY:
Mounted a generic Persian RTL Document Panel in every entity detail page. Users
with permissions can upload a logical document, see current scan/version state,
open immutable history, upload subsequent versions, and download CLEAN versions.
Added workspace-authorized list/detail/history reads needed by the panel.

FILES_CHANGED:
Backend document read repository/service/API/schemas, canonical/narrative API
contracts and tests; frontend multipart client handling, generic document API/types/
panel and test, entity-detail integration, Persian localization, and status docs.

DATABASE_CHANGES:
None.

API_CHANGES:
Added contract-aligned GET endpoints for entity documents, logical document
metadata, and immutable version history. Responses exclude private object keys.

TESTS_ADDED:
Backend coverage verifies workspace/permission-scoped metadata/history reads with
no storage access. Frontend coverage verifies list/current state, expandable
immutable history, and multipart logical-document upload; entity-tab integration
now verifies the document permission state.

TEST_RESULTS:
Focused backend Ruff/mypy and 7 read/service/OpenAPI tests pass. Frontend zero-
warning ESLint, strict TypeScript, the DocumentPanel test, and the entity-detail
integration test pass. Canonical OpenAPI YAML parses. Broad gates remain deferred
to the demo checkpoint per quota policy.

SECURITY_IMPACT:
Backend membership and DOCUMENT_READ/UPLOAD remain authoritative. Metadata reads
never require or expose storage credentials/object keys. Download stays disabled
in the UI unless CLEAN, while the backend independently enforces scan policy.
Client file checks are UX only and multipart boundaries are browser-generated.

KNOWN_LIMITATIONS:
Upload progress is represented by disabled/pending controls rather than byte-level
progress because the shared fetch client does not expose upload progress events.
The running local backend must be restarted before the browser can use new routes.
Preview waits for DOC-BE-005 and DOC-FE-002.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
DOC-BE-005 Preview Workflow, followed by DOC-FE-002 Preview and Version History UI.
```

Native document preview workflow implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M4 Documents and Import

TASKS_COMPLETED:
DOC-BE-005 Preview Workflow (P0 PDF/images)

TASKS_IN_PROGRESS:
None

SUMMARY:
Added authorized preview availability and short-lived exact-object access for
CLEAN PDF, PNG, and JPEG versions. Native-preview capability is recorded at upload
without bypassing quarantine. Conversion-dependent formats remain explicitly
unavailable/queued, and raw SVG is never returned for embedding.

FILES_CHANGED:
Document upload/preview service, preview API/schema, canonical/narrative contracts,
focused preview/OpenAPI tests, and current status documentation.

DATABASE_CHANGES:
None. Existing preview_status metadata is used; newly uploaded native-preview
formats are marked READY while scan_status remains independently PENDING.

API_CHANGES:
Added GET /api/v1/document-versions/{version_id}/preview with 200 availability/
ready responses and declared 202 behavior for queued conversion workflows.

TESTS_ADDED:
Focused coverage verifies PENDING quarantine, CLEAN PDF and raster IMAGE access,
exact-object URL generation, bounded expiry, and refusal to preview raw SVG.

TEST_RESULTS:
Focused Ruff and strict mypy checks pass; 7 document-service/OpenAPI tests pass;
canonical OpenAPI YAML parses.

SECURITY_IMPACT:
Membership, DOCUMENT_READ, and scan policy precede storage access. URLs stay
private, exact-object, and bounded. No server-side PDF execution, raw SVG embed,
Office macro execution, or in-process conversion was introduced.

KNOWN_LIMITATIONS:
Office preview conversion is P1 and requires an isolated background worker. Old
rows created before this feature may retain NOT_REQUESTED until reprocessed.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
DOC-FE-002 Preview and Version History UI.
```

Document preview and version-history UI implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M4 Documents and Import

TASKS_COMPLETED:
DOC-FE-002 Preview and Version History UI

TASKS_IN_PROGRESS:
None

SUMMARY:
Extended the generic Document Panel with backend-authorized preview access and a
Persian RTL dialog for immutable versions. Backend-declared PDF previews render in
a dedicated iframe and raster images render responsively; history, scan/preview
states, version upload, and download remain available together.

FILES_CHANGED:
Frontend document types/API/panel, Persian localization, focused panel test, and
current status documentation.

DATABASE_CHANGES:
None.

API_CHANGES:
None. The UI consumes the DOC-BE-005 preview contract.

TESTS_ADDED:
Focused interaction coverage verifies history expansion, preview request for the
selected immutable version, safe PDF dialog rendering with the authorized URL,
dialog closure, and the existing multipart upload flow.

TEST_RESULTS:
Zero-warning ESLint and strict application TypeScript pass; the focused Document
Panel preview/history/upload interaction test passes. Broader gates remain deferred
to the demo checkpoint per quota policy.

SECURITY_IMPACT:
The frontend renders only backend-declared PDF or IMAGE preview types, uses
no-referrer embeds, and never infers/executes SVG or Office content. Preview buttons
remain disabled unless scan and preview states are CLEAN/READY; backend policy is
still authoritative.

KNOWN_LIMITATIONS:
Office conversion preview remains P1. Byte-level upload progress is still not
available through the shared fetch client. New backend routes require a local API
restart before browser use.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
IMP-DB-001 Import Schema, the next dependency-ready P0 backlog task. DOC-BE-006
Malware Scan Workflow remains P1 security hardening.
```

Import schema implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M4 Documents and Import

TASKS_COMPLETED:
IMP-DB-001 Import Schema

TASKS_IN_PROGRESS:
None

SUMMARY:
Added the generic, metadata-driven persistence foundation for reusable import
profiles, column mappings, staged import jobs, and explicit conflict resolution.
The schema follows the documented safe lifecycle and does not introduce any
domain-specific concepts.

FILES_CHANGED:
Import ORM models and exports, Alembic revision 0011, focused schema contract
tests, and current status documentation.

DATABASE_CHANGES:
Revision 0011 creates import_profiles, import_mappings, import_jobs, and
import_conflicts with the specified foreign keys, JSONB configuration/value
fields, lifecycle and resolution checks, conflict lookup index, and optional
workspace-scoped idempotency uniqueness. The local database was upgraded from
0010 to 0011 successfully.

API_CHANGES:
None.

TESTS_ADDED:
Three focused contract tests cover generic profile/mapping metadata, staged job
summaries and idempotency, and preservation of both conflict values with explicit
resolution.

TEST_RESULTS:
Ruff formatting and lint pass for the changed files; strict mypy passes for the
new model; all three focused schema tests pass; migration upgrade to 0011 and head
verification pass. The repository-wide Alembic drift check still reports older
identity/audit ORM-to-migration differences outside this task.

SECURITY_IMPACT:
Profiles and jobs are workspace-scoped, import source objects remain private
storage references, job retries can be made idempotent per workspace, and conflict
records retain both canonical and imported values so later services cannot silently
overwrite data.

KNOWN_LIMITATIONS:
Service-layer work must validate that profiles, entity types, attributes, jobs,
and users belong to the same workspace. Parser limits, mapping validation, dry-run,
transactional commit, authorization, and audit behavior are implemented by the
following IMP-BE tasks rather than this persistence-only task. Pre-existing
identity/audit Alembic drift remains to be reconciled during housekeeping.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
IMP-BE-001 XLSX/CSV Parser.
```

Import parser implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M4 Documents and Import

TASKS_COMPLETED:
IMP-BE-001 XLSX/CSV Parser

TASKS_IN_PROGRESS:
None

SUMMARY:
Implemented a generic, bounded ImportParser that inspects UTF-8 CSV and XLSX
workbooks and returns sheet names, data-row counts, column headers, and bounded
sample values. XLSX formulas are read only as cached values and are never
evaluated. Malformed inputs and deterministic resource-limit violations fail with
safe reason codes that do not disclose imported content.

FILES_CHANGED:
Import parser service, focused parser tests, backend dependency manifest and lock,
backend parser strategy documentation, and current status documentation.

DATABASE_CHANGES:
None.

API_CHANGES:
None. Import upload/analyze endpoints remain a later service/API task.

TESTS_ADDED:
Eight focused cases cover CSV inspection and bounded sampling, multi-sheet XLSX
inspection, formula non-evaluation, malformed XLSX, invalid CSV encoding, duplicate
headers, empty input, unsupported file types, input/row limits, and suspicious ZIP
compression.

TEST_RESULTS:
Ruff formatting and lint pass; strict mypy passes; all eight parser tests pass;
the combined import schema/parser suite passes all 11 tests. Runtime verification
confirms openpyxl is using defusedxml.

SECURITY_IMPACT:
Untrusted input is bounded by compressed bytes, expanded archive bytes, archive
entries, compression ratio, sheets, rows, columns, cell size, and sample count.
XLSX uses read-only/data-only mode with external-link preservation disabled and
defused XML parsing. Formulas are not executed and safe errors contain no cell
content.

KNOWN_LIMITATIONS:
The synchronous parser intentionally rejects files above its limits. Larger files
require a future isolated background worker with equivalent archive, time, and
memory safeguards. CSV currently accepts UTF-8 with optional BOM; legacy encodings
require an explicit future product decision. Upload persistence, workspace
authorization, job state transitions, and asynchronous dispatch follow in later
IMP-BE tasks.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
IMP-BE-002 Import Profiles and Mapping.
```

Import profile and mapping implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M4 Documents and Import

TASKS_COMPLETED:
IMP-BE-002 Import Profiles and Mapping

TASKS_IN_PROGRESS:
None

SUMMARY:
Implemented reusable workspace-scoped import profiles with atomic mapping creation
and replacement. Profiles target generic entity types; mappings target exactly one
active attribute belonging to that type or an allowed generic entity system field.
Create, list, retrieve, and update operations are exposed through authenticated API
routes and material mutations are audited in the same transaction.

FILES_CHANGED:
Import profile schemas, repository, service, API router, API specification,
canonical OpenAPI contract, focused service/OpenAPI tests, and status documentation.

DATABASE_CHANGES:
None. The implementation uses the IMP-DB-001 tables.

API_CHANGES:
Added POST/GET /workspaces/{workspace_id}/import-profiles and GET/PATCH
/import-profiles/{profile_id}. The canonical and narrative API contracts were
updated together.

TESTS_ADDED:
Six focused service/schema cases cover exclusive mapping targets, atomic audited
creation, workspace-role permissions, missing permission rejection, foreign or
wrong-type attribute rejection, and atomic audited mapping replacement. OpenAPI
coverage asserts both route groups.

TEST_RESULTS:
Ruff formatting/lint and strict mypy pass for the implementation; all seven focused
service/OpenAPI tests pass; canonical OpenAPI YAML parses successfully.

SECURITY_IMPACT:
Backend IMPORT_EXECUTE authorization and active workspace membership are required.
Entity types and attribute targets are verified in the same workspace/type;
cross-workspace references fail. Mapping replacement and audit writes are atomic,
and request schemas reject unknown fields and multiple/no mapping targets.

KNOWN_LIMITATIONS:
Matching strategy configuration is intentionally deferred to IMP-BE-003. Parser
upload/job orchestration and mapping execution follow in subsequent import tasks.
The import-profile table has no optimistic version column in the accepted schema,
so updates use transaction atomicity but not client version preconditions.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
Repository/CI stabilization for PR #6, as requested, before IMP-BE-003.
```

PR #6 CI stabilization entry:

```text
DATE:
2026-08-23

MILESTONE:
Repository Quality / Required CI Gate

TASKS_COMPLETED:
PR #6 backend-quality and frontend-test failure repair

TASKS_IN_PROGRESS:
None

SUMMARY:
Reproduced and repaired both root failures from GitHub Actions run 32655400502.
Strict backend mypy failed on a Literal-typed configuration factory plus import
parser/schema test typing; the frontend test suite failed because the dashboard
test retained the old three-available/four-planned counts after workspace settings
became available. The Required CI Gate failure was consequential, and the build was
skipped because it depends on all preceding jobs.

FILES_CHANGED:
Typed configuration default factory, import parser/schema test typing, workspace
dashboard expectation, and current status documentation.

DATABASE_CHANGES:
None.

API_CHANGES:
None.

TESTS_ADDED:
None for the stabilization itself; stale and strict-typing coverage was corrected.

TEST_RESULTS:
Full backend format check, Ruff lint, strict mypy across app/scripts/tests, and all
166 backend tests with warnings-as-errors pass. All 31 frontend tests, zero-warning
ESLint, TypeScript checks, and production build pass. The referenced remote run
confirms backend quality and frontend tests were the only root failures; frontend
quality, backend tests, migration, secret scan, and Persian RTL E2E passed. A local
Windows E2E rerun was stopped after hanging in the browser runner, but the same E2E
job was green in the referenced GitHub run and its code was unchanged.

SECURITY_IMPACT:
No security controls were weakened. The secret scan and migration verification in
the referenced run passed, and backend tests continue to run with warnings treated
as errors.

KNOWN_LIMITATIONS:
GitHub will not rerun PR checks until these working-tree changes are committed and
pushed to the PR branch. The build job will remain skipped in the old run because
its dependencies already failed; a new run is required.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
Commit/push the repair and IMP-BE-001/002 slices, confirm a new Required CI Gate,
then resume IMP-BE-003 Matching Strategy.
```

Import matching strategy implementation entry:

```text
DATE:
2026-08-23

MILESTONE:
M4 Documents and Import

TASKS_COMPLETED:
IMP-BE-003 Matching Strategy

TASKS_IN_PROGRESS:
None

SUMMARY:
Added an explicit, discriminated matching-strategy contract for stable entity ID,
unique attribute, composite key, and parent-plus-key matching. Strategies are stored
inside reusable import profiles and may be replaced through the existing profile
API. Attribute and generic-name keys must correspond exactly to profile mappings;
parent-plus-key also requires an explicit parent_id mapping. Entity ID remains a
read-only match input rather than a mutable mapping target.

FILES_CHANGED:
Import profile schemas/service/API integration, backend and narrative API
specifications, canonical OpenAPI matching schemas, focused profile strategy tests,
and current status documentation.

DATABASE_CHANGES:
None. Strategies use the accepted import_profiles.matching_strategy JSONB field.

API_CHANGES:
Import profile create now requires matching_strategy; profile update may replace it.
The contract supports ENTITY_ID, UNIQUE_ATTRIBUTE, COMPOSITE_KEY, and
PARENT_AND_KEY discriminators with bounded, explicit key definitions.

TESTS_ADDED:
Focused coverage verifies distinct composite keys, rejects parent-plus-key without
an explicit parent mapping, and proves successful persistence for entity-ID,
unique-attribute, composite, and parent-plus-key modes.

TEST_RESULTS:
Ruff formatting/lint and strict mypy pass for the changed backend files; all ten
focused profile/OpenAPI tests pass; canonical OpenAPI YAML parses successfully.
The immediately preceding PR #6 workflow run 32663232281 passed every job including
the Required CI Gate before this slice began.

SECURITY_IMPACT:
Matching configuration remains workspace-authorized through ImportProfileService.
Foreign/inactive attribute IDs and unmapped key/parent sources are rejected.
Unknown strategy fields, implicit name fallback, mutable entity-ID mapping, and
arbitrary matching modes are prohibited by discriminated request schemas.

KNOWN_LIMITATIONS:
This task configures and validates matching semantics. Database lookup execution,
duplicate-row detection, ambiguity handling, diffs, and canonical-data protection
are implemented by IMP-BE-004 Dry Run. Existing pre-feature profiles with an empty
matching_strategy must be updated before they can be returned by the typed API.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
IMP-FE-001 Import Wizard as the next demo-visible, dependency-ready slice. It will
include the missing authorized upload/analyze API integration required to make the
wizard functional. IMP-BE-004 Dry Run follows that visible inspection workflow.
```

Visible import upload/inspect implementation entry:

```text
DATE:
2026-08-24

MILESTONE:
M4 Documents and Import / Demo-visible MVP

TASKS_COMPLETED:
IMP-FE-001 Import Wizard Upload/Inspect
Import upload/analyze API integration required by IMP-FE-001

TASKS_IN_PROGRESS:
None

SUMMARY:
Added a working Persian RTL seven-step import wizard and activated it in the
physical-right workspace navigation and dashboard. Users can select CSV/XLSX,
upload it through the authenticated API, and immediately inspect real sheet names,
row counts, headers, and bounded sample values. The backend creates an audited
staged job and stores the source under a server-generated private workspace key;
canonical entities remain unchanged.

FILES_CHANGED:
Import job repository/service/schemas/API, focused backend tests, import wizard
types/API/page/test, application route, workspace navigation/dashboard, Persian
localization, API contracts, OpenAPI test, and current status documentation.

DATABASE_CHANGES:
None. Uploads use the accepted import_jobs table from revision 0011.

API_CHANGES:
Implemented POST /workspaces/{workspace_id}/imports as multipart file upload with
optional import_profile_id. The 202 response now includes import_job_id, UPLOADED
status, and safe synchronous sheet/column/sample inspection. Narrative and
canonical contracts were updated.

TESTS_ADDED:
Backend tests prove authorized private/audited upload with real parsing and reject
missing permission or a cross-workspace profile. Frontend interaction coverage
proves file selection, upload, workspace routing, and rendering of returned source
metadata. Dashboard coverage reflects the newly available import capability.

TEST_RESULTS:
Focused Ruff and strict mypy pass; 11 backend import/parser/OpenAPI tests pass.
Frontend zero-warning ESLint and TypeScript pass; the wizard and dashboard tests
both pass.

SECURITY_IMPACT:
IMPORT_EXECUTE and active workspace membership are authoritative. Optional profiles
must belong to the same workspace and match the file source type. Input is parsed
under the existing archive/XML/resource limits before private storage; object keys
are server-generated, mutations are audited, storage failures are safe, and no
canonical entity values are changed.

KNOWN_LIMITATIONS:
Only synchronous files within the documented parser limits are accepted. The
wizard visibly reserves mapping, dry-run, conflict, commit, and completion steps,
but they remain disabled until their backend prerequisites are implemented. The
running local backend must be restarted to expose the new route.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
IMP-FE-002 Mapping UI as the next demo-visible task, paired with the minimum
profile/mapping integration needed to progress the same wizard. IMP-BE-004 Dry Run
then unlocks the visible summary step.
```

Import mapping UI implementation entry:

```text
DATE:
2026-08-24

MILESTONE:
M4 Documents and Import / Demo-visible MVP

TASKS_COMPLETED:
IMP-FE-002 Mapping UI

TASKS_IN_PROGRESS:
None

SUMMARY:
Extended the live Persian RTL import wizard with sheet selection, metadata-driven
entity-type and attribute targets, source-to-target column mapping, all four
accepted matching strategies, client-side invalid/duplicate mapping feedback, and
creation or reuse of authorized import profiles. Saving a profile advances the
visible wizard to the dry-run boundary.

FILES_CHANGED:
Import mapping component, wizard page and focused interaction test, frontend import
API/types, Persian localization, import-profile validation service/test, and current
status documentation.

DATABASE_CHANGES:
None.

API_CHANGES:
No new backend endpoint or published payload. The frontend now consumes the accepted
import-profile create/list endpoints.

TESTS_ADDED:
The focused wizard interaction proves real inspection rendering, metadata target
selection, a name mapping and matching key, profile creation, and visible wizard
advancement. Backend coverage proves duplicate target mappings are rejected.

TEST_RESULTS:
Frontend focused test passes; zero-warning ESLint, strict TypeScript, and production
build pass. Backend focused import-profile suite passes 10 tests; Ruff format/lint
and strict mypy pass for changed backend files.

SECURITY_IMPACT:
Backend workspace membership and IMPORT_EXECUTE checks remain authoritative for
profile listing and creation. The UI uses only backend-returned active metadata,
does not expose read-only attributes as import targets, and adds no client-side
authorization assumption. Duplicate targets are independently rejected server-side.

KNOWN_LIMITATIONS:
The uploaded job is not yet associated with the newly created or selected profile.
That lifecycle transition and re-validation of source columns belong to the dry-run
backend integration. Transform configuration remains an empty generic object until
its dedicated UX is specified.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
IMP-BE-004 Dry Run, including the accepted job-to-mapping/profile transition, then
IMP-FE-003 Dry-Run Summary UI for the earliest useful read-only MVP demonstration.
```

Import dry-run backend implementation entry:

```text
DATE:
2026-08-25

MILESTONE:
M4 Documents and Import / Demo-visible MVP

TASKS_COMPLETED:
IMP-BE-004 Dry Run

TASKS_IN_PROGRESS:
None

SUMMARY:
Implemented authorized reusable-profile assignment and a read-only import dry-run
engine. It securely reads the private staged source, streams bounded CSV/XLSX rows,
maps generic system fields and metadata attributes, applies safe type coercion and
metadata validation, executes all accepted matching strategies, rejects duplicate
or ambiguous source keys, and classifies create/update/unchanged/invalid rows.
Differences from persisted generic entities create reviewable conflict records;
canonical entity objects are never mutated.

FILES_CHANGED:
Import dry-run service, job repository/schemas/API, parser row iterator, private
storage reader, focused parser/storage/dry-run tests, narrative and canonical API
contracts, and current status documentation.

DATABASE_CHANGES:
None. Dry-run uses the accepted import_jobs.dry_run_summary and import_conflicts
structures from revision 0011.

API_CHANGES:
Implemented PUT /imports/{import_job_id}/mapping with an import_profile_id and POST
/imports/{import_job_id}/dry-run. Mapping assignment clears stale prior analysis.
Dry-run returns status, required summary counters, and row-addressable validation
errors. The canonical and narrative contracts were updated.

TESTS_ADDED:
Parser coverage proves full row iteration for CSV/XLSX without formula evaluation;
storage coverage proves private server-side reads; dry-run coverage proves create,
update, invalid and duplicate classification, persisted field conflicts, and an
unchanged canonical entity snapshot.

TEST_RESULTS:
All 174 backend tests pass. Full backend Ruff format/lint and strict mypy across
app, scripts, and tests pass.

SECURITY_IMPACT:
Active workspace membership and IMPORT_EXECUTE are checked before source access and
again inside the persistence transaction. Profiles are constrained to the job
workspace and source type. Source objects remain private, spreadsheet formulas are
never evaluated, arbitrary transformations are not executed, references remain
workspace-resolved, and a locked compare-before-write prevents stale dry-run state.

KNOWN_LIMITATIONS:
Validation errors are currently stored with the bounded job summary rather than a
separate paginated table. Existing candidates for the selected entity type are
loaded as one read-only matching snapshot; query-side batched matching is a future
performance optimization for very large workspaces. Conflict resolution and commit
remain intentionally unavailable until IMP-BE-005 and IMP-BE-006.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
IMP-FE-003 Dry-Run Summary UI, integrated into the same visible wizard. IMP-BE-005
Conflict Resolution follows immediately because dry-run now persists conflicts.
```

Dry-run summary UI implementation entry:

```text
DATE:
2026-08-25

MILESTONE:
M4 Documents and Import / First useful MVP demo

TASKS_COMPLETED:
IMP-FE-003 Dry-Run Summary UI

TASKS_IN_PROGRESS:
None

SUMMARY:
Connected the import wizard to the accepted mapping-assignment and dry-run APIs.
After creating or reusing a profile, users can explicitly run a read-only analysis
and see Persian RTL status, rows read/valid/invalid, creates, updates, unchanged
records, conflicts, and row-addressable validation errors. Loading, retry, and safe
failure states keep the user at the correct wizard boundary.

FILES_CHANGED:
Frontend import API/types, wizard orchestration and focused interaction test,
dry-run summary component, Persian localization, and current status documentation.

DATABASE_CHANGES:
None.

API_CHANGES:
No new API beyond the accepted IMP-BE-004 endpoints. The frontend now consumes PUT
/imports/{import_job_id}/mapping and POST /imports/{import_job_id}/dry-run.

TESTS_ADDED:
The existing focused wizard interaction now proves profile assignment, dry-run
execution, summary rendering, ready-for-review status, and the explicit guarantee
that canonical entities were not changed.

TEST_RESULTS:
Frontend zero-warning ESLint and strict TypeScript pass. The focused wizard test
passes in a single worker after the Windows fork pool timed out before starting a
worker. Production build passes; the existing advisory bundle-size warning remains.

SECURITY_IMPACT:
The browser sends only opaque job/profile identifiers and renders backend-authorized
results. Backend permission, workspace isolation, matching, reference validation,
and canonical write prevention remain authoritative. No commit control is exposed.

KNOWN_LIMITATIONS:
Validation codes are displayed as stable machine codes pending a dedicated localized
error-code presentation map. Conflict rows can be counted but not reviewed or
resolved until IMP-BE-005 and IMP-FE-004. The main JavaScript bundle remains above
Vite's advisory 500 kB threshold; route-level splitting is deferred housekeeping.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
IMP-BE-005 Conflict Resolution followed by IMP-FE-004 Conflict Resolver UI, keeping
the same demo-first vertical slice.
```

Import conflict-resolution backend implementation entry:

```text
DATE:
2026-08-25

MILESTONE:
M4 Documents and Import / Demo-visible MVP

TASKS_COMPLETED:
IMP-BE-005 Conflict Resolution

TASKS_IN_PROGRESS:
None

SUMMARY:
Implemented paginated import-conflict reads and explicit per-field or selected-bulk
MERGE, REPLACE, and SKIP decisions. Decisions retain actor/time attribution, every
mutation is audited, no resolution is selected by default, and the job advances to
READY_TO_COMMIT only when its persisted unresolved count reaches zero. A conflict-
free valid dry run now advances directly to READY_TO_COMMIT.

FILES_CHANGED:
Import conflict service, job repository queries, import API schemas/routes, focused
authorization/state tests, dry-run readiness transition, canonical API contract,
frontend status type/localization, and current status documentation.

DATABASE_CHANGES:
None. Resolution uses the accepted nullable resolution/resolved_by/resolved_at fields
on import_conflicts.

API_CHANGES:
Implemented GET /imports/{import_job_id}/conflicts, PUT
/imports/{import_job_id}/conflicts/{conflict_id}, and POST
/imports/{import_job_id}/resolve-bulk. Filters distinguish ALL, UNRESOLVED, RESOLVED,
and each decision. The canonical contract now publishes the routes and bounded
request payloads.

TESTS_ADDED:
Focused service tests prove nullable decisions become actor-attributed explicit
MERGE/SKIP decisions, bulk resolution is atomic, the last decision unlocks commit,
audits are written, missing permission is rejected, and a foreign/missing conflict
is not exposed.

TEST_RESULTS:
All 176 backend tests pass. Full backend Ruff format/lint and strict mypy across
app, scripts, and tests pass.

SECURITY_IMPACT:
Active workspace membership and IMPORT_EXECUTE remain authoritative. Conflict lookup
is constrained by both job and conflict identifiers, mutations lock current rows,
bulk IDs must be unique and all belong to the job, stale/non-reviewable job states
are rejected, and existing values are never overwritten by choosing a decision.

KNOWN_LIMITATIONS:
MERGE, REPLACE, and SKIP are persisted decisions only; their transactional write
semantics are intentionally deferred to IMP-BE-006. Bulk resolution operates on an
explicit bounded ID list rather than every result matching a server-side filter.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
IMP-FE-004 Conflict Resolver UI, followed by IMP-BE-006 transactional commit.
```

Import conflict resolver UI implementation entry:

```text
DATE:
2026-08-25

MILESTONE:
M4 Documents and Import / Demo-visible MVP

TASKS_COMPLETED:
IMP-FE-004 Conflict Resolver UI

TASKS_IN_PROGRESS:
None

SUMMARY:
Extended the same Persian RTL import wizard with a paginated field-level conflict
table showing source row, field, existing value, imported value, and current
decision. Users can explicitly choose MERGE, REPLACE, or SKIP per conflict or for a
selected bounded set. No option is preselected, REPLACE is visually cautionary,
loading/failure states are visible, and resolving the last conflict advances the
wizard to the final-confirmation boundary.

FILES_CHANGED:
Conflict resolver component, wizard orchestration and focused interaction test,
frontend import API/types, Persian localization, and current status documentation.

DATABASE_CHANGES:
None.

API_CHANGES:
No new API beyond IMP-BE-005. The frontend now consumes paginated conflict listing,
single resolution, and bounded bulk resolution endpoints.

TESTS_ADDED:
The focused wizard interaction now continues through conflict retrieval, displays
existing/imported values, applies an explicit MERGE decision, verifies the backend
payload, and displays readiness for final confirmation.

TEST_RESULTS:
Frontend zero-warning ESLint, strict TypeScript, focused wizard test, and production
build pass. The realistic wizard test uses a 15-second per-test ceiling and a single
thread because Windows worker startup previously consumed most of the default five
seconds. The existing advisory bundle-size warning remains.

SECURITY_IMPACT:
Conflict data is rendered only after the backend-authorized job query. The UI does
not infer permissions, never defaults to overwrite, sends only accepted decisions
and opaque IDs, and provides no canonical commit action before IMP-BE-006.

KNOWN_LIMITATIONS:
Values are rendered as plain strings or serialized JSON; rich type-specific diff
visualization is deferred. Bulk actions apply only to explicitly selected rows on
the loaded pages. Transactional commit and completion summary remain unavailable.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
IMP-BE-006 Transactional Commit, then IMP-FE-005 Commit Confirmation and Summary.
```

Transactional import commit implementation entry:

```text
DATE:
2026-08-25

MILESTONE:
M4 Documents and Import / Demo-visible MVP

TASKS_COMPLETED:
IMP-BE-006 Transactional Commit

TASKS_IN_PROGRESS:
None

SUMMARY:
Added a synchronous, idempotent transactional commit endpoint that revalidates the
reviewed import evidence, rejects unresolved or changed inputs, and applies create,
update, unchanged, and skip outcomes to generic entity records as one atomic unit.
MERGE, REPLACE, and SKIP now have explicit field-level write semantics, and every
material entity change plus the completed import job receives an audit record.

FILES_CHANGED:
Import API, commit service, import repository and schemas, domain exceptions,
focused backend tests, OpenAPI contract, API specification, and this status file.

DATABASE_CHANGES:
None.

API_CHANGES:
POST /imports/{import_job_id}/commit now accepts an optional bounded
Idempotency-Key and returns a completed import summary. The OpenAPI contract and API
specification document the synchronous 200 response and commit failure responses.

TESTS_ADDED:
Focused tests cover generic entity creation/update/skip behavior and audits,
unresolved-conflict rejection, completed-job idempotent retry behavior, and rollback
of a forced failure after a simulated canonical write.

TEST_RESULTS:
Focused Ruff, strict mypy, import commit tests, and OpenAPI validation pass. Full
backend verification is recorded in the implementation handoff.

SECURITY_IMPACT:
Workspace access and IMPORT_EXECUTE are checked before source access and again under
the final job lock. The private stored source and reviewed evidence are revalidated,
unresolved conflicts cannot commit, silent overwrite is prevented, hierarchy parent
changes use cycle protection, optimistic versions protect updates, and mutations
are audited.

KNOWN_LIMITATIONS:
Commit is synchronous and partial commit is intentionally unsupported. No phase
association or phase-lock schema exists in this milestone; when that model lands,
the shared lock policy must be integrated before imports can mutate phase-associated
entities.

ARCHITECTURE_DEVIATIONS:
None.

NEXT_TASK:
Paused at user request before IMP-FE-005; awaiting usage-scenario guidance.
```

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
