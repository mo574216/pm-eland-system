# Test Specification

**File:** `09_TEST_SPECIFICATION.md`  
**Status:** Normative  
**System:** Metadata-Driven Enterprise Architecture Management Platform  
**Version:** 1.0  
**Audience:** QA engineers, backend/frontend engineers, AI coding agents, security reviewers, release managers

---

# 1. Purpose

This document defines the testing strategy, required coverage, test environments, acceptance gates, and traceability model for the platform.

Testing SHALL verify not only feature success paths, but also:

- authorization,
- workspace isolation,
- validation failures,
- locked-resource behavior,
- import safety,
- concurrency conflicts,
- document version integrity,
- audit behavior,
- API contract stability.

A feature is not complete merely because its happy path works.

---

# 2. Normative References

Testing SHALL validate behavior defined in:

```text
01_ARCHITECTURE_RULES.md
02_SYSTEM_REQUIREMENTS.md
03_DATABASE_SPECIFICATION.md
04_API_SPECIFICATION.md
05_BACKEND_SPECIFICATION.md
06_FRONTEND_SPECIFICATION.md
08_TASK_BACKLOG.md
11_SECURITY_SPECIFICATION.md
```

---

# 3. Test Levels

The project SHALL use:

```text
L1 — Unit Tests
L2 — Component Tests
L3 — Repository/Database Integration Tests
L4 — API Integration Tests
L5 — Frontend Integration Tests
L6 — End-to-End Tests
L7 — Security Tests
L8 — Performance/Load Tests
L9 — Migration/Recovery Tests
```

Not every task requires every level, but critical workflows require multiple layers.

---

# 4. Test Technology

Backend:

```text
pytest
pytest-asyncio where needed
httpx / FastAPI test client
PostgreSQL test database
```

Frontend:

```text
Vitest
React Testing Library
Playwright
```

Optional production/security tooling MAY include:

```text
OWASP ZAP
k6
Locust
Trivy
dependency scanners
```

---

# 5. Test Environment Rules

## TEST-RULE-001 — PostgreSQL Required for Integration

SQLite SHALL NOT be the sole integration test database.

Reason:

The system depends on:

- JSONB,
- recursive CTEs,
- PostgreSQL constraints,
- PostgreSQL indexing behavior.

---

## TEST-RULE-002 — Isolated Test Data

Tests SHALL not depend on developer-local data.

Each test suite SHALL:

- create isolated fixtures,
- clean up or use disposable DB/container,
- avoid ordering dependencies.

---

## TEST-RULE-003 — Deterministic Tests

Tests SHALL avoid reliance on:

- wall-clock timing where unnecessary,
- external public services,
- random non-seeded behavior,
- manually prepared state.

---

# 6. Test Data Factory Strategy

Required factories/fixtures SHOULD include:

```text
UserFactory
RoleFactory
WorkspaceFactory
EntityTypeFactory
AttributeDefinitionFactory
EntityFactory
RelationshipTypeFactory
FormDefinitionFactory
FormInstanceFactory
DocumentFactory
ImportProfileFactory
PhaseFactory
```

Fixtures SHOULD support multiple workspaces and users to test isolation.

---

# 7. Requirement Traceability

Every P0/P1 requirement SHALL map to one or more tests.

Recommended naming:

```text
test_AUTH_FR_001_valid_login
test_WS_FR_002_cross_workspace_denied
test_HIER_FR_004_cycle_rejected
test_IMP_FR_009_no_silent_overwrite
```

The QA suite SHOULD maintain a traceability table or generated report.

---

# 8. Authentication Tests

# TEST-AUTH-001 — Valid Login

**Requirements:** AUTH-FR-001

Given active user with valid credentials:

Expected:

- 200 response,
- token returned,
- user context returned,
- login audit emitted.

---

# TEST-AUTH-002 — Invalid Password

Expected:

- authentication rejected,
- safe generic error,
- no password/username existence disclosure.

---

# TEST-AUTH-003 — Inactive User

Expected:

- login rejected.

---

# TEST-AUTH-004 — Expired Token

Expected:

- protected endpoint returns 401.

---

# TEST-AUTH-005 — Missing Token

Expected:

- protected endpoint returns 401.

---

# 9. Authorization Tests

# TEST-AUTHZ-001 — Missing Permission

Given authenticated user without `ENTITY_UPDATE`:

Expected:

- entity update rejected with 403.

---

# TEST-AUTHZ-002 — Frontend Guard Bypass

Direct API request SHALL still be rejected even if frontend UI is bypassed.

---

# TEST-AUTHZ-003 — Elevated Role

Verify only authorized roles can:

```text
FORM_DESIGN
PHASE_UNLOCK
WORKSPACE_MANAGE
AUDIT_READ
```

---

# 10. Workspace Isolation Tests

# TEST-WS-001 — Entity Read Isolation

User with Workspace A access attempts Workspace B entity read.

Expected:

```text
403 or non-leaking 404 according to API policy
```

No B metadata leaked.

---

# TEST-WS-002 — Entity Mutation Isolation

Cross-workspace create/update/reparent SHALL be rejected.

---

# TEST-WS-003 — Document Isolation

User cannot retrieve download/preview access for document outside permitted workspace.

---

# TEST-WS-004 — Import Isolation

Import profile/job from another workspace cannot be used.

---

# TEST-WS-005 — Dashboard Isolation

Dashboard query never returns data from inaccessible workspace.

---

# 11. Metadata Tests

# TEST-META-001 — Create Arbitrary Type

Create:

```text
Network Security Zone
```

without schema migration/code change.

Expected:

- type persisted,
- available through API/UI.

---

# TEST-META-002 — Duplicate Key

Same workspace + duplicate entity-type key:

Expected:

- validation/conflict error.

---

# TEST-META-003 — Same Key Different Workspace

Allowed if scoped uniqueness permits.

---

# TEST-META-004 — Invalid Attribute Type

Expected:

- rejected.

---

# TEST-META-005 — Enum Validation

Invalid enum configuration rejected.

---

# TEST-META-006 — Stable Key

Changing display label SHALL not modify stored attribute key.

---

# 12. Generic Entity Tests

# TEST-ENT-001 — Create Entity

Validate:

- workspace,
- entity type,
- attributes,
- audit,
- initial version.

---

# TEST-ENT-002 — Required Attribute Missing

Expected:

- 422,
- field-specific error.

---

# TEST-ENT-003 — Unknown Attribute Key

Expected behavior SHALL follow metadata policy:

- reject unknown key unless explicitly allowed.

---

# TEST-ENT-004 — Update Entity

Expected:

- values updated,
- version incremented,
- audit before/after stored.

---

# TEST-ENT-005 — Stale Version

Given client version 2 and DB version 3:

Expected:

```text
409 STALE_VERSION
```

No overwrite.

---

# TEST-ENT-006 — Soft Delete/Archive

Default query excludes deleted entity.

---

# 13. Hierarchy Tests

# TEST-HIER-001 — Parent/Child Creation

Valid child appears beneath parent.

---

# TEST-HIER-002 — Self Parent

Entity cannot become its own parent.

---

# TEST-HIER-003 — Ancestor Cycle

Given:

```text
A → B → C
```

Attempt:

```text
A parent = C
```

Expected:

```text
409 HIERARCHY_CYCLE
```

---

# TEST-HIER-004 — Cross-Workspace Parent

Rejected.

---

# TEST-HIER-005 — Recursive Tree Query

Verify complete hierarchy returned in correct order.

---

# TEST-HIER-006 — Query Count

Hierarchy load SHALL not exhibit N+1 query behavior.

---

# 14. Relationship Tests

# TEST-REL-001 — Valid Relationship

Create valid source/target relationship.

---

# TEST-REL-002 — Self Relationship

Rejected where relationship type forbids it.

---

# TEST-REL-003 — Type Constraint

Source/target types not allowed by relationship definition:

Expected rejection.

---

# TEST-REL-004 — Duplicate Relationship

Verify uniqueness policy.

---

# 15. Form Definition Tests

# TEST-FORM-001 — Create Draft Form

Expected DRAFT status.

---

# TEST-FORM-002 — Duplicate Field Key

Rejected.

---

# TEST-FORM-003 — Publish Form

Published form becomes immutable.

---

# TEST-FORM-004 — Edit Published Form

Direct mutation rejected.

---

# TEST-FORM-005 — New Version

New DRAFT created with incremented version.

Historical version unchanged.

---

# TEST-FORM-006 — Invalid Inheritance Rule

Rejected during validation/publish.

---

# TEST-FORM-007 — Invalid Visibility Rule

Rejected.

---

# 16. Form Rendering Tests

# TEST-FORM-RENDER-001 — Field Type Mapping

For each supported type:

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

Expected render contract generated correctly.

---

# TEST-FORM-RENDER-002 — Parent Prefill

Child process form receives configured parent service values.

---

# TEST-FORM-RENDER-003 — Read-Only Inheritance

Inherited read-only field cannot be modified successfully.

---

# TEST-FORM-RENDER-004 — Conditional Visibility

Rule evaluates correctly.

---

# 17. Form Submission Tests

# TEST-DATA-001 — Valid Submission

Values persisted.

---

# TEST-DATA-002 — Invalid Required Field

Rejected with field-specific error.

---

# TEST-DATA-003 — Repeating Table

Multiple rows persist and reload correctly.

---

# TEST-DATA-004 — Historical Form Version

Instance remains associated with original form version after newer form version published.

---

# TEST-DATA-005 — Locked Form Data

Mutation rejected when relevant phase locked.

---

# TEST-CTX-001 — Authorized Context Header

Opening a form from a phase/service deliverable returns and renders the configured
project, phase, service/entity, party, date/state, and lock context without requiring
raw ID entry. Forged or cross-workspace context is rejected.

# TEST-CTX-002 — Binding Mode Semantics

Verify live references update current views, read-only inherited values cannot be
mutated, editable suggestions can diverge, copy-on-create does not later change, and
snapshot-on-submit captures source ID/version/value atomically.

# TEST-ASSIST-001 — Manual and Import Suggestions

The same candidate contract works for a manual form and import row; every suggestion
includes reason/provenance and deterministic/AI classification. Generation does not
mutate canonical/draft values.

# TEST-ASSIST-002 — Accept/Edit/Reject Safety

Accept/edit/reject and bounded bulk decisions enforce permission, validation,
concurrency, workspace, field state, and lock policy. Rejected/obsolete candidates do
not repeatedly reappear without changed evidence or explicit regeneration.

# TEST-REF-001 — Current Propagation and Historical Stability

Changing a canonical service is visible through current live bindings and authorized
impact projections while submitted forms, deliverables, accepted packages, and
generated formal reports retain their captured source/version snapshots.

# TEST-REF-002 — Impact Isolation and Idempotency

Impact markers/notifications are bounded, workspace-isolated, permission-filtered,
and idempotent; they do not mutate user values, unrelated relationships, or history.

---

# 18. Frontend Component Tests

Required component tests include:

```text
DynamicFieldRenderer
DynamicFormRenderer
DynamicTableField
PermissionGuard
EntityTreeViewer
DocumentPanel
ImportWizard
FormContextHeader
SuggestionPanel
HumanReadableSelector
NaturalRelationshipPanel
ReportTemplateDesigner
```

---

# 19. Frontend Dynamic Form Tests

Validate:

- metadata field ordering,
- enum options,
- read-only state,
- backend validation display,
- nested/repeating row handling,
- loading state,
- empty/failure state.

---

# 19.1 Persian Localization and RTL Tests

## TEST-I18N-001 — Document Locale and Direction

Playwright SHALL verify that the document root declares `lang="fa"` and
`dir="rtl"`, and component tests SHALL verify the MUI theme direction is RTL.

## TEST-I18N-002 — Persian Core Workflows

Core routes SHALL render Persian headings, form labels, buttons, validation
messages, empty states, tooltips, aria labels, and notifications. Playwright
SHALL fail when known untranslated English platform copy appears in the core MVP
workflow. Technical identifiers and user-authored values are excluded from this
copy assertion.

## TEST-I18N-003 — RTL Component Usability

Representative navigation, forms, tables, dialogs, menus, breadcrumbs,
pagination, and directional controls SHALL remain visible, keyboard-usable, and
correctly ordered in RTL.

## TEST-I18N-004 — Persian Search Normalization

Backend unit and integration tests SHALL cover Persian/Arabic Yeh and Kaf,
zero-width non-joiner, diacritics/tatweel, whitespace, and Persian/Arabic numeral
equivalence while proving canonical display text is not overwritten.

## TEST-I18N-005 — Unicode Security

Persian metadata and user values SHALL be tested as untrusted Unicode input under
the normal XSS, validation, authorization, and workspace-isolation controls.

---

# 19.2 Human-Centered UX Contract Tests

## TEST-UX-001 — No Raw Identifier Entry

Membership, parent/entity/reference, relationship, phase/deliverable, and ordinary
configuration flows SHALL use named searchable selectors and SHALL not present UUID
text fields. Direct API authorization remains independently tested.

## TEST-UX-002 — Generated Technical Keys

Creating an information type, attribute, form section/field, workflow item, or other
supported configurable resource with a human-readable name and no key SHALL receive a
unique stable server-generated key. Advanced explicit-key validation and post-publish
immutability SHALL be tested separately.

## TEST-UX-003 — Natural Relationship Flow

From a current record, only compatible localized relation labels/authorized target
records appear. The UI creates the correct directional API payload without displaying
direction/cardinality/IDs and renders forward/reverse natural-language results.

## TEST-UX-004 — Progressive Administration

Critical administration flows SHALL test list/add/edit/preview/publish behavior,
plain-language labels, defaults, Advanced disclosure, validation, and safe
remove/archive impact warnings.

---

# 20. Document Tests

# TEST-DOC-001 — First Upload

Expected:

- logical document created,
- version 1 created,
- safe object key used.

---

# TEST-DOC-002 — Second Version

Expected:

- version 1 preserved,
- version 2 added,
- current version updated.

---

# TEST-DOC-003 — No Silent Replacement

Object/version history proves old content preserved.

---

# TEST-DOC-004 — Unauthorized Download

Rejected.

---

# TEST-DOC-005 — Presigned URL Expiry

If presigned URLs used:

- expiration is finite,
- unauthorized caller cannot obtain URL.

---

# TEST-DOC-006 — File Type Validation

Unsupported type rejected.

---

# TEST-DOC-007 — Oversized File

Expected:

```text
413 FILE_TOO_LARGE
```

---

# TEST-DOC-008 — Malware State

If scan workflow enabled:

infected file SHALL not be available under normal policy.

---

# 21. Import Parser Tests

# TEST-IMP-001 — XLSX Inspection

Verify:

- sheets,
- columns,
- row counts,
- sample values.

---

# TEST-IMP-002 — CSV Inspection

Equivalent CSV behavior.

---

# TEST-IMP-003 — Malformed File

Safe failure.

---

# 22. Import Mapping Tests

# TEST-IMP-004 — Valid Mapping

Columns map to attributes.

---

# TEST-IMP-005 — Missing Required Mapping

Rejected before dry run.

---

# TEST-IMP-006 — Type Conversion

Validate dates/numbers/enums.

---

# 23. Import Dry-Run Tests

# TEST-IMP-007 — Dry Run No Mutation

Snapshot canonical entity state before and after dry run.

Expected:

```text
identical
```

---

# TEST-IMP-008 — Create Classification

New records classified as create.

---

# TEST-IMP-009 — Update Classification

Changed existing values classified as update/conflict according to policy.

---

# TEST-IMP-010 — Unchanged Classification

No-op rows classified unchanged.

---

# TEST-IMP-011 — Validation Error Summary

Invalid rows returned without mutation.

---

# 24. Import Conflict Tests

# TEST-IMP-012 — MERGE

Verify merge semantics exactly as defined.

---

# TEST-IMP-013 — REPLACE

Explicit replace updates target values.

---

# TEST-IMP-014 — SKIP

Existing values preserved.

---

# TEST-IMP-015 — Unresolved Conflict Blocks Commit

Expected:

```text
IMPORT_CONFLICTS_UNRESOLVED
```

---

# 25. Import Commit Tests

# TEST-IMP-016 — Successful Transaction

Expected summary matches creates/updates/skips.

---

# TEST-IMP-017 — Rollback on Failure

Inject failure midway.

Expected:

- no partial canonical mutation.

---

# TEST-IMP-018 — Duplicate Commit

Using same idempotency key/job:

Expected:

- no duplicate records,
- stable response/state.

---

# TEST-IMP-019 — Audit Summary

Import audit exists with counts and user.

---

# TEST-IMP-020 — Contextual Import Binding

An import started from a phase deliverable inherits the authorized workspace, phase,
deliverable, target form/entity type, and permitted profile; committed records and
history retain those associations.

---

# TEST-IMP-021 — Locked or Forged Import Context

Locked-phase import and mixed/cross-workspace context IDs are rejected both at job
creation and commit recheck without target-existence leakage.

---

# TEST-IMP-022 — Relationship Preservation

Updating explicitly mapped fields through import preserves unrelated existing entity
relationships. Only explicitly mapped/reviewed relationship changes may mutate links.

---

# 26. Phase and Lock Tests

# TEST-PHASE-001 — Lock Phase

Authorized manager succeeds.

---

# TEST-PHASE-002 — Unauthorized Lock

Rejected.

---

# TEST-PHASE-003 — Locked Entity Update

Rejected with 423 or documented lock error.

---

# TEST-PHASE-004 — Locked Form Save

Rejected.

---

# TEST-PHASE-005 — Locked Hierarchy Move

Rejected where resource belongs to locked phase.

---

# TEST-PHASE-006 — Unlock Permission

Only explicit authorized user can unlock.

---

# TEST-PHASE-007 — Audit

Lock/unlock audit records exist.

---

# 27. Review Tests

P1:

- create review comment,
- list comments,
- resolve comment,
- revision requested,
- preserve author/time.

# TEST-GOV-001 — Authority Separation Matrix

For every governed transition, test allow and deny cases for the seven baseline
personas plus a custom role. At minimum prove:

- contractor contribution does not grant formal submission,
- contractor formal submission does not grant project review,
- Project Officer monitoring does not grant Project Manager decisions,
- technical recommendation/sign-off does not grant employer acceptance,
- employer acceptance does not grant contractor work management,
- frontend-hidden actions remain rejected through direct API calls.

# TEST-GOV-002 — Transition Version and Audit Integrity

Each internal review, submission, withdrawal, resubmission, recommendation, sign-off,
reopening, and acceptance transition SHALL retain workflow-definition version,
target artifact version, actor, authority context, time, prior/resulting state, and
an immutable audit event.

# TEST-GOV-003 — Governed Resource Isolation

Cross-workspace IDs for workflows, assignments, submissions, comments, threads,
notifications, acceptance packages, and conditions SHALL be denied without resource
existence leakage. Mixed-workspace bulk requests SHALL fail atomically.

# TEST-ACC-001 — Acceptance Gate Enforcement

Final acceptance SHALL be rejected while any configured mandatory phase,
deliverable, critical finding, or acceptance condition remains unsatisfied.

# TEST-ACC-002 — Conditional Acceptance Closure

Only configured verifiers may verify evidence; conditional acceptance becomes full
acceptance only when every mandatory condition is satisfied. Rejection and reopening
retain the earlier evidence and decisions.

# TEST-COM-001 — Communication Visibility

Internal contractor notes, Project Officer monitoring notes, formal review comments,
employer comments, threads, announcements, reminders, and notifications SHALL obey
their explicit visibility and linked-target authorization.

---

# 28. Dashboard Tests

# TEST-RPT-001 — Basic KPI

Expected correct entity/document/phase counts.

---

# TEST-RPT-002 — Workspace Isolation

No cross-workspace aggregation.

---

# TEST-RPT-003 — Arbitrary SQL Rejected

Browser cannot supply executable SQL.

---

# TEST-RPT-004 — Versioned Report Template

Draft/preview/publish/new-version behavior preserves immutable published versions and
validates allowlisted sections/bindings and required project/contractor details.

---

# TEST-RPT-005 — Generated Report Provenance

A generated formal report retains template version, data-as-of time, parameters,
authorized source IDs/versions, immutable output document version, actor, and audit.
Later source/template changes do not alter it.

---

# TEST-RPT-006 — Unsafe Template Rejected

Reject SQL, executable expressions, unsafe markup/resources, cross-workspace/hidden
bindings, oversized generation, and missing required sections.

---

# 29. Audit Tests

# TEST-AUD-001 — Entity Mutation Audit

Create/update/archive produces expected records.

---

# TEST-AUD-002 — Permission Mutation Audit

Role/member changes audited.

---

# TEST-AUD-003 — Audit Immutability

Application APIs cannot update/delete audit logs.

---

# TEST-AUD-004 — Sensitive Data Redaction

Audit does not contain:

```text
passwords
access tokens
storage secrets
```

---

# 30. API Contract Tests

Every public endpoint SHALL be tested for:

- expected success status,
- standard response envelope,
- stable error envelope,
- authentication behavior,
- validation behavior.

OpenAPI schema SHOULD be validated in CI.

---

# 31. Pagination Tests

For collection endpoints verify:

- default page,
- custom page size,
- max page-size enforcement,
- total count/meta,
- empty page behavior,
- invalid parameter handling.

---

# 32. Rate Limit Tests

Where enabled:

- repeated login attempts eventually rate-limited,
- response uses 429,
- retry metadata correct.

---

# 33. Background Job Tests

Validate:

```text
QUEUED
RUNNING
SUCCEEDED
FAILED
```

Retry tests SHALL verify no duplicate side effects.

---

# 34. Security Tests

Security suite SHALL include:

```text
broken object-level authorization
broken workspace isolation
injection attempts
XSS payload handling
unsafe rich text
file upload abuse
MIME mismatch
path traversal filenames
CORS misconfiguration
secret exposure
authorization bypass
```

---

# 35. SQL Injection Tests

Because ORM is used, tests SHALL still verify unsafe dynamic filtering/query-builder code does not concatenate untrusted SQL.

---

# 36. XSS Tests

Rich-text and displayed imported data SHALL be tested with malicious payloads such as:

```html
<script>alert(1)</script>
```

Expected:

- sanitized/escaped,
- never executed.

---

# 37. File Upload Security Tests

Test:

- double extension,
- MIME mismatch,
- path traversal filename,
- unsupported archive,
- zero-byte file if disallowed,
- oversized file.

---

# 38. Performance Tests

P1 production baseline.

Critical scenarios:

```text
10,000 entity list/search dataset
deep hierarchy traversal
relationship-heavy entity detail
large form metadata
large import
audit pagination
dashboard aggregation
```

---

# 39. Performance Targets

Initial target guidelines:

Ordinary CRUD:

```text
p95 server response < 500 ms
```

under agreed baseline load.

Hierarchy and report targets MAY be defined separately.

These targets SHALL be measured, not assumed.

---

# 40. Load Tests

Recommended load profiles:

```text
20 concurrent users — baseline
100 concurrent users — production target exploration
```

Exact production requirements MAY later be refined.

---

# 41. Migration Tests

CI SHALL verify:

1. empty database,
2. apply all Alembic upgrades,
3. application starts,
4. schema checks pass.

Representative downgrade tests SHOULD be included.

---

# 42. Seed Tests

Role/permission seed execution SHALL be idempotent.

Running seed twice SHALL not duplicate rows.

---

# 43. Backup/Restore Tests

Before production:

- restore PostgreSQL backup into clean environment,
- verify key records,
- verify application starts,
- verify object references remain consistent.

---

# 44. E2E MVP Scenario

Playwright SHALL implement the canonical workflow.

## E2E-001

```text
1. Login as admin.
2. Create workspace.
3. Create entity type "Business Service".
4. Create entity type "Business Process".
5. Define attributes.
6. Create process form.
7. Configure parent-prefilled service fields.
8. Create service.
9. Create process under service.
10. Open dynamic form.
11. Verify inherited service values.
12. Enter process-specific values.
13. Save/submit.
14. Upload document.
15. Upload new document version.
16. Upload Excel workbook.
17. Configure mapping.
18. Run dry run.
19. Resolve conflict.
20. Commit import.
21. Login as manager.
22. View dashboard.
23. Lock phase.
24. Login as analyst.
25. Attempt locked edit.
26. Verify rejection/read-only UX.
```

---

# 45. Negative E2E Scenario

## E2E-002

Attempt:

```text
cross-workspace entity access
unauthorized form designer access
document download without permission
import commit before dry run
unresolved conflict commit
cycle creation
```

Expected all rejected.

---

# 45.1 Governed Delivery and Acceptance Scenario

## E2E-003

```text
1. Administrator publishes a configurable deliverable workflow.
2. Contractor Team Member prepares a version and requests internal review.
3. Verify the Team Member cannot formally submit it.
4. Contractor Project Leader returns one internal correction.
5. Team Member revises and returns the work.
6. Contractor Project Leader marks it ready and formally submits the exact version.
7. Project Officer sees the queue and records a monitoring flag but cannot decide it.
8. Technical Reviewer records a major comment and requests revision.
9. Contractor resolves the assigned action through internal review and resubmission.
10. Technical Reviewer recommends approval; verify this is not acceptance.
11. Project Manager recommends phase acceptance.
12. Employer Representative conditionally accepts with one explicit condition.
13. Authorized verifier accepts evidence for the condition.
14. Employer Representative closes conditional acceptance.
15. Verify immutable submission, review, decision, condition, notification, and audit history.
16. Repeat protected reads/transitions with a foreign-workspace actor and verify denial.
```

---

# 45.2 Contextual Form, Import, Change, and Report Scenario

## E2E-004

```text
1. Administrator creates an organization/party for employer and contractor using names, not IDs.
2. Administrator creates a service information type/form using generated hidden keys.
3. Administrator configures project/service live fields, editable suggestions, and snapshot-on-submit fields.
4. Administrator publishes a report template requiring project and contractor details.
5. User opens a phase deliverable for a service and sees project/phase/service/party context above the form.
6. User accepts one explainable suggestion, rejects another, edits a third, and saves.
7. User launches embedded workbook import from the deliverable; known target/profile/context are inherited.
8. User completes dry run/conflicts/commit and returns to the same deliverable.
9. Verify imported updates preserve unrelated service relationships.
10. Authorized manager changes the canonical service and sees affected current project items.
11. Verify current live fields show the change and submitted snapshots remain unchanged.
12. Generate the configured progress report and verify required project/contractor content and provenance.
13. Change the service/template and verify the completed formal report remains unchanged.
14. Verify no normal workflow asked for UUID, raw stable key, direction/cardinality, or matching discriminator.
15. Repeat context, suggestion, impact, import, and report access with a foreign-workspace actor and verify denial.
```

---

# 46. Regression Gate

Before merging to protected branch:

Required:

- unit tests pass,
- integration tests pass,
- migration test passes,
- frontend tests pass,
- TypeScript passes,
- lint passes.

Before production:

Also require:

- E2E MVP pass,
- security review,
- no unresolved critical/high severity findings,
- backup/restore validation according to deployment plan.

---

# 47. Flaky Test Policy

Flaky tests SHALL not be ignored indefinitely.

A flaky test SHALL be:

- fixed,
- temporarily quarantined with issue/task ID,
- given an owner and deadline.

Repeated reruns until green are prohibited as a substitute for fixing instability.

---

# 48. Coverage Guidance

Coverage percentage alone SHALL not define quality.

Recommended baseline:

```text
backend unit/service coverage: >= 80% for critical modules
frontend reusable core components: >= 75%
```

Critical security/import/lock rules SHOULD approach full branch coverage.

---

# 49. Test Naming

Recommended pattern:

```text
test_<requirement_or_behavior>_<expected_result>
```

Examples:

```text
test_HIER_FR_004_reparent_to_descendant_rejected
test_IMP_FR_009_existing_value_not_silently_overwritten
```

---

# 50. Defect Severity

```text
Critical:
security breach, data loss, cross-workspace leakage

High:
core workflow broken, import corruption, authorization failure

Medium:
major UX/workflow issue with workaround

Low:
minor defect/cosmetic issue
```

---

# 51. Release Blocking Defects

Production release SHALL be blocked by unresolved:

```text
Critical
High security
High data-integrity
```

issues.

---

# 52. QA Agent Output Format

For each tested task:

```text
TASK_ID
REQUIREMENTS_TESTED
TESTS_RUN
PASSED
FAILED
BLOCKED
DEFECTS
SECURITY_OBSERVATIONS
RELEASE_RECOMMENDATION
```

---

# 53. Definition of Test Completion

A feature is considered tested when:

- [ ] requirement IDs mapped,
- [ ] happy path tested,
- [ ] validation failures tested,
- [ ] authorization tested,
- [ ] workspace isolation tested where relevant,
- [ ] lock behavior tested where relevant,
- [ ] audit tested for mutations,
- [ ] concurrency tested where relevant,
- [ ] API contract verified,
- [ ] relevant frontend behavior tested,
- [ ] regression suite updated.

---

# 54. Related Specifications

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
10_DEPLOYMENT_GUIDE.md
11_SECURITY_SPECIFICATION.md
12_CURRENT_STATUS.md
13_IMPLEMENTATION_ROADMAP.md
14_PROJECT_USAGE_SCENARIOS.md
```
