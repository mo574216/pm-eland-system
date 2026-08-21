# Project Context

**File:** `00_PROJECT_CONTEXT.md`  
**Status:** Normative Context  
**System:** Metadata-Driven Enterprise Architecture Management Platform  
**Version:** 1.0  
**Audience:** Human developers, AI coding agents, architects, QA, security, DevOps

---

# 1. Purpose

This document defines the project mission, problem statement, product boundaries, operating assumptions, users, architectural intent, and implementation philosophy.

All implementation agents SHALL read this file together with:

```text
01_ARCHITECTURE_RULES.md
12_CURRENT_STATUS.md
```

before starting work.

This file provides context. Where exact implementation rules are required, the corresponding normative specification takes precedence.

---

# 2. Project Mission

Build a configurable enterprise architecture and project knowledge platform that allows organizations to manage structured project information, documents, hierarchy, reviews, imports, and reporting without hard-coding business-domain concepts into software.

The platform SHALL support arbitrary enterprise architecture and consulting use cases through metadata.

Core principle:

> **Domain concepts are configuration data, not application code.**

---

# 3. Problem Statement

Enterprise architecture and transformation projects commonly distribute information across:

- Excel workbooks,
- CSV files,
- Word documents,
- PDFs,
- images,
- BPMN diagrams,
- Visual Paradigm/model files,
- manually maintained reports,
- disconnected folders.

This causes:

- duplication,
- inconsistent versions,
- weak traceability,
- difficult reporting,
- difficult review,
- repeated manual data entry,
- poor visibility of project progress.

The system addresses these problems by combining:

```text
structured metadata
+ generic entity hierarchy
+ dynamic forms
+ document repository
+ import workflows
+ phase control
+ relationships
+ dashboards
+ audit trail
```

---

# 4. Product Vision

The product should behave as a configurable knowledge platform rather than a fixed business application.

Administrators can define:

```text
entity types
attributes
forms
hierarchies
relationships
import profiles
phases
dashboards
```

without requiring software changes.

Example configurations may include:

```text
Umbrella Project
└── Subproject
    └── Company
        └── Business Service
            └── Business Process
```

or:

```text
Enterprise Architecture
├── Business Layer
├── Application Layer
├── Data Layer
└── Technology Layer
```

These examples are not hard-coded structures.

---

# 5. Primary Use Cases

## UC-001 — Enterprise Architecture Repository

Store enterprise architecture entities and relationships across arbitrary layers.

---

## UC-002 — Process Analysis

Capture:

```text
process properties
inputs
activities
outputs
timers
stakeholders
risks
control points
improvement opportunities
related services
documents
```

through dynamic metadata/forms.

---

## UC-003 — Project Deliverable Monitoring

Define:

```text
phases
deliverables
completion state
reviews
locks
```

without implementing full project scheduling/resource management.

---

## UC-004 — Existing Excel Migration

Import current structured spreadsheets into the platform through reusable mappings.

---

## UC-005 — Offline-to-Online Data Collection

Users can prepare Excel/CSV offline and later upload, validate, preview, resolve conflicts, and commit.

---

## UC-006 — Document Repository

Store and version:

```text
PDF
DOCX
XLSX
CSV
PNG
JPEG
SVG
BPMN/XML
Visual Paradigm/model binaries
other project files
```

---

## UC-007 — Management Reporting

Managers can inspect:

```text
phase progress
entity counts
deliverables
structured attributes
documents
relationships
```

through dashboards and reports.

---

# 6. User Roles

Initial roles:

## System Administrator

Responsible for:

- users,
- roles,
- permissions,
- metadata,
- forms,
- system configuration.

## Project Manager / Employer Representative

Responsible for:

- monitoring,
- review,
- dashboards,
- deliverables,
- phase locking/unlocking.

## Analyst / Designer

Responsible for:

- structured data entry,
- entities,
- documents,
- Excel/CSV import,
- revisions.

## Viewer

Read-only access to authorized content.

---

# 7. Functional Capability Map

The system consists of these logical engines:

```text
Identity & Access Engine
Workspace Engine
Metadata Engine
Entity Engine
Hierarchy Engine
Relationship Engine
Dynamic Form Engine
Document Engine
Import Engine
Phase / Lock Engine
Review Engine
Reporting Engine
Audit Engine
Background Job Engine
```

---

# 8. Non-Goals

The product is NOT intended to become a general-purpose project management suite.

MVP SHALL NOT include unless separately approved:

```text
resource allocation
budget management
timesheets
payroll
team chat
real-time collaboration
Gantt scheduling
CRM
billing/subscriptions
```

---

# 9. Domain-Agnostic Requirement

The following are examples of configuration only:

```text
Business Process
Business Service
Application
Server
Database
Stakeholder
Risk
Technology Component
```

No implementation agent may infer that these require dedicated tables/pages/models.

Correct interpretation:

```text
EntityType("Business Process")
```

Incorrect interpretation:

```text
class BusinessProcess(...)
```

---

# 10. Hierarchy Model

Hierarchy SHALL support arbitrary depth.

Example:

```text
A
└── B
    └── C
        └── D
            └── ...
```

The application SHALL not hard-code maximum business hierarchy levels.

---

# 11. Structured Data Philosophy

Files alone are insufficient.

Important project information SHALL be queryable as structured records.

Examples:

```text
owner
status
risk level
stakeholder role
process input
process output
control point
system dependency
```

Dynamic metadata and forms define these values.

---

# 12. Dynamic Form Philosophy

Administrators SHALL be able to build forms that support:

```text
simple fields
sections
conditional visibility
validation
default values
inherited values
repeating rows
dynamic columns
references
```

The frontend SHALL render these forms generically.

---

# 13. Parent Inheritance

Child entities/forms may inherit values from parent/context.

Examples:

```text
Service ID → Process Specification
Service Name → Process Specification
Organization → Service Form
```

Inheritance SHALL be metadata-defined, not hard-coded.

---

# 14. Document Philosophy

A logical document may have multiple immutable versions.

Example:

```text
Process Report
├── v1
├── v2
└── v3 current
```

Users may inspect historical versions.

---

# 15. Import Philosophy

Import is a safety-critical workflow.

Required high-level lifecycle:

```text
Upload
→ Analyze
→ Map
→ Validate
→ Dry Run
→ Diff
→ Conflict Resolution
→ Commit
→ Audit
```

The system SHALL never silently overwrite existing canonical information.

---

# 16. Phase / Lock Philosophy

Completed phases may be locked.

Normal users cannot mutate locked content.

Authorized managers may unlock when necessary.

This is not merely a UI rule; backend enforcement is mandatory.

---

# 17. Review Philosophy

Managers should be able to:

```text
review
comment
request revision
approve where configured
```

Historical versions/audit SHALL remain available.

---

# 18. Technology Direction

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
MUI
TanStack Query
Redux Toolkit
React Hook Form
Zod
```

Storage:

```text
MinIO / S3-compatible
```

Background work:

```text
Redis
Celery or approved equivalent
```

Deployment:

```text
Docker Compose initially
Kubernetes only when justified
```

## 18.1 Language and Localization Direction

The product is Persian-first. Persian/Farsi (`fa-IR`) SHALL be the primary
user-facing language for the MVP, and the primary application layout direction
SHALL be right-to-left (RTL).

The localization boundary is:

> **Developer-facing contracts are English; the entire end-user interface is Persian and RTL.**

English SHALL remain the internal technical language for source-code identifiers,
API field names, stable error codes, database identifiers, logs, and developer
documentation. User-authored and metadata-configured values MAY contain Persian
Unicode. User-facing labels, validation messages, notifications, empty states,
and safe API error messages SHALL be Persian and SHALL come from localization or
metadata resources rather than being scattered through business logic.

The frontend SHALL retain an internationalization framework even while Persian
is the only mandatory MVP locale. This preserves a clean translation boundary
without weakening the Persian-first requirement.

---

# 19. Development Philosophy

The codebase SHALL be:

```text
metadata-driven
API-first
modular
domain-agnostic
testable
secure by default
AI-agent friendly
```

---

# 20. AI-Agent Development Philosophy

AI coding agents are expected to implement much of the system.

Therefore specifications SHALL provide:

- stable task IDs,
- exact boundaries,
- acceptance criteria,
- API contracts,
- schema constraints,
- review gates,
- prohibited anti-patterns.

Agents SHALL not improvise product architecture where documentation exists.

---

# 21. MVP Success Scenario

The MVP is successful when:

```text
Admin logs in
→ creates workspace
→ creates arbitrary entity types
→ defines dynamic attributes/forms
→ Analyst builds hierarchy
→ Analyst fills dynamic form
→ Parent values are inherited
→ Analyst uploads document versions
→ Analyst imports Excel
→ Dry run detects differences
→ Analyst resolves conflicts
→ Import commits transactionally
→ Manager views dashboard
→ Manager locks completed phase
→ Analyst edit is rejected
→ Audit trail proves actions
```

---

# 22. Future AI Vision

Potential future AI capabilities include:

```text
document extraction
automatic metadata suggestions
import mapping suggestions
enterprise Q&A
semantic search
report drafting
relationship discovery
```

These are deferred until a separate AI architecture/security ADR is approved.

---

# 23. Core Product Invariant

All contributors SHALL preserve:

> **The platform is metadata-driven. Domain concepts are data, not code.**

---

# 24. Related Specifications

```text
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
contracts/
ADR/
```
