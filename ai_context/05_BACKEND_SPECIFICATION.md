# Backend Specification

**File:** `05_BACKEND_SPECIFICATION.md`  
**Status:** Normative  
**System:** Metadata-Driven Enterprise Architecture Management Platform  
**Version:** 1.0  
**Language:** Python 3.12+  
**Framework:** FastAPI  
**ORM:** SQLAlchemy 2.x  
**Validation:** Pydantic v2  
**Migration Tool:** Alembic  
**Primary Database:** PostgreSQL 16+  
**Object Storage:** S3-compatible / MinIO abstraction  
**Background Processing:** Celery-compatible worker architecture or approved equivalent  
**Audience:** Backend engineers, AI coding agents, reviewers, QA engineers, security engineers

---

# 1. Purpose

This document defines the backend implementation architecture and coding rules for the platform.

The backend SHALL implement:

- authentication and identity,
- authorization,
- workspace isolation,
- metadata processing,
- generic entity management,
- hierarchy management,
- relationship management,
- dynamic forms,
- structured data persistence,
- document lifecycle,
- Excel/CSV imports,
- phase/lock control,
- review comments,
- dashboards/reporting,
- audit logging,
- background jobs.

The backend SHALL preserve the core principle:

> **Business-domain concepts are metadata, not Python code.**

---

# 2. Normative References

The backend implementation SHALL conform to:

```text
00_PROJECT_CONTEXT.md
01_ARCHITECTURE_RULES.md
02_SYSTEM_REQUIREMENTS.md
03_DATABASE_SPECIFICATION.md
04_API_SPECIFICATION.md
09_TEST_SPECIFICATION.md
11_SECURITY_SPECIFICATION.md
```

If implementation convenience conflicts with these specifications, the specifications take precedence.

---

# 3. Technology Baseline

Required:

```text
Python 3.12+
FastAPI
Pydantic v2
SQLAlchemy 2.x
Alembic
PostgreSQL 16+
Pytest
httpx / FastAPI TestClient-compatible testing
```

Recommended:

```text
psycopg 3
structlog or standard structured logging
Redis
Celery or equivalent background queue
boto3-compatible S3 client
```

The backend SHALL avoid unnecessary framework sprawl.

---

# 4. Backend Package Structure

Recommended repository structure:

```text
backend/
├── pyproject.toml
├── alembic.ini
├── alembic/
│   └── versions/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── dependencies.py
│   │   ├── error_handlers.py
│   │   └── v1/
│   │       ├── router.py
│   │       └── routes/
│   │           ├── auth.py
│   │           ├── workspaces.py
│   │           ├── metadata.py
│   │           ├── entities.py
│   │           ├── relationships.py
│   │           ├── forms.py
│   │           ├── documents.py
│   │           ├── imports.py
│   │           ├── phases.py
│   │           ├── reviews.py
│   │           ├── dashboards.py
│   │           ├── audit.py
│   │           └── jobs.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── logging.py
│   │   ├── security.py
│   │   ├── permissions.py
│   │   ├── exceptions.py
│   │   └── constants.py
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   ├── policies/
│   ├── storage/
│   ├── imports/
│   ├── rules/
│   ├── workers/
│   ├── audit/
│   └── utils/
└── tests/
    ├── unit/
    ├── integration/
    └── api/
```

Module names MAY vary slightly, but responsibility boundaries SHALL remain equivalent.

---

# 5. Layered Architecture

# 5.1 API Layer

The API layer SHALL:

- parse HTTP input,
- resolve authenticated user,
- perform request-level dependency checks,
- invoke application/service methods,
- serialize responses,
- map known exceptions to API errors.

The API layer SHALL NOT:

- contain substantial business rules,
- execute raw SQL directly,
- make independent authorization decisions inconsistent with shared policy services,
- manipulate object storage directly.

Example:

```python
@router.post("/entities")
async def create_entity(
    payload: EntityCreateRequest,
    context: RequestContext = Depends(get_request_context),
    service: EntityService = Depends(get_entity_service),
):
    entity = await service.create_entity(context, payload)
    return success_response(entity)
```

---

# 5.2 Service Layer

The service layer owns application/business logic.

Responsibilities include:

- metadata validation,
- authorization orchestration,
- lock evaluation,
- transaction coordination,
- hierarchy validation,
- relationship validation,
- form rule evaluation,
- import orchestration,
- audit event generation.

Examples:

```text
WorkspaceService
MetadataService
EntityService
RelationshipService
FormDefinitionService
FormInstanceService
DocumentService
ImportService
PhaseService
ReviewService
DashboardService
AuditQueryService
JobService
```

---

# 5.3 Repository Layer

Repositories SHALL encapsulate persistence access.

Responsibilities:

- SQLAlchemy queries,
- inserts/updates,
- recursive hierarchy queries,
- persistence-specific filtering,
- row locking where necessary.

Repositories SHALL NOT contain:

- permission policy,
- form business rules,
- import conflict semantics,
- user-facing error messages.

---

# 5.4 Policy Layer

Cross-cutting policy decisions SHALL be centralized.

Required policy/service abstractions SHOULD include:

```text
AuthorizationService
WorkspaceAccessPolicy
LockPolicyService
MetadataValidationService
FormRuleEvaluator
RelationshipPolicy
ImportConflictPolicy
```

This prevents duplicated authorization/lock logic.

---

# 6. Request Context

Every authenticated request SHALL construct a request context containing at least:

```python
class RequestContext:
    request_id: UUID
    user_id: UUID
    roles: set[str]
    permissions: set[str]
    client_ip: str | None
    user_agent: str | None
```

Workspace-scoped service methods SHALL resolve authorized workspace membership explicitly.

---

# 7. Dependency Injection

FastAPI dependency injection SHALL be used for:

- database session,
- current user/context,
- service factories,
- storage client,
- queue client where appropriate.

Global mutable singleton state SHALL be avoided.

---

# 8. Database Session and Transaction Rules

## 8.1 Session Scope

A database session SHALL be scoped to a request or explicit background job transaction.

---

## 8.2 Service-Owned Transactions

Transactional business operations SHALL be coordinated by the service layer.

Examples:

- create entity with attributes,
- reparent entity,
- submit form,
- lock phase,
- commit import,
- create document version metadata.

---

## 8.3 Repository Transaction Ownership

Repositories SHALL NOT commit independently when participating in a larger service transaction.

Recommended pattern:

```python
async with unit_of_work:
    ...
    await unit_of_work.commit()
```

or equivalent explicit session transaction management.

---

# 9. ORM Model Rules

SQLAlchemy models SHALL map platform tables from `03_DATABASE_SPECIFICATION.md`.

Prohibited ORM models:

```text
BusinessProcess
Application
Server
Stakeholder
Risk
```

Allowed:

```text
EntityType
EntityObject
AttributeDefinition
RelationshipType
FormDefinition
Document
ImportJob
Phase
```

---

# 10. Pydantic Schema Rules

Pydantic request/response models SHALL be separate from ORM models.

Required categories:

```text
CreateRequest
UpdateRequest
Response
ListResponseItem
InternalCommand where useful
```

The API SHALL not serialize SQLAlchemy models directly without controlled schema conversion.

---

# 11. Standard API Response Helpers

The backend SHALL implement common response helpers matching `04_API_SPECIFICATION.md`.

Success:

```python
{
    "success": True,
    "data": data,
    "error": None,
    "meta": meta,
}
```

Failure mapping SHALL be centralized through exception handlers.

---

# 12. Exception Model

Create typed application exceptions.

Recommended hierarchy:

```text
ApplicationError
├── AuthenticationError
├── AuthorizationError
├── ResourceNotFoundError
├── ValidationError
├── ConflictError
├── LockedResourceError
├── MetadataError
├── HierarchyCycleError
├── ImportError
├── FileSecurityError
└── DependencyUnavailableError
```

Each exception SHALL map to:

- stable API error code,
- HTTP status,
- safe public message,
- optional details.

Internal stack traces SHALL not be returned to clients.

---

# 13. Authentication Service

`AuthService` SHALL own:

- credential verification,
- token creation,
- user activation checks,
- login audit,
- failed-login handling.

Passwords SHALL:

- never be stored plaintext,
- use an approved strong password hashing algorithm,
- be compared using library-provided secure verification.

JWT claims SHOULD include minimal required identity information.

Permissions SHOULD be resolved server-side rather than trusting stale permission lists embedded permanently in tokens.

---

# 14. Authorization Service

Every protected service operation SHALL call shared authorization logic.

Example:

```python
await authorization.require(
    context=context,
    permission="ENTITY_UPDATE",
    workspace_id=workspace_id,
    resource=entity,
)
```

The service SHALL consider:

- global permission,
- workspace membership,
- object scope,
- lock state separately where applicable.

---

# 15. Workspace Service

Required methods:

```text
create_workspace()
get_workspace()
list_workspaces()
update_workspace()
add_member()
remove_member()
list_members()
```

Rules:

- every workspace creation is audited,
- membership changes are audited,
- inaccessible workspaces SHALL not leak metadata through list endpoints.

---

# 16. Metadata Service

Required responsibilities:

- create/update entity types,
- create/update attributes,
- validate metadata configuration,
- prevent duplicate keys,
- prevent unsupported data types,
- validate inheritance references,
- enforce stable-key policies.

Recommended methods:

```text
create_entity_type()
update_entity_type()
archive_entity_type()
create_attribute()
update_attribute()
deactivate_attribute()
get_entity_schema()
```

---

# 17. Metadata Validation Engine

Dynamic values SHALL be validated against `AttributeDefinition`.

Validation SHALL support:

```text
required
data type
enum membership
numeric constraints
length constraints
pattern constraints
reference existence
read-only enforcement
```

Example internal interface:

```python
validate_attributes(
    entity_type: EntityType,
    definitions: list[AttributeDefinition],
    values: dict[str, Any],
    mode: ValidationMode,
) -> ValidationResult
```

Hard-coded checks by domain attribute name are prohibited.

---

# 18. Entity Service

Required methods:

```text
create_entity()
get_entity()
list_entities()
search_entities()
update_entity()
archive_entity()
reparent_entity()
get_tree()
```

Create/update flow SHALL be:

```text
authorize
→ resolve workspace/type
→ validate metadata
→ validate parent
→ validate lock/policies
→ mutate inside transaction
→ write audit
→ return DTO
```

---

# 19. Hierarchy Service Logic

Hierarchy traversal SHALL use repository/database recursive CTEs.

Cycle prevention SHALL occur before reparenting.

The service SHALL verify:

- same workspace,
- target parent exists,
- no self-parent,
- no ancestor cycle,
- lock state permits move.

---

# 20. Relationship Service

Required methods:

```text
create_relationship_type()
list_relationship_types()
create_relationship()
list_relationships()
delete_relationship()
```

Validation SHALL include:

- same workspace,
- source/target existence,
- relationship-type constraints,
- no prohibited self-link,
- duplicate rule where configured.

---

# 21. Form Definition Service

Required methods:

```text
create_form()
update_draft_form()
add_field()
update_field()
publish_form()
create_new_version()
get_render_contract()
```

Published forms SHALL be immutable.

`publish_form()` SHALL validate:

- field keys unique,
- referenced attributes exist,
- inheritance rules valid,
- visibility rules parse correctly,
- required metadata complete.

---

# 22. Form Rule Evaluator

A shared evaluator SHALL interpret metadata-defined rules.

Responsibilities:

- visibility rules,
- required conditions,
- inherited values,
- read-only state,
- validation predicates.

Rule representation MAY be JSON-based, but SHALL be deterministic and versionable.

Arbitrary Python execution from stored rule expressions is prohibited.

---

# 23. Form Instance Service

Required methods:

```text
create_instance()
get_instance()
save_draft()
submit()
request_revision()
approve()  # if implemented in current release
```

Submission SHALL:

```text
authorize
→ check lock
→ load exact form version
→ evaluate inherited/read-only rules
→ validate values
→ persist transactionally
→ audit
```

Historical form version identity SHALL be preserved.

---

# 24. Document Storage Abstraction

Define an interface such as:

```python
class StorageProvider(Protocol):
    async def put_object(...)
    async def delete_object(...)
    async def create_download_url(...)
    async def create_upload_url(...)
    async def object_exists(...)
```

Concrete implementations:

```text
MinioStorageProvider
S3StorageProvider
```

Business services SHALL depend on the abstraction, not boto3/minio clients directly.

---

# 25. Document Service

Required methods:

```text
create_document_with_version()
add_version()
get_document()
list_versions()
get_download_access()
get_preview_access()
archive_document()
```

Rules:

- new versions are append-only,
- object keys are unique and non-user-controlled,
- authorization occurs before URL generation,
- file metadata is persisted,
- file scans/previews may be asynchronous.

---

# 26. File Upload Pipeline

Required pipeline:

```text
authorize
→ inspect metadata
→ enforce size limit
→ validate extension
→ validate MIME
→ generate safe object key
→ store quarantine/original object
→ create metadata
→ enqueue scan
→ enqueue preview if supported
```

Uploaded filenames SHALL be treated as display metadata only.

They SHALL NOT determine storage paths directly.

---

# 27. Malware Scan Workflow

Production-capable architecture SHOULD support:

```text
PENDING
CLEAN
INFECTED
FAILED
```

Downloads/previews of non-clean files MAY be blocked by policy.

Scan implementation SHALL be isolated from the web process where practical.

---

# 28. Preview Generation

Preview generation SHALL use background workers for expensive conversions.

Examples:

```text
DOCX → PDF preview
XLSX → HTML/PDF preview
Image → direct preview
PDF → direct preview
```

Conversion workers SHALL operate in restricted environments.

---

# 29. Import Service

Required operations:

```text
create_import_job()
analyze()
save_mapping()
dry_run()
list_conflicts()
resolve_conflict()
bulk_resolve()
commit()
get_job()
```

Import code SHALL be separated into stages and SHALL NOT combine parsing and final persistence in one opaque function.

---

# 30. Import Parser Abstraction

Recommended interfaces:

```python
class ImportParser(Protocol):
    def inspect(self, file_path) -> ImportInspection
    def iter_rows(self, mapping) -> Iterator[SourceRow]
```

Implementations:

```text
XlsxImportParser
CsvImportParser
```

Avoid loading entire very large workbooks into memory when streaming/iterative approaches are feasible.

---

# 31. Import Mapping Engine

Mapping engine SHALL transform source columns to:

```text
system fields
dynamic attribute keys
references
```

Mappings SHALL be validated before dry run.

Transformations MAY include:

- trim,
- type conversion,
- enum normalization,
- date parsing.

Arbitrary untrusted code execution is prohibited.

---

# 32. Import Matching Strategy

Imports need an explicit way to identify existing entities.

Matching strategy MAY use:

- stable entity ID,
- configured unique attribute(s),
- composite key,
- parent context + key.

The matching strategy SHALL be part of the import profile/configuration.

Name-only matching SHALL not be assumed globally.

---

# 33. Import Dry Run

Dry run SHALL:

- parse rows,
- map values,
- validate metadata,
- find matches,
- classify create/update/unchanged,
- calculate diffs,
- persist conflict records or equivalent preview state,
- avoid mutating canonical entity data.

---

# 34. Import Commit

Commit SHALL:

```text
authorize
→ verify dry-run state
→ verify conflicts resolved
→ verify idempotency
→ begin transaction
→ apply creates/updates
→ emit audit records
→ store summary
→ commit
→ mark job completed
```

Failure SHALL roll back the canonical data transaction.

---

# 35. Phase Service

Required methods:

```text
create_phase()
update_phase()
list_phases()
lock_phase()
unlock_phase()
add_deliverable()
update_deliverable_status()
```

Lock/unlock SHALL be audited.

---

# 36. Lock Policy Service

Every mutation touching lockable content SHALL call a shared lock policy.

Example:

```python
await lock_policy.assert_mutable(
    context=context,
    resource=entity,
)
```

The policy SHALL determine whether the resource is associated with a locked phase.

Duplicated local lock checks are prohibited.

---

# 37. Review Service

Required methods:

```text
create_comment()
list_comments()
resolve_comment()
request_revision()
```

Review comments SHALL preserve author and timestamp.

---

# 38. Dashboard Service

The dashboard service SHALL execute only approved query definitions.

It SHALL NOT accept arbitrary SQL from browser clients.

Safe approaches:

- predefined metric types,
- metadata-driven query builder,
- server-generated SQL from validated configuration.

---

# 39. Audit Service

Every material mutation SHALL call a shared audit service.

Recommended interface:

```python
audit.record(
    request_context,
    action="ENTITY_UPDATE",
    resource_type="ENTITY",
    resource_id=entity.id,
    before_state=before,
    after_state=after,
)
```

Audit failure policy SHALL be explicit.

For critical mutations, inability to produce required audit records SHOULD cause the transaction to fail closed.

---

# 40. Background Job Service

Background operations SHALL have:

- job ID,
- job type,
- status,
- payload reference,
- result,
- error state,
- retry count.

Workers SHALL be idempotent where retry is possible.

---

# 41. Celery / Queue Rules

If Celery is used:

- task payloads SHOULD use IDs/references rather than large binary blobs,
- tasks SHALL retrieve current state from storage/database,
- retries SHALL be bounded,
- duplicate side effects SHALL be prevented,
- task exceptions SHALL be logged with job ID.

---

# 42. Configuration Management

Application configuration SHALL be loaded through typed settings.

Example categories:

```text
DATABASE_URL
JWT_SECRET
JWT_EXPIRY_SECONDS
S3_ENDPOINT
S3_BUCKET
S3_ACCESS_KEY
S3_SECRET_KEY
REDIS_URL
MAX_UPLOAD_SIZE
ALLOWED_MIME_TYPES
LOG_LEVEL
```

Secrets SHALL not be committed.

`.env.example` SHALL contain placeholders only.

---

# 43. Logging

Backend logs SHOULD be structured.

Each request log SHOULD contain:

```text
request_id
method
path
status_code
duration_ms
user_id if known
workspace_id if known
```

Sensitive request bodies, passwords, access tokens, and secrets SHALL NOT be logged.

---

# 44. Health Endpoints

Required:

```text
GET /health/live
GET /health/ready
```

Liveness checks process viability.

Readiness checks critical dependencies such as database connectivity.

Object storage/queue dependency checks MAY be included according to deployment policy.

---

# 45. OpenAPI

FastAPI-generated OpenAPI SHALL conform to `04_API_SPECIFICATION.md`.

The project SHALL export:

```text
contracts/openapi.yaml
```

CI SHOULD detect accidental breaking API changes.

---

# 46. Security Headers and Middleware

Backend/API gateway SHOULD provide security-relevant headers and middleware.

Examples:

- request IDs,
- CORS policy,
- trusted hosts,
- rate limiting where applicable.

CORS SHALL be explicitly configured, not wildcarded in production unless justified.

---

# 47. CORS

Development MAY allow known local frontend origins.

Production SHALL define explicit allowed origins.

Example:

```text
https://app.example.com
```

---

# 48. Input Validation

All incoming API payloads SHALL be validated with Pydantic or equivalent typed validation.

Never trust:

- entity IDs,
- workspace IDs,
- file extensions,
- MIME types,
- form metadata,
- import mapping,
- relationship constraints.

---

# 49. Output Serialization

API responses SHALL expose only intended public fields.

ORM internal data SHALL not be blindly serialized.

Sensitive fields prohibited from response include:

```text
password_hash
secret keys
internal credentials
storage secret tokens
```

---

# 50. Performance Rules

Backend SHALL avoid:

- N+1 ORM queries,
- loading entire hierarchy into Python for traversal,
- unbounded list endpoints,
- synchronous large file conversion,
- synchronous very large imports.

Use:

- eager/select-in loading where appropriate,
- recursive CTEs,
- pagination,
- background jobs.

---

# 51. Caching

Caching MAY be introduced for:

- metadata schemas,
- permissions,
- entity type definitions,
- dashboard summaries.

Cache SHALL never become the source of truth.

Invalidation rules SHALL be explicit.

---

# 52. Coding Standards

Python code SHALL:

- use type hints,
- pass formatter/linter checks,
- avoid dead code,
- avoid large God services,
- use descriptive naming,
- keep domain-independent abstractions.

Recommended tools MAY include:

```text
ruff
mypy or pyright
black-compatible formatting
```

Exact tool choice may be established by repository configuration.

---

# 53. Function Complexity

Services SHOULD be decomposed when functions become difficult to test or reason about.

A single service method SHALL not perform unrelated responsibilities such as:

```text
parse Excel
+ create DB schema
+ send email
+ generate dashboard
```

---

# 54. Testing Requirements

Every backend module SHALL include:

- unit tests for pure rules/services,
- integration tests for repositories/database,
- API tests for HTTP contracts,
- authorization tests,
- failure-path tests.

Critical modules requiring extensive coverage:

```text
Authorization
Metadata validation
Hierarchy cycle prevention
Form validation
Document versioning
Import dry-run/commit
Phase locking
Audit logging
```

---

# 55. Test Database

Integration tests SHALL run against PostgreSQL-compatible behavior.

SQLite SHALL NOT be used as the sole integration test database because JSONB, recursive CTE behavior, constraints, and PostgreSQL semantics differ.

---

# 56. Migration Testing

CI SHALL:

1. create empty PostgreSQL database,
2. run all Alembic upgrades,
3. validate schema,
4. run tests.

Where downgrade is supported, representative downgrade testing SHOULD also occur.

---

# 57. Idempotency

Backend SHALL support idempotency for critical retriable commands per `04_API_SPECIFICATION.md`.

Implementation MAY use a dedicated idempotency table or job-specific unique keys.

The behavior SHALL be deterministic and tested.

---

# 58. Concurrency

Mutable versioned resources SHALL detect stale writes.

Recommended flow:

```text
client version = 5
database version = 6
→ reject update
→ 409 STALE_VERSION
```

Blind last-write-wins behavior SHOULD be avoided for critical enterprise data.

---

# 59. Deletion Rules

Service methods SHALL respect soft-deletion policies.

Default queries SHOULD exclude:

```text
deleted_at IS NOT NULL
```

unless explicitly requesting archived/deleted resources.

---

# 60. Search

MVP search MAY use PostgreSQL.

Repository abstraction SHOULD allow future search-engine integration.

The backend SHALL distinguish:

- entity search,
- tree retrieval,
- document full-text search,
- reporting aggregation.

---

# 61. Prohibited Backend Anti-Patterns

Reject:

- `BusinessProcessService`,
- hard-coded field keys such as `"risk_level"` in domain branching,
- direct DB access from route handlers,
- repository-level commits inside multi-step workflows,
- broad `except Exception: return 200`,
- user-supplied SQL,
- arbitrary eval/exec for rules,
- permanent S3 credentials exposed to clients,
- silent file overwrite,
- silent import overwrite,
- mutable published form definitions,
- permission checks only in frontend,
- synchronous large conversion/import work.

---

# 62. Backend Agent Task Protocol

Before coding, AI backend agents SHALL state:

```text
TASK
REQUIREMENTS
FILES_AFFECTED
DATABASE_IMPACT
API_IMPACT
SECURITY_IMPACT
IMPLEMENTATION_PLAN
```

After coding:

```text
SUMMARY
FILES_CHANGED
MIGRATIONS
API_CHANGES
TESTS_ADDED
TEST_RESULTS
KNOWN_LIMITATIONS
ARCHITECTURE_DEVIATIONS
```

---

# 63. Definition of Done

A backend feature is complete only when:

- [ ] architecture rules are satisfied,
- [ ] service/repository boundaries are respected,
- [ ] request/response schemas exist,
- [ ] authorization is enforced,
- [ ] workspace isolation is enforced,
- [ ] lock policy is enforced where applicable,
- [ ] validation exists server-side,
- [ ] transactions are correct,
- [ ] audit exists for material mutations,
- [ ] tests cover success and failure paths,
- [ ] API/OpenAPI is updated,
- [ ] migrations are included if needed,
- [ ] no secrets are introduced,
- [ ] observability is adequate,
- [ ] no prohibited anti-pattern is present.

---

# 64. Requirement Traceability

```text
AUTH-FR-*  → AuthService, AuthorizationService
WS-FR-*    → WorkspaceService
META-FR-*  → MetadataService, MetadataValidationService
ENT-FR-*   → EntityService
HIER-FR-*  → EntityService + hierarchy repository queries
REL-FR-*   → RelationshipService
FORM-FR-*  → FormDefinitionService, FormRuleEvaluator
DATA-FR-*  → FormInstanceService
DOC-FR-*   → DocumentService, StorageProvider, workers
IMP-FR-*   → ImportService, ImportParser, ImportConflictPolicy
PHASE-FR-* → PhaseService, LockPolicyService
REV-FR-*   → ReviewService
RPT-FR-*   → DashboardService
AUD-FR-*   → AuditService
```

---

# 65. Related Specifications

```text
00_PROJECT_CONTEXT.md
01_ARCHITECTURE_RULES.md
02_SYSTEM_REQUIREMENTS.md
03_DATABASE_SPECIFICATION.md
04_API_SPECIFICATION.md
06_FRONTEND_SPECIFICATION.md
07_AI_AGENT_ROLES.md
08_TASK_BACKLOG.md
09_TEST_SPECIFICATION.md
10_DEPLOYMENT_GUIDE.md
11_SECURITY_SPECIFICATION.md
12_CURRENT_STATUS.md
contracts/openapi.yaml
```
