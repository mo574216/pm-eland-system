# Development Task Backlog

**File:** `08_TASK_BACKLOG.md`  
**Status:** Normative Execution Plan  
**System:** Metadata-Driven Enterprise Architecture Management Platform  
**Version:** 1.0  
**Audience:** AI coding agents, human developers, project owner, QA, architecture reviewers

---

# 1. Purpose

This document converts the system architecture and requirements into executable development tasks.

Every implementation task SHALL:

- have a unique task ID,
- reference requirement IDs from `02_SYSTEM_REQUIREMENTS.md`,
- identify owning agent(s),
- identify dependencies,
- define acceptance criteria,
- identify expected artifacts,
- identify API/database/security impact,
- include tests.

Tasks SHALL be executed in dependency order unless the Architecture Agent explicitly approves parallel execution.

---

# 2. Priority Definitions

```text
P0 — required for MVP / blocks usable system
P1 — required for first production release
P2 — enhancement after core production release
P3 — future/optional
```

---

# 3. Milestones

Recommended milestone structure:

```text
M0 — Repository and Engineering Foundation
M1 — Identity, Workspace, and Security Foundation
M2 — Metadata and Generic Entity Platform
M3 — Dynamic Forms and Structured Data
M4 — Documents and Import
M5 — Phase Control, Review, Audit, Dashboard
M6 — Production Hardening
M7 — AI Enhancements
```

---

# 4. M0 — Repository and Engineering Foundation

# TASK FND-001 — Initialize Monorepo

**Priority:** P0  
**Owner:** DevOps Agent  
**Dependencies:** None

## Objective

Create the canonical repository structure.

## Required Deliverables

```text
backend/
frontend/
infrastructure/
contracts/
ADR/
ai_context/
README.md
```

## Acceptance Criteria

- [ ] repository builds from clean clone,
- [ ] backend and frontend directories exist,
- [ ] `.gitignore` configured,
- [ ] `.env.example` exists with placeholders only,
- [ ] no secrets committed.

---

# TASK FND-002 — Initialize Backend Application

**Priority:** P0  
**Owner:** Backend Agent  
**Dependencies:** FND-001

## Requirements

Supports foundation for all backend requirements.

## Deliverables

- FastAPI application,
- settings/config system,
- `/health/live`,
- `/health/ready`,
- structured logging,
- base `/api/v1` router.

## Acceptance Criteria

- [ ] backend starts locally,
- [ ] liveness returns 200,
- [ ] readiness validates database when configured,
- [ ] request IDs appear in logs.

---

# TASK FND-003 — Initialize Frontend Application

**Priority:** P0  
**Owner:** Frontend Agent  
**Dependencies:** FND-001

## Deliverables

- React + TypeScript + Vite,
- MUI setup,
- TanStack Query provider,
- Redux Toolkit store,
- router shell,
- basic authenticated/unauthenticated layouts.

## Acceptance Criteria

- [ ] frontend builds,
- [ ] strict TypeScript enabled,
- [ ] application shell renders,
- [ ] placeholder login route exists.

---

# TASK FND-004 — PostgreSQL and Alembic Setup

**Priority:** P0  
**Owner:** Database Agent  
**Dependencies:** FND-002

## Deliverables

- SQLAlchemy async/sync database configuration as approved,
- Alembic initialized,
- first migration infrastructure,
- local PostgreSQL connection.

## Acceptance Criteria

- [ ] migration upgrade succeeds on empty database,
- [ ] migration downgrade strategy documented,
- [ ] test database can be created automatically.

---

# TASK FND-005 — Local Docker Compose

**Priority:** P0  
**Owner:** DevOps Agent  
**Dependencies:** FND-002, FND-003, FND-004

## Services

```text
frontend
backend
postgres
minio
redis
```

## Acceptance Criteria

- [ ] one command starts development environment,
- [ ] frontend reaches backend,
- [ ] backend reaches PostgreSQL,
- [ ] backend reaches MinIO/Redis when required.

---

# TASK FND-006 — CI Baseline

**Priority:** P0  
**Owner:** DevOps Agent + QA Agent  
**Dependencies:** FND-002, FND-003, FND-004

## CI Stages

```text
backend lint/type-check
frontend lint/type-check
backend tests
frontend tests
migration test
secret scan
build
```

## Acceptance Criteria

- [ ] CI runs on pull request,
- [ ] failing tests block merge,
- [ ] migration-from-empty is tested.

---

# TASK FND-007 — Persian-First RTL Foundation

**Priority:** P0
**Owner:** Frontend Agent + Backend Agent + QA Agent
**Dependencies:** FND-003

## Deliverables

- `fa-IR` internationalization resource boundary,
- Persian application shell and placeholder routes,
- document and MUI RTL configuration,
- Persian-capable application font,
- centralized Persian safe API error messages,
- shared Persian search normalization utility,
- localization and RTL component/E2E tests.

## Acceptance Criteria

- [ ] document root uses `lang="fa"` and `dir="rtl"`,
- [ ] MUI theme, locale, and Emotion styles are configured for RTL,
- [ ] current user-facing copy is Persian and obtained through localization resources,
- [ ] API identifiers and error codes remain English while safe messages are Persian,
- [ ] Persian search normalization variants are unit tested,
- [ ] frontend lint, type check, tests, E2E, and build pass,
- [ ] backend lint, type check, and tests pass.

---

# 5. M1 — Identity, Workspace, and Security Foundation

# TASK AUTH-DB-001 — Identity Schema

**Priority:** P0  
**Owner:** Database Agent  
**Requirements:** AUTH-FR-001 through AUTH-FR-005  
**Dependencies:** FND-004

## Tables

```text
users
roles
permissions
user_roles
role_permissions
```

## Acceptance Criteria

- [ ] constraints match `03_DATABASE_SPECIFICATION.md`,
- [ ] initial roles/permissions seed idempotently.

---

# TASK AUTH-BE-001 — Authentication Service

**Priority:** P0  
**Owner:** Backend Agent  
**Requirements:** AUTH-FR-001, AUTH-FR-002, AUTH-FR-003  
**Dependencies:** AUTH-DB-001

## Deliverables

- login endpoint,
- logout behavior,
- current user endpoint,
- password hashing,
- JWT/session logic,
- login audit.

## Acceptance Criteria

- [ ] valid login succeeds,
- [ ] invalid login returns safe error,
- [ ] inactive user blocked,
- [ ] token expiration enforced,
- [ ] tests cover failures.

---

# TASK AUTH-BE-002 — Authorization Service

**Priority:** P0  
**Owner:** Backend Agent + Security Agent  
**Requirements:** AUTH-FR-004, AUTH-FR-005, SEC-FR-001  
**Dependencies:** AUTH-BE-001

## Deliverables

```text
AuthorizationService
permission dependency helpers
role resolution
```

## Acceptance Criteria

- [ ] protected endpoints reject missing permission,
- [ ] permission logic centralized,
- [ ] backend does not rely on frontend permission guards.

---

# TASK AUTH-FE-001 — Login and Auth Context

**Priority:** P0  
**Owner:** Frontend Agent  
**Dependencies:** AUTH-BE-001

## Deliverables

```text
LoginPage
AuthProvider
ProtectedRoute
UserMenu
```

## Acceptance Criteria

- [ ] login flow works,
- [ ] invalid login shown safely,
- [ ] authenticated routes protected,
- [ ] auth expiration handled globally.

---

# TASK WS-DB-001 — Workspace Schema

**Priority:** P0  
**Owner:** Database Agent  
**Requirements:** WS-FR-001 through WS-FR-003  
**Dependencies:** AUTH-DB-001

## Tables

```text
workspaces
workspace_memberships
```

---

# TASK WS-BE-001 — Workspace CRUD

**Priority:** P0  
**Owner:** Backend Agent  
**Requirements:** WS-FR-001, WS-FR-002, WS-FR-003  
**Dependencies:** WS-DB-001, AUTH-BE-002

## Endpoints

```text
POST /workspaces
GET /workspaces
GET /workspaces/{id}
PATCH /workspaces/{id}
GET /workspaces/{id}/members
POST /workspaces/{id}/members
DELETE /workspaces/{id}/members/{user_id}
```

## Acceptance Criteria

- [ ] inaccessible workspaces never appear in list,
- [ ] membership changes audited,
- [ ] cross-workspace access rejected.

---

# TASK WS-FE-001 — Workspace UI

**Priority:** P0  
**Owner:** Frontend Agent  
**Dependencies:** WS-BE-001

## Deliverables

```text
WorkspaceListPage
WorkspaceSelector
WorkspaceSettingsPage
WorkspaceMemberManager
```

---

# 6. M2 — Metadata and Generic Entity Platform

# TASK META-DB-001 — Metadata Schema

**Priority:** P0  
**Owner:** Database Agent  
**Requirements:** META-FR-001 through META-FR-009  
**Dependencies:** WS-DB-001

## Tables

```text
entity_types
attribute_definitions
```

---

# TASK META-BE-001 — Entity Type API

**Priority:** P0  
**Owner:** Backend Agent  
**Requirements:** META-FR-001, META-FR-002, META-FR-003  
**Dependencies:** META-DB-001, AUTH-BE-002

## Deliverables

- create/list/get/update/archive entity types,
- stable key validation,
- workspace isolation.

---

# TASK META-BE-002 — Attribute Definition API

**Priority:** P0  
**Owner:** Backend Agent  
**Requirements:** META-FR-004 through META-FR-009  
**Dependencies:** META-BE-001

## Acceptance Criteria

- [ ] supported types validated,
- [ ] duplicate keys rejected,
- [ ] enum config validated,
- [ ] invalid inheritance rejected.

---

# TASK META-BE-003 — Metadata Validation Engine

**Priority:** P0  
**Owner:** Backend Agent  
**Requirements:** META-FR-004 through META-FR-009  
**Dependencies:** META-BE-002

## Deliverable

Generic validator supporting:

```text
required
data type
enum membership
numeric/string constraints
reference existence
read-only enforcement
```

---

# TASK META-FE-001 — Metadata Administration

**Priority:** P0  
**Owner:** Frontend Agent  
**Dependencies:** META-BE-001, META-BE-002

## Deliverables

```text
EntityTypeList
EntityTypeEditor
AttributeDefinitionEditor
```

## Acceptance Criteria

- [ ] admin can create new entity type without code change,
- [ ] admin can add fields,
- [ ] no domain-specific UI.

---

# TASK ENT-DB-001 — Generic Entity Schema

**Priority:** P0  
**Owner:** Database Agent  
**Requirements:** ENT-FR-001 through ENT-FR-006  
**Dependencies:** META-DB-001

## Table

```text
entity_objects
```

## Acceptance Criteria

- [ ] JSONB attribute model implemented,
- [ ] required indexes present,
- [ ] no domain tables added.

---

# TASK ENT-BE-001 — Create Entity

**Priority:** P0  
**Owner:** Backend Agent  
**Requirements:** ENT-FR-001, META-FR-006, AUD-FR-001  
**Dependencies:** ENT-DB-001, META-BE-003

## Endpoint

```text
POST /workspaces/{workspace_id}/entities
```

## Acceptance Criteria

- [ ] generic entity created,
- [ ] dynamic attributes validated,
- [ ] invalid workspace/type rejected,
- [ ] audit record written.

---

# TASK ENT-BE-002 — Read/List/Search Entities

**Priority:** P0  
**Owner:** Backend Agent  
**Requirements:** ENT-FR-002, ENT-FR-005, ENT-FR-006  
**Dependencies:** ENT-BE-001

## Endpoints

```text
GET /entities/{id}
GET /workspaces/{workspace_id}/entities
```

---

# TASK ENT-BE-003 — Update/Archive Entity

**Priority:** P0  
**Owner:** Backend Agent  
**Requirements:** ENT-FR-003, ENT-FR-004  
**Dependencies:** ENT-BE-001

## Acceptance Criteria

- [ ] metadata validation enforced,
- [ ] version increments,
- [ ] stale version returns conflict,
- [ ] audit includes before/after state.

---

# TASK HIER-BE-001 — Hierarchy Retrieval

**Priority:** P0  
**Owner:** Backend Agent + Database Agent  
**Requirements:** HIER-FR-001, HIER-FR-005  
**Dependencies:** ENT-DB-001

## Deliverable

Recursive CTE-based hierarchy retrieval.

## Acceptance Criteria

- [ ] no N+1 hierarchy traversal,
- [ ] workspace filter enforced,
- [ ] deleted entities excluded.

---

# TASK HIER-BE-002 — Reparent and Cycle Prevention

**Priority:** P0  
**Owner:** Backend Agent + Database Agent  
**Requirements:** HIER-FR-002, HIER-FR-003, HIER-FR-004, HIER-FR-007  
**Dependencies:** HIER-BE-001

## Acceptance Criteria

- [ ] same-workspace rule enforced,
- [ ] self-parent rejected,
- [ ] cycles rejected,
- [ ] audit emitted.

---

# TASK ENT-FE-001 — Entity Tree Viewer

**Priority:** P0  
**Owner:** Frontend Agent  
**Requirements:** HIER-FR-001 through HIER-FR-006  
**Dependencies:** HIER-BE-001

## Deliverable

Generic lazy-loaded `EntityTreeViewer`.

---

# TASK ENT-FE-002 — Generic Entity Detail Page

**Priority:** P0  
**Owner:** Frontend Agent  
**Requirements:** ENT-FR-002  
**Dependencies:** ENT-BE-002

## Tabs

```text
Overview
Information
Forms
Documents
Relationships
History
```

---

# TASK REL-DB-001 — Relationship Schema

**Priority:** P0  
**Owner:** Database Agent  
**Requirements:** REL-FR-001 through REL-FR-005  
**Dependencies:** ENT-DB-001

## Tables

```text
relationship_types
entity_relationships
```

---

# TASK REL-BE-001 — Relationship API

**Priority:** P0  
**Owner:** Backend Agent  
**Dependencies:** REL-DB-001

## Deliverables

- relationship type CRUD,
- create relationship,
- list incoming/outgoing,
- delete relationship.

---

# TASK REL-FE-001 — Relationship Panel

**Priority:** P0  
**Owner:** Frontend Agent  
**Dependencies:** REL-BE-001

---

# 7. M3 — Dynamic Forms and Structured Data

# TASK FORM-DB-001 — Form Schema

**Priority:** P0  
**Owner:** Database Agent  
**Requirements:** FORM-FR-001 through FORM-FR-012  
**Dependencies:** META-DB-001, ENT-DB-001

## Tables

```text
form_definitions
form_fields
form_instances
```

---

# TASK FORM-BE-001 — Draft Form Definition API

**Priority:** P0  
**Owner:** Backend Agent  
**Requirements:** FORM-FR-001, FORM-FR-002, FORM-FR-003  
**Dependencies:** FORM-DB-001

---

# TASK FORM-BE-002 — Form Publish and Versioning

**Priority:** P1  
**Owner:** Backend Agent  
**Requirements:** FORM-FR-011, FORM-FR-012  
**Dependencies:** FORM-BE-001

## Acceptance Criteria

- [ ] published form immutable,
- [ ] new-version flow creates draft copy,
- [ ] historical instance remains tied to old version.

---

# TASK FORM-BE-003 — Form Rule Evaluator

**Priority:** P0  
**Owner:** Backend Agent  
**Requirements:** FORM-FR-004, FORM-FR-007, FORM-FR-008, FORM-FR-009  
**Dependencies:** FORM-BE-001

## Features

```text
visibility
read-only
inheritance
conditional requirement
```

Arbitrary code execution prohibited.

---

# TASK FORM-BE-004 — Render Contract

**Priority:** P0  
**Owner:** Backend Agent  
**Requirements:** FORM-FR-003 through FORM-FR-010  
**Dependencies:** FORM-BE-003

## Endpoint

```text
GET /forms/{form_id}/render
```

---

# TASK DATA-BE-001 — Create/Save Form Instance

**Priority:** P0  
**Owner:** Backend Agent  
**Requirements:** DATA-FR-001, DATA-FR-002, DATA-FR-004  
**Dependencies:** FORM-BE-004

---

# TASK DATA-BE-002 — Submit Form Instance

**Priority:** P0  
**Owner:** Backend Agent  
**Requirements:** DATA-FR-004, DATA-FR-005  
**Dependencies:** DATA-BE-001

## Acceptance Criteria

- [ ] server validation authoritative,
- [ ] locked resources rejected,
- [ ] exact form version retained,
- [ ] audit generated.

---

# TASK FORM-FE-001 — Dynamic Field Renderer

**Priority:** P0  
**Owner:** Frontend Agent  
**Dependencies:** FORM-BE-004

## Supported Field Types

```text
TEXT
RICH_TEXT
INTEGER
DECIMAL
BOOLEAN
DATE
DATETIME
ENUM
MULTI_ENUM
USER_REFERENCE
ENTITY_REFERENCE
FILE_REFERENCE
TABLE
```

---

# TASK FORM-FE-002 — Dynamic Form Renderer

**Priority:** P0  
**Owner:** Frontend Agent  
**Dependencies:** FORM-FE-001, DATA-BE-001

## Acceptance Criteria

- [ ] consumes render contract,
- [ ] inherited values displayed,
- [ ] backend errors mapped to fields,
- [ ] no domain-specific branches.

---

# TASK FORM-FE-003 — Dynamic Repeating Table

**Priority:** P0  
**Owner:** Frontend Agent  
**Requirements:** FORM-FR-005, FORM-FR-006  
**Dependencies:** FORM-FE-001

---

# TASK FORM-FE-004 — Form Designer MVP

**Priority:** P0  
**Owner:** Frontend Agent  
**Dependencies:** FORM-BE-001

## MVP Scope

- add sections,
- add fields,
- configure options,
- configure required/read-only,
- configure inheritance,
- preview.

Drag-and-drop is optional.

---

# TASK FORM-FE-005 — Publish/New Version UI

**Priority:** P1  
**Owner:** Frontend Agent  
**Dependencies:** FORM-BE-002

---

# 8. M4 — Documents and Import

# TASK DOC-DB-001 — Document Schema

**Priority:** P0  
**Owner:** Database Agent  
**Requirements:** DOC-FR-001 through DOC-FR-009  
**Dependencies:** ENT-DB-001

## Tables

```text
documents
document_versions
```

---

# TASK DOC-BE-001 — Storage Provider Abstraction

**Priority:** P0  
**Owner:** Document Agent  
**Dependencies:** FND-005

## Deliverables

```text
StorageProvider
MinioStorageProvider
```

---

# TASK DOC-BE-002 — Upload First Document Version

**Priority:** P0  
**Owner:** Document Agent + Backend Agent  
**Dependencies:** DOC-DB-001, DOC-BE-001

## Acceptance Criteria

- [ ] file metadata validated,
- [ ] safe object key generated,
- [ ] version 1 created,
- [ ] audit emitted.

---

# TASK DOC-BE-003 — Add Document Version

**Priority:** P0  
**Owner:** Document Agent  
**Dependencies:** DOC-BE-002

## Acceptance Criteria

- [ ] old version preserved,
- [ ] new immutable version created,
- [ ] current version updated safely.

---

# TASK DOC-BE-004 — Download Access

**Priority:** P0  
**Owner:** Document Agent + Security Agent  
**Dependencies:** DOC-BE-002

## Deliverable

Authorized streaming or presigned short-lived access.

---

# TASK DOC-BE-005 — Preview Workflow

**Priority:** P0 for PDF/images, P1 for Office  
**Owner:** Document Agent  
**Dependencies:** DOC-BE-002

---

# TASK DOC-BE-006 — Malware Scan Workflow

**Priority:** P1  
**Owner:** Document Agent + Security Agent  
**Dependencies:** DOC-BE-002

---

# TASK DOC-FE-001 — Document Panel

**Priority:** P0  
**Owner:** Frontend Agent  
**Dependencies:** DOC-BE-002, DOC-BE-003

---

# TASK DOC-FE-002 — Preview and Version History UI

**Priority:** P0  
**Owner:** Frontend Agent  
**Dependencies:** DOC-BE-004, DOC-BE-005

---

# TASK IMP-DB-001 — Import Schema

**Priority:** P0  
**Owner:** Database Agent  
**Requirements:** IMP-FR-001 through IMP-FR-012  
**Dependencies:** ENT-DB-001

## Tables

```text
import_profiles
import_mappings
import_jobs
import_conflicts
```

---

# TASK IMP-BE-001 — XLSX/CSV Parser

**Priority:** P0  
**Owner:** Import Agent  
**Dependencies:** IMP-DB-001

## Acceptance Criteria

- [ ] sheet/column inspection works,
- [ ] CSV supported,
- [ ] XLSX supported,
- [ ] large-file strategy documented.

---

# TASK IMP-BE-002 — Import Profiles and Mapping

**Priority:** P0  
**Owner:** Import Agent  
**Dependencies:** IMP-BE-001, META-BE-003

---

# TASK IMP-BE-003 — Matching Strategy

**Priority:** P0  
**Owner:** Import Agent  
**Dependencies:** IMP-BE-002

## Features

Support configured:

```text
entity ID
unique attribute
composite key
parent + key
```

---

# TASK IMP-BE-004 — Dry Run

**Priority:** P0  
**Owner:** Import Agent  
**Requirements:** IMP-FR-005 through IMP-FR-007  
**Dependencies:** IMP-BE-003

## Acceptance Criteria

- [ ] canonical entity data unchanged,
- [ ] create/update/unchanged classified,
- [ ] validation errors returned,
- [ ] conflicts persisted/reported.

---

# TASK IMP-BE-005 — Conflict Resolution

**Priority:** P0  
**Owner:** Import Agent  
**Dependencies:** IMP-BE-004

## Actions

```text
MERGE
REPLACE
SKIP
```

---

# TASK IMP-BE-006 — Transactional Commit

**Priority:** P0  
**Owner:** Import Agent + Backend Agent  
**Requirements:** IMP-FR-008 through IMP-FR-011  
**Dependencies:** IMP-BE-005

## Acceptance Criteria

- [ ] dry run required,
- [ ] unresolved required conflicts block commit,
- [ ] idempotency implemented,
- [ ] transaction rollback on failure,
- [ ] audit summary written.

---

# TASK IMP-FE-001 — Import Wizard Upload/Inspect

**Priority:** P0  
**Owner:** Frontend Agent  
**Dependencies:** IMP-BE-001

---

# TASK IMP-FE-002 — Mapping UI

**Priority:** P0  
**Owner:** Frontend Agent  
**Dependencies:** IMP-BE-002

---

# TASK IMP-FE-003 — Dry-Run Summary UI

**Priority:** P0  
**Owner:** Frontend Agent  
**Dependencies:** IMP-BE-004

---

# TASK IMP-FE-004 — Conflict Resolver UI

**Priority:** P0  
**Owner:** Frontend Agent  
**Dependencies:** IMP-BE-005

---

# TASK IMP-FE-005 — Commit Confirmation and Summary

**Priority:** P0  
**Owner:** Frontend Agent  
**Dependencies:** IMP-BE-006

---

# 9. M5 — Phase Control, Review, Audit, Dashboard

# TASK PHASE-DB-001 — Phase Schema

**Priority:** P0  
**Owner:** Database Agent  
**Requirements:** PHASE-FR-001 through PHASE-FR-008  
**Dependencies:** WS-DB-001

## Tables

```text
phases
phase_deliverables
```

---

# TASK PHASE-BE-001 — Phase CRUD

**Priority:** P0  
**Owner:** Backend Agent  
**Dependencies:** PHASE-DB-001

---

# TASK PHASE-BE-002 — Lock Policy Service

**Priority:** P0  
**Owner:** Backend Agent + Security Agent  
**Dependencies:** PHASE-BE-001

## Acceptance Criteria

- [ ] lock enforced server-side,
- [ ] shared policy used,
- [ ] unlock permission explicit,
- [ ] lock/unlock audited.

---

# TASK PHASE-FE-001 — Phase UI

**Priority:** P0  
**Owner:** Frontend Agent  
**Dependencies:** PHASE-BE-001, PHASE-BE-002

---

# TASK REV-DB-001 — Review Comment Schema

**Priority:** P1  
**Owner:** Database Agent  
**Requirements:** REV-FR-001 through REV-FR-004

---

# TASK REV-BE-001 — Review Comment API

**Priority:** P1  
**Owner:** Backend Agent  
**Dependencies:** REV-DB-001

---

# TASK REV-FE-001 — Review UI

**Priority:** P1  
**Owner:** Frontend Agent  
**Dependencies:** REV-BE-001

---

# TASK AUD-DB-001 — Audit Schema

**Priority:** P0  
**Owner:** Database Agent  
**Requirements:** AUD-FR-001 through AUD-FR-004

---

# TASK AUD-BE-001 — Audit Service

**Priority:** P0  
**Owner:** Backend Agent + Security Agent  
**Dependencies:** AUD-DB-001

## Acceptance Criteria

- [ ] append-only behavior,
- [ ] all material mutations covered,
- [ ] sensitive values excluded.

---

# TASK AUD-BE-002 — Audit Query API

**Priority:** P1  
**Owner:** Backend Agent  
**Dependencies:** AUD-BE-001

---

# TASK AUD-FE-001 — Audit Viewer

**Priority:** P1  
**Owner:** Frontend Agent  
**Dependencies:** AUD-BE-002

---

# TASK RPT-DB-001 — Dashboard Schema

**Priority:** P0  
**Owner:** Database Agent  
**Requirements:** RPT-FR-001 through RPT-FR-005

---

# TASK RPT-BE-001 — Basic KPI Dashboard API

**Priority:** P0  
**Owner:** Backend Agent  
**Dependencies:** RPT-DB-001

## MVP KPIs

```text
entity count
document count
phase completion
pending deliverables
```

---

# TASK RPT-FE-001 — Dashboard Viewer

**Priority:** P0  
**Owner:** Frontend Agent  
**Dependencies:** RPT-BE-001

---

# TASK RPT-BE-002 — Configurable Dashboard Query Builder

**Priority:** P1  
**Owner:** Backend Agent  
**Dependencies:** RPT-BE-001

Arbitrary browser SQL prohibited.

---

# TASK RPT-FE-002 — Dashboard Builder

**Priority:** P1  
**Owner:** Frontend Agent  
**Dependencies:** RPT-BE-002

---

# 10. M6 — Production Hardening

# TASK SEC-001 — Security Review Baseline

**Priority:** P0 before production  
**Owner:** Security Agent  
**Dependencies:** Core MVP functionality

Review:

```text
authentication
authorization
workspace isolation
file upload
imports
CORS
secrets
XSS
object storage access
audit coverage
```

---

# TASK QA-001 — MVP End-to-End Regression

**Priority:** P0  
**Owner:** QA Agent  
**Dependencies:** M0-M5 P0 tasks

Scenario:

```text
login
→ workspace
→ metadata
→ entity hierarchy
→ dynamic form
→ document version
→ Excel import
→ conflict resolution
→ phase lock
→ rejected locked edit
```

---

# TASK PERF-001 — Database Query Review

**Priority:** P1  
**Owner:** Database Agent + Backend Agent

Review:

- entity list,
- tree query,
- relationship query,
- form rendering,
- audit query,
- dashboard query.

---

# TASK OBS-001 — Production Observability

**Priority:** P1  
**Owner:** DevOps Agent + Backend Agent

Deliver:

```text
structured logs
health/readiness
metrics
request IDs
error monitoring hooks
```

---

# TASK DR-001 — Backup and Restore Procedure

**Priority:** P1  
**Owner:** DevOps Agent + Database Agent

Acceptance:

- [ ] PostgreSQL backup documented,
- [ ] restore tested,
- [ ] object storage backup/replication documented.

---

# TASK DEP-001 — Production Deployment Pipeline

**Priority:** P1  
**Owner:** DevOps Agent  
**Dependencies:** SEC-001, QA-001

---

# 11. M7 — AI Enhancements

# TASK AI-001 — AI Architecture ADR

**Priority:** P2  
**Owner:** Architecture Agent

Before implementing runtime AI features, define:

- model provider abstraction,
- data privacy model,
- prompt/version storage,
- cost controls,
- auditability.

---

# TASK AI-002 — Document Extraction Assistant

**Priority:** P2  
**Owner:** Future AI Agent + Document Agent

Capabilities MAY include:

- extract candidate entities,
- extract stakeholder rows,
- extract risk rows,
- propose form values.

AI output SHALL require user review before persistence.

---

# TASK AI-003 — Natural Language Enterprise Assistant

**Priority:** P2  
**Owner:** Future AI Agent

The assistant SHALL use authorized platform APIs/query services.

It SHALL NOT bypass workspace/object-level permissions.

---

# TASK AI-004 — Import Mapping Suggestions

**Priority:** P2  
**Owner:** Future AI Agent + Import Agent

AI MAY suggest column mappings with confidence scores.

User approval remains required.

---

# 12. Cross-Cutting Test Tasks

# TASK TEST-AUTH-001

Test authentication and authorization failure matrix.

---

# TASK TEST-WS-001

Test workspace isolation across all core resources.

---

# TASK TEST-HIER-001

Test hierarchy cycle cases:

```text
self parent
child → ancestor
deep cycle
cross-workspace parent
```

---

# TASK TEST-FORM-001

Test all supported field render/validation types.

---

# TASK TEST-DOC-001

Test immutable version history and unauthorized download.

---

# TASK TEST-IMP-001

Test:

```text
dry run no mutation
MERGE
REPLACE
SKIP
rollback
duplicate commit
```

---

# TASK TEST-LOCK-001

Test locked resources across:

```text
entity update
form save
document mutation where applicable
hierarchy move
```

---

# 13. Parallelization Guidance

Safe early parallel work:

```text
FND-002 backend bootstrap
FND-003 frontend bootstrap
FND-004 DB setup
```

After contracts stabilize:

```text
backend entity APIs
frontend shell/tree
database relationship migration
```

Do not parallelize frontend/backend against undefined payload contracts.

---

# 14. Critical Path

Recommended critical path:

```text
FND-001
→ FND-002/FND-003/FND-004
→ AUTH
→ WORKSPACE
→ METADATA
→ ENTITY
→ HIERARCHY
→ FORMS
→ DOCUMENTS
→ IMPORT
→ PHASE LOCK
→ DASHBOARD
→ QA/SECURITY
→ PRODUCTION
```

---

# 15. MVP Exit Criteria

The MVP milestone is complete only when:

- [ ] user can authenticate,
- [ ] workspace isolation works,
- [ ] admin can define arbitrary entity types,
- [ ] analyst can create arbitrary hierarchy,
- [ ] dynamic form renders from metadata,
- [ ] inherited values work,
- [ ] repeating tables work,
- [ ] documents support version history,
- [ ] Excel/CSV import supports dry run,
- [ ] conflicts require explicit resolution,
- [ ] commit is transactional,
- [ ] manager can lock phase,
- [ ] locked edits are rejected server-side,
- [ ] dashboard displays basic KPIs,
- [ ] audit records material mutations,
- [ ] E2E suite passes,
- [ ] security review has no unresolved critical finding.

---

# 16. Task Completion Record Template

Each completed task SHALL record:

```text
TASK_ID:
STATUS:
COMPLETED_BY:
REQUIREMENTS:
FILES_CHANGED:
MIGRATIONS:
API_CHANGES:
TESTS:
TEST_RESULTS:
SECURITY_REVIEW:
KNOWN_LIMITATIONS:
FOLLOW_UP_TASKS:
```

---

# 17. Related Specifications

```text
00_PROJECT_CONTEXT.md
01_ARCHITECTURE_RULES.md
02_SYSTEM_REQUIREMENTS.md
03_DATABASE_SPECIFICATION.md
04_API_SPECIFICATION.md
05_BACKEND_SPECIFICATION.md
06_FRONTEND_SPECIFICATION.md
07_AI_AGENT_ROLES.md
09_TEST_SPECIFICATION.md
10_DEPLOYMENT_GUIDE.md
11_SECURITY_SPECIFICATION.md
12_CURRENT_STATUS.md
```
