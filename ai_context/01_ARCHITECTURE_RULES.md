# Architecture & Agent Rules

**File:** `01_ARCHITECTURE_RULES.md`  
**Status:** Normative  
**Applies to:** All human developers, AI coding agents, reviewers, CI checks, migration authors, and deployment agents  
**Precedence:** These rules override implementation convenience unless superseded by an approved Architecture Decision Record (ADR).

---

# 1. Purpose

This document defines mandatory architectural constraints for the Metadata-Driven Enterprise Architecture Management Platform.

The platform is intended to support arbitrary enterprise domains, including but not limited to:

- business architecture,
- business services,
- business processes,
- application architecture,
- information/data architecture,
- technology architecture,
- infrastructure architecture,
- transformation programs,
- organizational structures,
- project deliverables.

None of these concepts may be embedded as fixed software-domain models.

The central architectural principle is:

> **Domain concepts are configuration data, not application code.**

Any implementation that violates this principle must be rejected during code review.

---

# 2. Requirement Language

The terms below are normative:

- **MUST / SHALL** — mandatory requirement.
- **MUST NOT / SHALL NOT** — prohibited implementation.
- **SHOULD** — strongly recommended; deviation requires justification.
- **MAY** — optional implementation.

---

# 3. Golden Rule 1 — Zero Domain-Specific Persistence Models

## 3.1 Rule

The application MUST NOT create dedicated database tables, ORM classes, repositories, services, or migrations for user-configurable enterprise concepts.

### Prohibited examples

```text
business_processes
business_services
applications
servers
databases
stakeholders
risks
technology_components
requirements
```

Likewise, these ORM models are prohibited:

```python
class BusinessProcess(...)
class BusinessService(...)
class Application(...)
class Server(...)
```

## 3.2 Required Mechanism

All user-defined domain objects SHALL be represented through the generic entity model:

```text
entity_types
entity_objects
attribute_definitions
entity_attribute_values
relationship_types
entity_relationships
```

For example:

```text
entity_types
-------------
id: <uuid>
name: "Business Process"
```

and:

```text
entity_objects
--------------
id: <uuid>
entity_type_id: <Business Process type UUID>
name: "Certificate Verification"
```

A new enterprise concept therefore requires metadata creation rather than a schema migration.

## 3.3 Attribute Storage

Dynamic attributes MUST be represented through the approved metadata/value architecture defined in:

`03_DATABASE_SPECIFICATION.md`

Agents MUST NOT introduce arbitrary fixed columns such as:

```text
process_owner
risk_level
application_version
server_ip
```

into `entity_objects`.

## 3.4 Acceptance Test

A system administrator SHALL be able to define a new entity type called:

```text
Network Security Zone
```

with attributes:

```text
Name
Security Level
Owner
Description
```

without:

- modifying Python code,
- modifying TypeScript code,
- creating a database migration,
- creating an ORM class,
- redeploying the backend.

---

# 4. Golden Rule 2 — Generic UI Only

## 4.1 Rule

Frontend components SHALL NOT encode domain-specific enterprise concepts.

### Prohibited

```text
BusinessProcessForm.tsx
ServiceDetailPage.tsx
ServerView.tsx
ApplicationEditor.tsx
RiskAnalysisPage.tsx
```

### Required generic components

Examples include:

```text
EntityTreeViewer
EntityDetailPage
DynamicFormRenderer
DynamicFieldRenderer
DynamicTableField
RelationshipPanel
DocumentPanel
ImportWizard
MetadataDesigner
FormDesigner
```

See:

`06_FRONTEND_SPECIFICATION.md`

## 4.2 Mechanism

The frontend SHALL determine rendering behavior from API-provided metadata.

Example API metadata:

```json
{
  "key": "risk_level",
  "label": "Risk Level",
  "data_type": "ENUM",
  "required": true,
  "configuration": {
    "options": [
      "Low",
      "Medium",
      "High"
    ]
  }
}
```

The frontend SHALL render the corresponding control without knowing that the field belongs to a business process, application, server, or any other domain concept.

## 4.3 Prohibited Logic

This is prohibited:

```typescript
if (entity.type === "Business Process") {
  return <BusinessProcessForm />;
}
```

The required pattern is:

```typescript
return <DynamicFormRenderer definition={formDefinition} />;
```

## 4.4 Acceptance Test

After an administrator defines a new entity type and form, the frontend SHALL be capable of displaying and editing it without recompilation.

---

# 5. Golden Rule 3 — Generic Hierarchy

## 5.1 Rule

The platform SHALL NOT assume a predefined hierarchy.

It must support structures such as:

```text
Organization
└── Program
    └── Project
        └── Business Service
            └── Business Process
```

but also:

```text
Portfolio
└── Architecture Domain
    └── Platform
        └── Infrastructure Element
```

and any other administrator-defined structure.

## 5.2 Persistence

Hierarchical containment SHALL use generic entity relationships, primarily:

```text
entity_objects.parent_id
```

unless an approved later design introduces a dedicated hierarchy relationship mechanism.

## 5.3 Depth

The system MUST NOT impose an application-level maximum hierarchy depth.

Practical database and API safeguards MAY limit pathological requests, but the domain model remains unbounded.

## 5.4 Tree Queries

Hierarchy traversal SHALL occur using database-level operations such as PostgreSQL recursive CTEs.

### Prohibited

Fetching all entities and recursively constructing hierarchy relationships through repeated Python database calls.

### Preferred

```sql
WITH RECURSIVE entity_tree AS (...)
```

See:

`03_DATABASE_SPECIFICATION.md`

## 5.5 Cycle Protection

The backend MUST reject hierarchy mutations that would create cycles.

For example:

```text
A → B → C
```

must reject:

```text
C → A
```

---

# 6. Golden Rule 4 — Metadata Controls Behavior

Metadata SHALL be the source of truth for configurable behavior.

Metadata may define:

- entity types,
- attributes,
- labels,
- ordering,
- required fields,
- allowed values,
- validation rules,
- visibility conditions,
- default values,
- inherited values,
- relationship constraints,
- form definitions,
- repeating sections,
- table columns.

Backend and frontend code SHALL implement generic engines that interpret this metadata.

## 6.1 Human Interaction Boundary

Metadata drives behavior but its storage vocabulary SHALL NOT dictate primary UX.
The normal interface uses user goals, Persian domain labels, searchable named
selectors, sensible defaults, contextual help, and progressive disclosure.

The following are integration/advanced concepts and SHALL not be mandatory raw input
in ordinary workflows:

```text
UUIDs and foreign keys
stable technical keys
storage/object keys
relationship source/target direction
cardinality codes
matching-strategy payloads
workflow/configuration JSON
```

Technical keys SHALL be server-generated by default and shown only where advanced
configuration, diagnostics, or integration requires them. APIs still use stable IDs;
the frontend resolves them through authorized human-readable selectors.

Operational capabilities SHALL be invoked in their work context. In particular,
import is launched from an eligible phase/deliverable/form/output specification and
inherits known target context; it is not an ordinary top-level project destination.
See ADR-0007.

---

# 7. Golden Rule 5 — Form Definitions Are Versioned

Published form definitions MUST be immutable.

Editing an already published form SHALL create a new definition version.

Example:

```text
Process Specification Form
v1 — retired
v2 — current
v3 — draft
```

Historical form instances MUST retain the identifier/version of the definition under which they were created.

An agent MUST NOT modify a published form definition in place if doing so could alter interpretation of historical data.

---

# 8. Golden Rule 6 — Parent/Child Inheritance Is Configured

Automatic field population from parent entities SHALL NOT be hard-coded.

Example requirement:

```text
Service ID → Process Specification.Service ID
Service Name → Process Specification.Service Name
```

must be represented through metadata such as:

```json
{
  "source": {
    "scope": "parent",
    "attribute": "service_id"
  },
  "target_field": "service_id",
  "mode": "prefill"
}
```

The exact schema is defined in the form/metadata specification.

The application MUST support:

- inherited read-only values,
- inherited editable defaults,
- explicitly copied values where configured.

## 8.1 Reference and Snapshot Semantics

Every reusable-value binding SHALL explicitly distinguish:

```text
LIVE_REFERENCE
READ_ONLY_INHERITED
EDITABLE_SUGGESTION
COPY_ON_CREATE
SNAPSHOT_ON_SUBMIT
```

Current project information SHOULD use canonical live references. Formal submissions,
approvals, acceptances, and generated reports SHALL capture immutable source/version
snapshots. Updating a referenced service/entity SHALL become visible to current
authorized consumers and impact projections, but SHALL NOT rewrite historical
evidence or silently replace user-entered values.

Form assistance, import suggestions, and report bindings SHALL use generic,
metadata-defined sources with provenance. Suggestions require explicit user action
unless the field is a configured read-only live binding. See ADR-0008.

---

# 9. Golden Rule 7 — Strict REST Boundary

## 9.1 Rule

Browser clients SHALL communicate with backend services only through documented `/api/v1` endpoints.

The frontend SHALL NOT:

- connect directly to PostgreSQL,
- access internal backend repositories,
- manipulate object-storage credentials,
- bypass backend authorization.

## 9.2 Base Contract

All standard JSON API responses SHALL use:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": {}
}
```

Failed operations SHALL use:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ENTITY_LOCKED",
    "message": "The requested resource is locked.",
    "details": {}
  },
  "meta": {
    "request_id": "..."
  }
}
```

The complete contract is defined in:

`04_API_SPECIFICATION.md`

## 9.3 HTTP Semantics

Agents SHALL preserve proper HTTP semantics:

```text
200 OK
201 Created
204 No Content
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Validation Error
423 Locked
500 Internal Server Error
```

No endpoint may return `200 OK` for a failed business operation merely because the HTTP request reached the server.

---

# 10. Golden Rule 8 — Workspace Isolation

Every tenant-like project context is represented by a workspace.

Workspace-scoped resources MUST be explicitly scoped to a `workspace_id`.

This includes at minimum:

- entity types,
- entities,
- forms,
- relationships,
- phases,
- dashboards,
- import profiles,
- documents where applicable.

A user possessing permission in Workspace A SHALL NOT automatically gain equivalent access in Workspace B.

Every workspace-sensitive query MUST enforce authorization server-side.

---

# 11. Golden Rule 9 — RBAC Plus Object-Level Authorization

Role membership alone is insufficient.

Authorization SHALL consider:

1. authenticated user,
2. system role,
3. required permission,
4. workspace membership,
5. resource-level restrictions,
6. locking state where applicable.

Example:

An `ANALYST` with `ENTITY_UPDATE` permission MAY update Entity X only if:

- Entity X belongs to an accessible workspace,
- the user has update privileges in that workspace,
- Entity X is not protected by a locked phase,
- no additional resource-specific restriction applies.

Frontend permission guards are usability controls only.

**Backend authorization remains authoritative.**

---

# 12. Golden Rule 10 — Safe Import Execution

## 12.1 Rule

Imports SHALL NOT silently overwrite existing information.

## 12.2 Required Pipeline

Every structured import SHALL follow:

```text
Upload
  ↓
Parse
  ↓
Analyze
  ↓
Map
  ↓
Validate
  ↓
Dry Run
  ↓
Conflict Detection
  ↓
User Review
  ↓
Explicit Resolution
  ↓
Transactional Commit
  ↓
Audit
```

## 12.3 Dry Run

Before committing mutations, the import system MUST return a preview containing at least:

```text
rows_read
rows_valid
rows_invalid
records_to_create
records_to_update
records_unchanged
conflicts
validation_errors
```

## 12.4 Conflict Resolution

Supported actions SHALL include:

```text
MERGE
REPLACE
SKIP
```

Where appropriate, resolution MAY be performed:

- globally,
- per row,
- per conflicting field.

## 12.5 Transaction Safety

An import commit MUST:

- use database transactions,
- be repeat-safe where feasible,
- prevent unintended duplicate execution,
- emit audit records.

See:

`05_BACKEND_SPECIFICATION.md`  
`09_TEST_SPECIFICATION.md`

---

# 13. Golden Rule 11 — Universal Mutation Audit Trail

All material mutations MUST generate immutable audit events.

Covered operations include:

```text
CREATE
UPDATE
DELETE
IMPORT
DOCUMENT_UPLOAD
DOCUMENT_VERSION_CREATE
LOCK
UNLOCK
PERMISSION_CHANGE
FORM_PUBLISH
METADATA_CHANGE
```

Each audit record SHALL contain, where applicable:

```text
audit_id
request_id
user_id
workspace_id
action
resource_type
resource_id
timestamp
before_state
after_state
source
client_ip
user_agent
```

Audit records SHALL NOT be updateable through normal application APIs.

Sensitive secrets and raw credentials MUST NOT appear in audit data.

---

# 14. Golden Rule 12 — Document Versions Are Append-Only

A new upload for an existing logical document SHALL create a new document version.

Existing file objects SHALL NOT be silently replaced.

Example:

```text
Process Specification
├── v1
├── v2
└── v3 ← current
```

The logical `documents` record identifies the document.

`document_versions` identifies immutable file versions.

Historical versions must remain accessible to authorized users unless retention policies explicitly remove them.

---

# 15. Golden Rule 13 — Object Storage Is Private

S3/MinIO buckets SHALL NOT be publicly accessible.

Frontend clients SHALL NOT receive permanent object-storage credentials.

Allowed patterns include:

```text
Browser
  ↓
Backend authorization
  ↓
Short-lived presigned URL
  ↓
Object storage
```

or proxied backend delivery where required.

Presigned URLs MUST:

- expire,
- be generated only after authorization,
- scope access to the requested object/action.

---

# 16. Golden Rule 14 — File Upload Is Untrusted Input

Uploaded files SHALL be treated as hostile input.

The upload pipeline MUST consider:

- maximum file size,
- allowed MIME types,
- extension validation,
- MIME/extension mismatch,
- filename sanitization,
- malware scanning,
- archive abuse,
- storage isolation.

Uploaded files MUST NOT be executed by the application server.

Office-to-PDF preview conversion SHOULD execute in an isolated worker environment.

---

# 17. Golden Rule 15 — Business Logic Belongs in Services

FastAPI route handlers SHALL remain thin.

### Route responsibility

```text
Parse request
Authenticate
Authorize
Invoke service
Serialize response
```

### Service responsibility

```text
Business validation
Rule evaluation
Transactions
Coordination
```

### Repository responsibility

```text
Persistence operations
Database queries
```

### Prohibited

Embedding substantial business logic directly inside route functions.

See:

`05_BACKEND_SPECIFICATION.md`

---

# 18. Golden Rule 16 — Database Changes Require Migrations

All relational schema changes MUST use Alembic migrations.

Direct manual production schema edits are prohibited.

Every migration SHALL define:

- upgrade path,
- downgrade path where practical,
- compatibility implications,
- index changes,
- data migration needs.

CI SHALL execute migrations against a clean PostgreSQL database.

---

# 19. Golden Rule 17 — No N+1 Query Patterns

Backend agents SHALL review list, hierarchy, relationship, form-rendering, and document queries for N+1 access patterns.

Use:

- joins,
- select-in loading,
- aggregation,
- batched queries,
- recursive CTEs,

rather than one SQL query per object.

Performance-sensitive endpoints SHALL have explicit query-count or latency tests where appropriate.

---

# 20. Golden Rule 18 — Optimistic Concurrency Protection

Mutable resources SHOULD support concurrency protection.

For critical records, use one of:

```text
version counter
updated_at precondition
ETag / If-Match
```

This prevents one analyst from silently overwriting another analyst's recent changes.

A stale update SHOULD result in:

```text
409 Conflict
```

---

# 21. Golden Rule 19 — Locks Are Enforced Server-Side

A locked phase or protected resource MUST remain read-only even if a caller bypasses the frontend.

Every mutating service touching lockable resources SHALL call the shared lock-policy service.

Do not duplicate lock logic across modules.

Unlocking requires an explicit permission such as:

```text
PHASE_UNLOCK
```

and MUST generate an audit event.

---

# 22. Golden Rule 20 — Deletion Policy

Hard deletion of enterprise knowledge SHOULD be exceptional.

Default behavior SHOULD be:

```text
ACTIVE
ARCHIVED
DELETED/soft deleted
```

Hard deletion MAY be used for:

- temporary import artifacts,
- uncommitted uploads,
- explicitly disposable technical records.

Referenced enterprise entities SHALL not be hard-deleted without integrity checks.

---

# 23. Golden Rule 21 — Stable Public IDs

Public API resources SHALL use UUIDs or another approved globally unique identifier.

Sequential internal database identifiers MUST NOT be exposed if they create security or enumeration concerns.

Identifiers SHALL remain stable across updates.

---

# 24. Golden Rule 22 — Enumerations and Statuses Are Contracted

Technical lifecycle states such as:

```text
DRAFT
ACTIVE
ARCHIVED
LOCKED
PUBLISHED
FAILED
```

must be defined centrally.

Agents MUST NOT introduce spelling variants such as:

```text
COMPLETED
Complete
completed
Done
```

for the same state.

Shared backend/frontend generated types SHOULD be used where feasible.

---

# 25. Golden Rule 23 — API Pagination Is Mandatory

Collection endpoints SHALL support bounded pagination.

Typical request:

```text
?page=1&page_size=50
```

or approved cursor pagination.

The API MUST NOT allow an unbounded:

```text
GET /entities
```

to return an entire enterprise repository.

Maximum page sizes SHALL be enforced by the server.

---

# 26. Golden Rule 24 — Search Is Not Hierarchy Traversal

The system SHALL distinguish between:

- entity lookup/search,
- hierarchy expansion,
- reporting queries,
- full-text document search.

Agents MUST NOT misuse hierarchy APIs to implement broad search.

PostgreSQL search MAY support MVP needs.

OpenSearch or another search engine MAY be introduced behind an abstraction when justified.

---

# 27. Golden Rule 25 — Background Processing for Expensive Work

Long-running operations SHALL NOT block synchronous HTTP workers.

Examples:

- large Excel imports,
- document conversions,
- malware scans,
- document text extraction,
- report generation,
- future AI inference.

The backend SHOULD submit such work to the approved background processing infrastructure.

The API SHOULD return a job identifier such as:

```json
{
  "job_id": "...",
  "status": "QUEUED"
}
```

Clients can then retrieve job state.

---

# 28. Golden Rule 26 — Idempotency for Critical Commands

Critical retriable operations SHOULD support idempotency.

Particularly:

- import commit,
- document upload completion,
- asynchronous job submission,
- externally triggered creation operations.

Use an `Idempotency-Key` or equivalent mechanism.

Repeated identical requests MUST NOT unintentionally duplicate enterprise records.

---

# 29. Golden Rule 27 — No Secrets in Source Code

Agents MUST NOT commit:

```text
JWT secrets
database passwords
S3 credentials
API keys
private certificates
```

Configuration SHALL use environment variables or an approved secret-management system.

`.env.example` MAY contain names and placeholder values only.

---

# 30. Golden Rule 28 — Fail Closed

If authorization, metadata validation, lock checking, or security configuration cannot be evaluated, the system SHALL reject the protected operation.

The system MUST NOT interpret uncertainty as permission.

---

# 31. Golden Rule 29 — Validation Exists on the Server

Frontend validation improves usability but is never authoritative.

All validation rules relevant to persistence MUST be evaluated server-side before committing data.

This includes metadata-defined validation.

Malformed or manipulated API requests SHALL be rejected even if they bypass the web frontend.

---

# 32. Golden Rule 30 — Backward Compatibility

Published `/api/v1` behavior SHOULD remain backward-compatible.

Breaking changes require either:

- a new API version, or
- an explicitly approved migration strategy.

Removing or renaming response fields used by existing clients without versioning is prohibited.

---

# 33. Prohibited Anti-Patterns

The following patterns MUST be rejected in review.

## 33.1 Domain Table Proliferation

```sql
CREATE TABLE business_processes (...)
```

unless the table represents a true platform-level concept rather than administrator-defined domain data.

---

## 33.2 Domain-Specific Backend Logic

```python
if entity_type.name == "Business Process":
    ...
```

unless behavior is explicitly defined as a plugin/extension approved by architecture.

Use metadata rules instead.

---

## 33.3 Domain-Specific Frontend Branches

```typescript
switch (entity.type) {
  case "Application":
    return <ApplicationView />;
}
```

---

## 33.4 Client-Side Authorization as Security

Hiding a button does not constitute authorization.

---

## 33.5 Direct Browser Database Access

Strictly prohibited.

---

## 33.6 Permanent Browser Object-Storage Credentials

Strictly prohibited.

---

## 33.7 Silent Import Overwrites

Strictly prohibited.

---

## 33.8 File Replacement Instead of Version Creation

Prohibited for version-controlled documents.

---

## 33.9 Unbounded API Queries

Prohibited.

---

## 33.10 Recursive Hierarchy Loading in Application Memory

Avoid repeated Python/JavaScript database access for recursive traversal.

Use PostgreSQL capabilities.

---

## 33.11 Business Logic in Controllers

Prohibited beyond request orchestration.

---

## 33.12 Manual Production Schema Modification

Prohibited.

---

## 33.13 Storing Binary Documents in PostgreSQL

Unless an ADR explicitly approves an exceptional case, file binaries belong in object storage.

PostgreSQL stores metadata and object references.

---

## 33.14 Mutable Audit History

Prohibited.

---

# 34. Required Cross-Cutting Services

Implementations SHOULD centralize the following concerns rather than duplicating logic:

```text
AuthorizationService
AuditService
LockPolicyService
MetadataValidationService
StorageService
ImportValidationService
FormRuleEvaluator
```

---

# 35. AI Coding Agent Operating Rules

Every AI coding agent SHALL perform the following sequence.

## Before Editing

1. Read:
   - `00_PROJECT_CONTEXT.md`
   - `01_ARCHITECTURE_RULES.md`
   - relevant subsystem specifications.

2. Inspect existing implementation.

3. Identify:
   - affected modules,
   - migrations,
   - APIs,
   - tests,
   - security implications.

4. State assumptions if the specification is incomplete.

5. Prefer the architecture documents over inferred conventions.

---

# 36. AI Agent Change Boundary

An agent SHALL modify only files required for its assigned task.

Broad refactoring is prohibited unless:

- required to complete the task safely, or
- explicitly authorized.

An agent must not opportunistically redesign unrelated modules.

---

# 37. AI Agent Schema Rule

AI agents MUST NOT independently introduce database schema changes when an existing design covers the requirement.

If a new schema change is necessary:

1. identify the need,
2. evaluate generic vs domain-specific impact,
3. create/update migration,
4. update `03_DATABASE_SPECIFICATION.md`,
5. request architecture review when structurally significant.

---

# 38. AI Agent API Rule

An agent MUST NOT introduce undocumented public endpoints.

New or changed public APIs require corresponding updates to:

```text
04_API_SPECIFICATION.md
OpenAPI schema
API tests
```

---

# 39. AI Agent Completion Report

Every implementation task SHALL finish with:

```text
TASK
SUMMARY
FILES_CHANGED
DATABASE_CHANGES
API_CHANGES
TESTS_ADDED
TEST_RESULTS
SECURITY_IMPACT
KNOWN_LIMITATIONS
ARCHITECTURE_DEVIATIONS
```

If no architecture deviation exists:

```text
ARCHITECTURE_DEVIATIONS: None
```

---

# 40. Architecture Deviation Procedure

If a requirement cannot reasonably be implemented while following this document, the agent SHALL NOT silently violate a rule.

It must produce an ADR proposal containing:

```text
Title
Context
Existing Rule
Problem
Options Considered
Recommended Decision
Consequences
Migration Impact
Security Impact
```

Implementation of the deviation should wait for architecture approval unless required to repair an immediate critical defect.

---

# 41. Mandatory CI Architecture Checks

The project SHOULD progressively automate architectural checks.

Examples:

- migration validation,
- OpenAPI schema validation,
- backend type checking,
- frontend type checking,
- linting,
- unit tests,
- integration tests,
- dependency vulnerability scanning,
- prohibited secret detection.

Where practical, custom checks SHOULD flag obvious domain-specific persistence artifacts.

---

# 42. Definition of Architecture Compliance

A feature is architecture-compliant only if:

- [ ] It introduces no hard-coded domain entity model.
- [ ] Dynamic behavior is driven by metadata where applicable.
- [ ] Backend authorization is enforced.
- [ ] Workspace isolation is preserved.
- [ ] Mutations are audited.
- [ ] Imports do not silently overwrite data.
- [ ] Documents preserve version history.
- [ ] API contracts are documented.
- [ ] Database changes have migrations.
- [ ] Tests cover critical behavior.
- [ ] No secrets are committed.
- [ ] Long-running operations are handled appropriately.
- [ ] No known prohibited anti-pattern has been introduced.

---

# 43. Related Specifications

This document must be interpreted together with:

```text
00_PROJECT_CONTEXT.md
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

When requirements conflict:

1. Security requirements override convenience.
2. This architecture rules document overrides module implementation preferences.
3. Explicit API/database specifications override illustrative examples.
4. Approved ADRs may override individual rules and must be linked from the affected specification.
