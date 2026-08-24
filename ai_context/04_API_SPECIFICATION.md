# API Specification

**File:** `04_API_SPECIFICATION.md`  
**Status:** Normative  
**System:** Metadata-Driven Enterprise Architecture Management Platform  
**Version:** 1.0  
**Protocol:** REST over HTTPS  
**Base Path:** `/api/v1`  
**Primary Format:** JSON  
**API Description Format:** OpenAPI 3.1  
**Audience:** Backend engineers, frontend engineers, AI coding agents, QA engineers, security reviewers

---

# 1. Purpose

This document defines the public HTTP API contract between:

- web frontend,
- backend services,
- background workers where applicable,
- future external integrations,
- AI agents interacting with application APIs.

The API SHALL preserve:

- metadata-driven architecture,
- strict workspace isolation,
- server-side authorization,
- stable versioned contracts,
- consistent error handling,
- pagination for large collections,
- safe asynchronous workflows for expensive operations.

This document SHALL be interpreted together with:

- `01_ARCHITECTURE_RULES.md`
- `02_SYSTEM_REQUIREMENTS.md`
- `03_DATABASE_SPECIFICATION.md`
- `05_BACKEND_SPECIFICATION.md`
- `06_FRONTEND_SPECIFICATION.md`
- `11_SECURITY_SPECIFICATION.md`

---

# 2. API Design Principles

## API-RULE-001 — Versioned Base Path

All public REST APIs SHALL be exposed under:

```text
/api/v1
```

Breaking contract changes require:

- `/api/v2`, or
- an approved compatibility/migration strategy.

---

## API-RULE-002 — JSON Envelope

All standard JSON responses SHALL follow:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": {}
}
```

Error responses SHALL follow:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "RESOURCE_LOCKED",
    "message": "این مورد در مرحله قفل‌شده قرار دارد و قابل ویرایش نیست.",
    "details": {}
  },
  "meta": {
    "request_id": "0191..."
  }
}
```

Binary file streams and HTTP redirects MAY bypass the JSON envelope where explicitly documented.

---

## API-RULE-003 — Correlation ID

Every API response SHOULD include:

```http
X-Request-ID: <uuid>
```

If the client provides a valid request ID, the server MAY propagate it.

---

## API-RULE-004 — Authentication

Protected endpoints SHALL require:

```http
Authorization: Bearer <access-token>
```

Unauthenticated access SHALL return:

```text
401 Unauthorized
```

---

## API-RULE-005 — Authorization

Authentication alone is insufficient.

Each protected operation SHALL evaluate:

- effective permission,
- workspace membership,
- resource scope,
- lock state where applicable.

---

## API-RULE-006 — Content Type

JSON endpoints SHALL use:

```http
Content-Type: application/json
```

Uploads SHALL use:

```http
multipart/form-data
```

---

## API-RULE-007 — Pagination

Potentially large collection endpoints SHALL use bounded pagination.

Default query parameters:

```text
page=1
page_size=50
```

Server maximum:

```text
page_size <= 200
```

Response metadata:

```json
{
  "meta": {
    "page": 1,
    "page_size": 50,
    "total": 217,
    "total_pages": 5
  }
}
```

Cursor pagination MAY replace page-based pagination for endpoints where required by scale.

---

## API-RULE-008 — Localization Boundary

Public API paths, field names, enum values, permission names, stable error codes,
and OpenAPI operation identifiers SHALL remain English. String values MAY contain
Persian Unicode.

For the Persian-first MVP, safe user-facing `error.message` values SHALL be
Persian (`fa-IR`) while `error.code` remains an English stable contract
identifier. Clients SHALL branch on `code`, never on translated `message`.
Backend logs and exception diagnostics SHALL remain English and SHALL not expose
localized messages as their only diagnostic context.

API timestamps SHALL remain ISO 8601 and numeric fields SHALL remain JSON numbers;
presentation formatting belongs to the frontend localization layer.

---

# 3. HTTP Status Codes

The API SHALL use standard HTTP semantics.

| Status | Meaning |
|---|---|
| 200 | Successful read/update |
| 201 | Resource created |
| 202 | Accepted for asynchronous processing |
| 204 | Successful operation with no body |
| 400 | Malformed request |
| 401 | Authentication required/failed |
| 403 | Authenticated but forbidden |
| 404 | Resource not found or not visible |
| 409 | Business/concurrency conflict |
| 413 | Payload/file too large |
| 415 | Unsupported media type |
| 422 | Semantic validation failure |
| 423 | Locked resource |
| 429 | Rate limit exceeded |
| 500 | Unexpected internal error |
| 503 | Dependency/service unavailable |

The server SHALL NOT return `200 OK` for a failed business operation.

---

# 4. Common Data Types

## 4.1 UUID

Public IDs are represented as strings:

```json
"0191d3b2-..."
```

---

## 4.2 Timestamp

All API timestamps SHALL be ISO 8601 with timezone:

```json
"2026-08-21T14:10:33Z"
```

---

## 4.3 Version

Mutable resources MAY include:

```json
"version": 4
```

Clients MAY supply:

```http
If-Match: "4"
```

or equivalent request fields for concurrency-sensitive operations.

---

# 5. Standard Error Codes

The following error codes SHALL be reserved:

```text
AUTH_INVALID_CREDENTIALS
AUTH_TOKEN_EXPIRED
AUTH_REQUIRED

PERMISSION_DENIED
WORKSPACE_ACCESS_DENIED

RESOURCE_NOT_FOUND
RESOURCE_CONFLICT
STALE_VERSION
RESOURCE_LOCKED

VALIDATION_ERROR
INVALID_METADATA
INVALID_RELATIONSHIP
HIERARCHY_CYCLE

FILE_TOO_LARGE
FILE_TYPE_NOT_ALLOWED
FILE_SCAN_FAILED

IMPORT_VALIDATION_FAILED
IMPORT_CONFLICTS_UNRESOLVED
IMPORT_ALREADY_COMMITTED

FORM_NOT_PUBLISHED
FORM_VERSION_CONFLICT

RATE_LIMITED
INTERNAL_ERROR
DEPENDENCY_UNAVAILABLE
```

Error `details` SHOULD contain field-specific information when appropriate.

Example:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "One or more fields are invalid.",
    "details": {
      "fields": [
        {
          "field": "risk_level",
          "code": "INVALID_ENUM_VALUE",
          "message": "Allowed values are LOW, MEDIUM, HIGH."
        }
      ]
    }
  },
  "meta": {
    "request_id": "..."
  }
}
```

---

# 6. Authentication API

# 6.1 POST /auth/login

Authenticate a user.

### Authentication

Public.

### Request

```json
{
  "username": "analyst1",
  "password": "********"
}
```

### Success

```text
200 OK
```

```json
{
  "success": true,
  "data": {
    "access_token": "...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "...",
      "username": "analyst1",
      "display_name": "Analyst One",
      "roles": ["ANALYST"]
    }
  },
  "error": null,
  "meta": {}
}
```

### Errors

- `AUTH_INVALID_CREDENTIALS`
- `RATE_LIMITED`

---

# 6.2 POST /auth/refresh

Rotate the HttpOnly refresh cookie and return a new short-lived access token.

### Authentication

Valid refresh cookie and allowed request origin required. Bearer authentication is not
required because the access token may have expired.

### Success

Same response shape as login. The old refresh token is invalidated and a replacement
refresh cookie is set.

### Errors

- `AUTH_REQUIRED`
- `AUTH_TOKEN_EXPIRED`

---

# 6.3 POST /auth/logout

Terminate current session where server-side revocation applies.

### Authentication

Required.

### Success

```text
204 No Content
```

---

# 6.4 GET /auth/me

Return authenticated user context.

### Response

```json
{
  "success": true,
  "data": {
    "id": "...",
    "username": "analyst1",
    "display_name": "Analyst One",
    "roles": ["ANALYST"],
    "permissions": [
      "ENTITY_CREATE",
      "ENTITY_READ",
      "FORM_SUBMIT"
    ],
    "workspaces": [
      {
        "id": "...",
        "name": "EA Project"
      }
    ]
  },
  "error": null,
  "meta": {}
}
```

---

# 6.5 POST /users/{user_id}/roles

Assign a global role using an explicit `role_code` request field.

### Permission

```text
IDENTITY_MANAGE
```

The actor SHALL possess every effective permission granted by the target role.
Successful material changes SHALL create an append-only `ROLE_ASSIGNED` audit record
in the same transaction.

---

# 6.6 DELETE /users/{user_id}/roles/{role_code}

Remove a global role. Requires `IDENTITY_MANAGE` and creates an append-only
`ROLE_REMOVED` audit record in the same transaction when state changes.

---

# 7. Workspace API

# 7.1 POST /workspaces

Create workspace.

### Permission

```text
WORKSPACE_CREATE
```

### Request

```json
{
  "name": "Digital Government Transformation",
  "slug": "digital-government-transformation",
  "description": "Enterprise architecture engagement"
}
```

### Success

```text
201 Created
```

Workspace creation, creator membership, and `WORKSPACE_CREATED` audit insertion SHALL
commit in one transaction. The creator becomes an active member; no global role alone
grants access to unrelated workspaces.

---

# 7.2 GET /workspaces

List accessible workspaces.

### Query Parameters

```text
page
page_size
status
search
```

### Authorization

Returns only workspaces accessible to the caller.

The collection SHALL be bounded and membership-scoped. A global `WORKSPACE_READ`
permission does not bypass active workspace membership.

---

# 7.3 GET /workspaces/{workspace_id}

Retrieve workspace.

### Permission

Workspace read access.

---

# 7.4 PATCH /workspaces/{workspace_id}

Update mutable workspace fields.

### Request

```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "version": 3
}
```

### Errors

- `STALE_VERSION`
- `WORKSPACE_ACCESS_DENIED`

Successful updates increment `version` atomically and create a `WORKSPACE_UPDATED`
audit record in the same transaction.

---

# 7.5 GET /workspaces/{workspace_id}/members

List workspace members.

### Permission

```text
WORKSPACE_MANAGE
```

---

# 7.6 POST /workspaces/{workspace_id}/members

Add member.

### Permission

```text
WORKSPACE_MANAGE
```

### Request

```json
{
  "user_id": "...",
  "role_id": "..."
}
```

The acting user SHALL possess every effective permission granted by the selected
workspace role. Membership creation and `WORKSPACE_MEMBER_ADDED` audit insertion SHALL
commit in one transaction.

---

# 7.7 DELETE /workspaces/{workspace_id}/members/{user_id}

Remove workspace membership.

Requires `WORKSPACE_MANAGE`. Membership removal and `WORKSPACE_MEMBER_REMOVED` audit
insertion SHALL commit in one transaction.

---

# 8. Metadata API

# 8.1 POST /workspaces/{workspace_id}/entity-types

Create metadata-defined entity type.

### Permission

```text
METADATA_MANAGE
```

### Request

```json
{
  "key": "business_process",
  "name": "Business Process",
  "plural_name": "Business Processes",
  "description": "A configurable process concept",
  "configuration": {}
}
```

### Success

```text
201 Created
```

### Validation

- key unique within workspace,
- key must follow stable naming rules.

---

# 8.2 GET /workspaces/{workspace_id}/entity-types

List entity types.

### Query

```text
page
page_size
active
search
```

---

# 8.3 GET /entity-types/{entity_type_id}

Retrieve entity type and metadata summary.

---

# 8.4 PATCH /entity-types/{entity_type_id}

Update entity type.

Stable keys SHOULD NOT be changed after persistent usage unless explicitly supported.

The MVP treats `key` as immutable. Updates require the current `version`; stale writes
return `STALE_VERSION`.

---

# 8.4.1 DELETE /entity-types/{entity_type_id}?version={version}

Logically archive an entity type. The operation requires `METADATA_MANAGE`, an active
membership in the owning workspace, the current resource version, and writes an audit
record in the same transaction. Archived types are excluded from normal lookup.

---

# 8.5 POST /entity-types/{entity_type_id}/attributes

Create attribute.

### Request

```json
{
  "key": "risk_level",
  "label": "Risk Level",
  "data_type": "ENUM",
  "is_required": true,
  "validation_config": {},
  "display_config": {
    "options": [
      {"value": "LOW", "label": "Low"},
      {"value": "MEDIUM", "label": "Medium"},
      {"value": "HIGH", "label": "High"}
    ]
  }
}
```

---

# 8.6 GET /entity-types/{entity_type_id}/attributes

Return active attributes in display order.

---

# 8.7 PATCH /attributes/{attribute_id}

Update attribute metadata.

Changes SHALL be validated against existing data where necessary.

The MVP keeps `key` and `data_type` immutable. Mutable fields require the current
`version`; all changes require `METADATA_MANAGE` and are audited atomically.

---

# 8.8 DELETE /attributes/{attribute_id}

Logical deactivation is preferred if persistent values exist.

The MVP uses `DELETE /attributes/{attribute_id}?version={version}` as a logical
deactivation and excludes deactivated definitions from the active ordered list.

For ENUM and MULTI_ENUM, `display_config.options` is a required non-empty list of
unique `{value, label}` objects. MVP inheritance uses a `source` object with `scope`,
stable `attribute`, and optional `entity_type_id`, plus `mode` (`prefill` or
`read_only`). Referenced metadata must exist in the same workspace.

---

# 9. Entity API

# 9.1 POST /workspaces/{workspace_id}/entities

Create generic entity.

### Permission

```text
ENTITY_CREATE
```

### Request

```json
{
  "entity_type_id": "...",
  "parent_id": null,
  "name": "Certificate Issuing Service",
  "description": "Service description",
  "attributes": {
    "service_code": "SVC-102",
    "owner": "Organization A"
  }
}
```

### Server Validation

- workspace access,
- entity type belongs to workspace,
- parent belongs to workspace,
- metadata fields valid,
- required attributes present,
- hierarchy rules satisfied.

### Success

```text
201 Created
```

```json
{
  "success": true,
  "data": {
    "id": "...",
    "workspace_id": "...",
    "entity_type": {
      "id": "...",
      "key": "business_service",
      "name": "Business Service"
    },
    "parent_id": null,
    "name": "Certificate Issuing Service",
    "attributes": {
      "service_code": "SVC-102",
      "owner": "Organization A"
    },
    "status": "ACTIVE",
    "version": 1
  },
  "error": null,
  "meta": {}
}
```

---

# 9.2 GET /entities/{entity_id}

Retrieve entity.

### Include Options

Optional:

```text
include=attributes,relationships,documents,forms
```

Server MAY restrict costly include combinations.

The MVP response includes the entity type summary (`id`, stable `key`, and display
`name`) alongside `entity_type_id`. Access requires active workspace membership and
effective `ENTITY_READ`.

---

# 9.2.1 GET /workspaces/{workspace_id}/entities

Return a bounded workspace-scoped entity collection. Supported query parameters are:

```text
page
page_size (maximum 200)
search
status
entity_type_id
parent_id
```

Search preserves canonical names and compares a separately normalized expression so
the specified Arabic/Persian Yeh, Kaf, joining-mark, diacritic, whitespace, and numeral
variants match consistently. Both item and count queries require active membership;
effective `ENTITY_READ` is enforced by the service.

---

# 9.3 PATCH /entities/{entity_id}

Update entity.

### Request

```json
{
  "name": "Updated Name",
  "attributes": {
    "risk_level": "HIGH"
  },
  "version": 5
}
```

### Errors

- `RESOURCE_LOCKED`
- `STALE_VERSION`
- `VALIDATION_ERROR`

The MVP treats `attributes` as a partial dynamic-field update: validated supplied
keys are merged with existing attributes, while unknown and read-only keys are
rejected. `name`, `description`, and attributes are updated with the current
`version`; successful mutation increments the version and atomically audits before
and after state. Reparenting is handled by the hierarchy API rather than this patch.

---

# 9.4 DELETE /entities/{entity_id}?version={version}

Logically archive an active entity. The operation requires active membership,
effective `ENTITY_ARCHIVE`, and the current version. It sets status to `ARCHIVED`,
preserves the row and dynamic values, increments the version, and writes an audit
record in the same transaction.

### Permission

```text
ENTITY_ARCHIVE
```

### Errors

- child dependency conflict,
- locked phase,
- permission denied.

---

# 9.5 GET /workspaces/{workspace_id}/entities

Search/list entities.

### Query Parameters

```text
page
page_size
entity_type_id
parent_id
status
search
sort
```

Example:

```text
GET /api/v1/workspaces/{id}/entities?entity_type_id=...&search=certificate&page=1&page_size=50
```

---

# 9.6 GET /workspaces/{workspace_id}/entities/tree

Retrieve hierarchy.

### Query

```text
root_id
depth
include_type
```

`depth` MAY be used to constrain transfer size.

The server SHALL use database-level hierarchy traversal.

The response is a flat, path-ordered node collection so clients can render the
hierarchy without backend-specific nesting assumptions. Each node includes `depth`,
its complete `path`, and `has_children`. When `root_id` is omitted, traversal starts
at every non-deleted root in the workspace; when supplied, depth zero is that root.
`depth` is relative to the selected root(s), and `include_type=false` omits the
optional entity-type summary while retaining `entity_type_id`. Access requires an
active workspace membership and effective `ENTITY_READ`; a root outside the scoped
workspace is returned as `RESOURCE_NOT_FOUND`.

---

# 9.7 PATCH /entities/{entity_id}/parent

Reparent entity.

### Request

```json
{
  "parent_id": "... or null to move to a root",
  "version": 5
}
```

### Validation

- same workspace,
- no cycle,
- permission,
- lock policy.

Hierarchy mutations are serialized per workspace before the recursive ancestor
check, then applied with optimistic concurrency. A successful move preserves the
entity identifier, increments `version`, and atomically audits before/after state.
An invisible, cross-workspace, archived, or deleted proposed parent is reported as
`RESOURCE_NOT_FOUND`; self-parenting and descendant-parenting both return
`HIERARCHY_CYCLE`.

### Error

```text
409 HIERARCHY_CYCLE
```

---

# 10. Relationship API

# 10.1 POST /workspaces/{workspace_id}/relationship-types

Create relationship metadata.

### Request

```json
{
  "key": "uses",
  "name": "Uses",
  "directionality": "DIRECTED",
  "source_type_id": null,
  "target_type_id": null,
  "configuration": {
    "allow_duplicates": false
  }
}
```

`configuration.allow_duplicates` defaults to `true`. When explicitly `false`,
creation SHALL reject an active relationship with the same type and ordered endpoints.
For undirected relationship types, reversed endpoints are the same duplicate pair.

---

# 10.2 GET /workspaces/{workspace_id}/relationship-types

List active relationship types.

---

# 10.3 POST /workspaces/{workspace_id}/relationships

Create entity relationship.

### Request

```json
{
  "relationship_type_id": "...",
  "source_entity_id": "...",
  "target_entity_id": "...",
  "attributes": {}
}
```

### Validation

- all resources in same workspace,
- relationship metadata constraints,
- source != target,
- duplicate prevention where configured.

---

# 10.4 GET /entities/{entity_id}/relationships

### Query

```text
direction=incoming|outgoing|both
relationship_type_id
page
page_size
```

---

# 10.5 DELETE /relationships/{relationship_id}

Remove logical relationship.

Audited.

---

# 11. Form Definition API

# 11.1 POST /workspaces/{workspace_id}/forms

Create draft form definition.

### Permission

```text
FORM_DESIGN
```

### Request

```json
{
  "key": "process_specification",
  "name": "Process Specification",
  "entity_type_id": "...",
  "description": "Specification form"
}
```

Creates:

```text
version_number = 1
lifecycle_status = DRAFT
```

---

# 11.2 GET /workspaces/{workspace_id}/forms

Query:

```text
entity_type_id
status
search
page
page_size
```

---

# 11.3 GET /forms/{form_id}

Retrieve full definition.

---

# 11.4 PATCH /forms/{form_id}

Allowed only when form is DRAFT.

Mutable fields are `name`, `entity_type_id`, `description`, and `schema_json`.
For FORM-BE-001, `schema_json.sections` is an ordered list of generic section metadata:

```json
{
  "sections": [
    {
      "key": "general",
      "label": "General",
      "display_order": 10,
      "configuration": {}
    }
  ]
}
```

Section keys SHALL be unique within a definition. A field with `section_key` SHALL
reference one of these configured sections.

Attempting to edit a published form SHALL fail or create a new version through the version endpoint.

---

# 11.5 POST /forms/{form_id}/fields

Add field to draft form.

### Request

```json
{
  "key": "risk_level",
  "label": "Risk Level",
  "field_type": "ENUM",
  "attribute_definition_id": "...",
  "section_key": "risk",
  "display_order": 10,
  "is_required": true,
  "configuration": {},
  "visibility_rule": {},
  "validation_rule": {},
  "inheritance_rule": {}
}
```

Rule objects use a bounded, versioned JSON grammar. Empty objects mean no rule.
Conditional rules use `version: 1` plus `condition` (visibility) or `required_when`
(conditional requirement). Expressions support `all`, `any`, `not`, and comparisons:

```json
{
  "version": 1,
  "condition": {
    "path": "current.risk_level",
    "operator": "eq",
    "value": "HIGH"
  }
}
```

Comparison operators are `eq`, `neq`, `in`, `not_in`, `exists`, `gt`, `gte`, `lt`,
and `lte`. Paths resolve only through supplied metadata contexts such as `current`,
`parent`, `referenced`, and `user`.

Inheritance rules use exactly one of `source_path` or `static_value` and an explicit
mode of `READ_ONLY` or `EDITABLE_DEFAULT`:

```json
{
  "version": 1,
  "source_path": "parent.name",
  "mode": "READ_ONLY"
}
```

Unknown versions/operators/keys, invalid paths, more than 100 clauses, or nesting
deeper than 10 levels SHALL be rejected. Stored rules SHALL never execute code.

---

# 11.6 POST /forms/{form_id}/publish

Publish draft form.

### Permission

```text
FORM_DESIGN
```

### Success

```text
200 OK
```

Published form becomes immutable.

---

# 11.7 POST /forms/{form_id}/new-version

Create new draft version based on published form.

### Response

Returns new form ID/version.

---

# 11.8 GET /forms/{form_id}/render

Return normalized rendering contract.

### Optional Query

```text
entity_id
```

If `entity_id` is supplied, response MAY include:

- inherited values,
- current values,
- read-only evaluation,
- visibility evaluation context.

Draft definitions are renderable only by users with `FORM_DESIGN`; published
and retired definitions require `ENTITY_READ`. When supplied, `entity_id` MUST
resolve inside the form workspace and MUST match the configured entity type.

Each normalized field also returns:

- `visible` — the evaluated version-1 visibility result,
- `has_value` — distinguishes a present `null` from no candidate value,
- `value_source` — `CURRENT`, `INHERITED`, `DEFAULT`, or `NONE`,
- `visibility_rule` and `validation_rule` — the bounded JSON metadata needed for
  responsive client-side UX; backend submission validation remains authoritative.

Value precedence is current entity value, evaluated inheritance, attribute
default, then form-field `configuration.default_value`. Rule context exposes
`current`, `parent`, `referenced`, and `user`. Referenced context is keyed by the
stable entity-reference attribute/form-field key and contains only entities
resolved inside the same workspace.

Fields with no configured section are preserved in one final normalized section
whose `key` and `label` are `null`; clients SHALL render it without a heading.

### Response Example

```json
{
  "success": true,
  "data": {
    "form": {
      "id": "...",
      "key": "process_specification",
      "name": "Process Specification",
      "version_number": 2
    },
    "sections": [
      {
        "key": "general",
        "label": "General",
        "order": 10,
        "fields": [
          {
            "key": "service_name",
            "label": "Service Name",
            "type": "TEXT",
            "required": true,
            "read_only": true,
            "value": "Certificate Issuing Service",
            "configuration": {}
          }
        ]
      }
    ]
  },
  "error": null,
  "meta": {}
}
```

---

# 12. Form Instance API

# 12.1 POST /forms/{form_id}/instances

Create draft form instance for entity.

The form definition MUST be `PUBLISHED`. The caller requires `FORM_SUBMIT`, and
the entity MUST be active, in the same workspace, and match the form's optional
entity type. The created instance retains the exact immutable form-definition ID.

### Request

```json
{
  "entity_id": "..."
}
```

---

# 12.2 GET /form-instances/{instance_id}

Retrieve instance and associated form version.

The response includes instance status, values, optimistic-concurrency version,
and the immutable form key/name/version identity. Access requires active workspace
membership and `ENTITY_READ`.

---

# 12.3 PATCH /form-instances/{instance_id}

Save draft values.

The caller requires `FORM_SUBMIT`. Values are validated generically against field
types, configuration, evaluated visibility/read-only state, enum options,
references, and dynamic table columns. Unknown fields are rejected. Validation
errors use `VALIDATION_ERROR` with `details.fields` entries containing stable
`field` paths and `code` values. Concurrent edits return `STALE_VERSION`.

### Request

```json
{
  "values": {
    "risk_level": "HIGH",
    "stakeholders": [
      {
        "name": "Organization A",
        "power": "HIGH",
        "interest": "MEDIUM"
      }
    ]
  },
  "version": 2
}
```

---

# 12.4 POST /form-instances/{instance_id}/submit

Validate and submit.

### Errors

- `VALIDATION_ERROR`
- `RESOURCE_LOCKED`
- `STALE_VERSION`

---

# 12.5 POST /form-instances/{instance_id}/request-revision

Manager/reviewer action.

### Permission

Review permission defined in security specification.

---

# 13. Document API

# 13.1 POST /entities/{entity_id}/documents

Create logical document and upload first version.

### Content Type

```text
multipart/form-data
```

### Parts

```text
file
title
description
document_type
```

### Validation

- authorization,
- file size,
- extension,
- MIME type.

### Success

If synchronous metadata storage and async scan:

```text
202 Accepted
```

Response:

```json
{
  "success": true,
  "data": {
    "document_id": "...",
    "version_id": "...",
    "version_number": 1,
    "scan_status": "PENDING"
  },
  "error": null,
  "meta": {}
}
```

---

# 13.1A GET /entities/{entity_id}/documents

Return a paginated list of logical documents associated with an accessible entity.
The caller requires `DOCUMENT_READ`. Each item includes logical metadata and the
current immutable version summary; private object keys are never returned.

---

# 13.2 POST /documents/{document_id}/versions

Upload new immutable version.

Silent overwrite is prohibited.

### Content Type

```text
multipart/form-data
```

### Parts

```text
file
comment (optional)
```

The caller requires `DOCUMENT_UPLOAD`. The backend SHALL lock the logical
document while allocating the next version number, preserve all previous version
rows and objects, and advance `current_version_id` transactionally.

### Success

```text
202 Accepted
```

The response uses the same document/version/scan-status envelope as the first
version upload, with the newly allocated version number.

---

# 13.3 GET /documents/{document_id}

Retrieve logical document metadata.

The response includes the current-version summary but excludes private storage
object keys. Active workspace membership and `DOCUMENT_READ` are required.

---

# 13.4 GET /documents/{document_id}/versions

Paginated version history.

Versions are returned newest first and preserve immutable historical metadata.
Private object keys are excluded. Active workspace membership and `DOCUMENT_READ`
are required.

---

# 13.5 GET /document-versions/{version_id}/download

Authorized download.

The caller requires active workspace membership and `DOCUMENT_READ`. Authorization
and configured scan-state policy SHALL be evaluated before storage access is
generated. Inaccessible version identifiers SHALL NOT disclose cross-workspace
existence.

Implementation MAY:

- stream content, or
- return a short-lived presigned URL.

If returning URL:

```json
{
  "success": true,
  "data": {
    "url": "https://...",
    "expires_at": "2026-08-21T14:30:00Z"
  },
  "error": null,
  "meta": {}
}
```

Presigned access SHALL scope to the exact immutable object and expire within the
configured security bound of 5–15 minutes.

---

# 13.6 GET /document-versions/{version_id}/preview

Return preview availability.

Active workspace membership and `DOCUMENT_READ` are required, and configured
scan-state policy is enforced before any preview access is generated. CLEAN PDF,
PNG, and JPEG versions MAY use their exact immutable private object for safe
browser-native preview. Raw SVG SHALL NOT be returned for embedding. Office and
other conversion-dependent formats require an isolated background conversion
workflow and do not expose their original object as a preview.

Possible response:

```json
{
  "success": true,
  "data": {
    "status": "READY",
    "preview_type": "PDF",
    "url": "https://...",
    "expires_at": "..."
  },
  "error": null,
  "meta": {}
}
```

If conversion pending:

```text
202 Accepted
```

All ready preview URLs use the same bounded presigned-access policy as downloads.

---

# 14. Import API

The import API SHALL use a staged lifecycle.

# 14.0 Import Profiles

Reusable profiles and their mappings are managed through:

```text
POST /workspaces/{workspace_id}/import-profiles
GET /workspaces/{workspace_id}/import-profiles
GET /import-profiles/{profile_id}
PATCH /import-profiles/{profile_id}
```

Creating a profile stores its mappings atomically. A mapping targets exactly one
active attribute definition belonging to the profile entity type or one supported
generic entity system field (`name`, `description`, or `parent_id`). Replacing a
mapping set is atomic. Every operation requires active workspace membership and
`IMPORT_EXECUTE`; mutations are audited.

Create requests require a discriminated `matching_strategy`. Update requests may
replace it. Supported `type` values are `ENTITY_ID`, `UNIQUE_ATTRIBUTE`,
`COMPOSITE_KEY`, and `PARENT_AND_KEY`; referenced keys must correspond to mappings
in the same profile.

# 14.1 POST /workspaces/{workspace_id}/imports

Upload import file and create import job.

### Multipart Parts

```text
file
import_profile_id (optional)
```

### Success

```text
202 Accepted
```

```json
{
  "success": true,
  "data": {
    "import_job_id": "...",
    "status": "UPLOADED",
    "sheets": [
      {
        "name": "Sheet1",
        "row_count": 128,
        "columns": [
          {"name": "Name", "sample_values": ["Agency A", "Agency B"]}
        ]
      }
    ]
  },
  "error": null,
  "meta": {}
}
```

For files within the synchronous parser limits, upload performs safe structural
inspection and includes the result so the wizard can immediately enter its Inspect
step. This does not perform a dry run or mutate canonical entity data.

---

# 14.2 POST /imports/{import_job_id}/analyze

Analyze workbook/CSV.

### Success

```text
202 Accepted
```

or synchronous `200` for small files.

Result eventually contains:

```json
{
  "sheets": [
    {
      "name": "Stakeholders",
      "row_count": 128,
      "columns": [
        {
          "name": "Stakeholder Name",
          "sample_values": ["Agency A", "Agency B"]
        }
      ]
    }
  ]
}
```

---

# 14.3 PUT /imports/{import_job_id}/mapping

Store mapping.

### Request

```json
{
  "entity_type_id": "...",
  "sheet": "Stakeholders",
  "match_keys": ["stakeholder_name"],
  "mappings": [
    {
      "source_column": "Stakeholder Name",
      "target": {
        "type": "ATTRIBUTE",
        "key": "stakeholder_name"
      }
    }
  ]
}
```

---

# 14.4 POST /imports/{import_job_id}/dry-run

Mandatory before commit.

### Result

```json
{
  "success": true,
  "data": {
    "status": "READY_FOR_REVIEW",
    "summary": {
      "rows_read": 128,
      "rows_valid": 124,
      "rows_invalid": 4,
      "records_to_create": 80,
      "records_to_update": 32,
      "records_unchanged": 12,
      "conflicts": 9
    },
    "validation_errors": [],
    "conflicts": []
  },
  "error": null,
  "meta": {}
}
```

Large previews MAY be paginated.

---

# 14.5 GET /imports/{import_job_id}/conflicts

Paginated conflicts.

### Query

```text
page
page_size
resolution_status
```

---

# 14.6 PUT /imports/{import_job_id}/conflicts/{conflict_id}

Resolve conflict.

### Request

```json
{
  "resolution": "MERGE"
}
```

Allowed:

```text
MERGE
REPLACE
SKIP
```

---

# 14.7 POST /imports/{import_job_id}/resolve-bulk

Apply a resolution to a filtered conflict set.

Example:

```json
{
  "resolution": "SKIP",
  "conflict_ids": ["...", "..."]
}
```

---

# 14.8 POST /imports/{import_job_id}/commit

Commit import.

### Headers

Recommended:

```http
Idempotency-Key: <client-generated-key>
```

### Preconditions

- dry run completed,
- required conflicts resolved,
- user authorized,
- job not previously committed.

### Success

For background execution:

```text
202 Accepted
```

```json
{
  "success": true,
  "data": {
    "import_job_id": "...",
    "status": "COMMITTING"
  },
  "error": null,
  "meta": {}
}
```

---

# 14.9 GET /imports/{import_job_id}

Get job state and summary.

---

# 15. Phase API

# 15.1 POST /workspaces/{workspace_id}/phases

Create phase.

### Request

```json
{
  "key": "current_state",
  "name": "Current State Analysis",
  "sequence_number": 1,
  "description": "..."
}
```

---

# 15.2 GET /workspaces/{workspace_id}/phases

Return phases ordered by `sequence_number`.

---

# 15.3 PATCH /phases/{phase_id}

Update unlocked phase metadata.

---

# 15.4 POST /phases/{phase_id}/lock

### Permission

```text
PHASE_LOCK
```

### Success

```json
{
  "success": true,
  "data": {
    "id": "...",
    "is_locked": true,
    "locked_at": "...",
    "locked_by": "..."
  },
  "error": null,
  "meta": {}
}
```

---

# 15.5 POST /phases/{phase_id}/unlock

### Permission

```text
PHASE_UNLOCK
```

Audited.

---

# 15.6 POST /phases/{phase_id}/deliverables

Associate entity, document, or form instance.

Exactly one target SHALL be supplied.

---

# 16. Review API

# 16.1 POST /reviews/comments

Create review comment.

### Request

```json
{
  "workspace_id": "...",
  "resource_type": "FORM_INSTANCE",
  "resource_id": "...",
  "comment_text": "Please revise the stakeholder assessment."
}
```

---

# 16.2 GET /reviews/comments

Query by:

```text
workspace_id
resource_type
resource_id
status
page
page_size
```

---

# 16.3 POST /reviews/comments/{comment_id}/resolve

Resolve comment.

---

# 17. Dashboard API

# 17.1 POST /workspaces/{workspace_id}/dashboards

Create dashboard definition.

---

# 17.2 GET /workspaces/{workspace_id}/dashboards

List dashboards.

---

# 17.3 GET /dashboards/{dashboard_id}

Retrieve dashboard definition.

---

# 17.4 GET /dashboards/{dashboard_id}/data

Execute configured dashboard queries.

Response MAY include multiple widgets:

```json
{
  "success": true,
  "data": {
    "widgets": [
      {
        "id": "completed_processes",
        "type": "KPI",
        "value": 120
      },
      {
        "id": "risk_distribution",
        "type": "CHART",
        "series": [
          {"label": "High", "value": 8},
          {"label": "Medium", "value": 21},
          {"label": "Low", "value": 44}
        ]
      }
    ]
  },
  "error": null,
  "meta": {}
}
```

---

# 18. Audit API

# 18.1 GET /workspaces/{workspace_id}/audit

### Permission

```text
AUDIT_READ
```

### Query

```text
resource_type
resource_id
user_id
action
from
to
page
page_size
```

Audit API is read-only.

No public API SHALL modify audit records.

---

# 19. Background Job API

# 19.1 GET /jobs/{job_id}

Return background job status.

Response:

```json
{
  "success": true,
  "data": {
    "id": "...",
    "job_type": "DOCUMENT_PREVIEW",
    "status": "RUNNING",
    "created_at": "...",
    "started_at": "...",
    "completed_at": null,
    "result": null
  },
  "error": null,
  "meta": {}
}
```

---

# 19.2 POST /jobs/{job_id}/cancel

Optional P1 capability.

Only cancellable job types may accept cancellation.

---

# 20. Filtering and Sorting Convention

Collection endpoints SHOULD use consistent parameters.

Examples:

```text
search=certificate
status=ACTIVE
sort=name
order=asc
```

Multiple filters SHALL be combined with logical AND unless endpoint-specific behavior says otherwise.

Unsupported sort fields SHALL return validation errors.

---

# 21. Field Selection and Includes

To reduce payload size, selected endpoints MAY support:

```text
fields=id,name,status
include=relationships,documents
```

The server SHALL define allowed include values.

Unbounded graph expansion SHALL NOT be allowed.

---

# 22. Idempotency

The following endpoints SHOULD accept:

```http
Idempotency-Key
```

- import commit,
- document upload completion,
- asynchronous creation operations.

Same key + same authenticated principal + same logical operation SHALL not produce duplicate side effects.

---

# 23. Rate Limiting

Authentication and expensive APIs SHOULD support rate limits.

Potential targets:

- login,
- import analysis,
- preview generation,
- reporting,
- future AI endpoints.

Rate-limited responses SHALL use:

```text
429 Too Many Requests
```

and SHOULD include retry metadata.

---

# 24. OpenAPI Requirements

The backend SHALL generate or maintain an OpenAPI 3.1 specification.

Every public endpoint SHALL document:

- operation ID,
- summary,
- permissions,
- path parameters,
- query parameters,
- request schema,
- response schema,
- error responses,
- examples.

Machine-readable contract:

```text
contracts/openapi.yaml
```

SHALL become the source of integration validation.

---

# 25. API Security Rules

The API SHALL:

- validate all request data,
- enforce object-level authorization,
- never trust workspace IDs from the frontend without permission checks,
- never expose permanent object-storage credentials,
- avoid sensitive details in errors,
- log request IDs,
- audit material mutations.

---

# 26. API Acceptance Criteria

The API contract is implementation-ready when:

- [ ] all P0 requirements have endpoints or explicit internal-service ownership,
- [ ] every collection endpoint is bounded/paginated,
- [ ] JSON responses use the standard envelope,
- [ ] error codes are stable and documented,
- [ ] authorization requirements are defined,
- [ ] concurrency conflict behavior is defined,
- [ ] import requires dry-run before commit,
- [ ] document uploads create immutable versions,
- [ ] hierarchy reparenting rejects cycles,
- [ ] background job patterns are defined,
- [ ] OpenAPI 3.1 contract can be generated,
- [ ] frontend can integrate without knowledge of backend internals.

---

# 27. Requirement Traceability

```text
AUTH-FR-*  → /auth/*
WS-FR-*    → /workspaces/*
META-FR-*  → /entity-types/*, /attributes/*
ENT-FR-*   → /entities/*
HIER-FR-*  → /entities/tree, /entities/{id}/parent
REL-FR-*   → /relationship-types/*, /relationships/*
FORM-FR-*  → /forms/*
DATA-FR-*  → /form-instances/*
DOC-FR-*   → /documents/*, /document-versions/*
IMP-FR-*   → /imports/*
PHASE-FR-* → /phases/*
REV-FR-*   → /reviews/*
RPT-FR-*   → /dashboards/*
AUD-FR-*   → /audit/*
```

---

# 28. Related Specifications

```text
00_PROJECT_CONTEXT.md
01_ARCHITECTURE_RULES.md
02_SYSTEM_REQUIREMENTS.md
03_DATABASE_SPECIFICATION.md
05_BACKEND_SPECIFICATION.md
06_FRONTEND_SPECIFICATION.md
07_AI_AGENT_ROLES.md
08_TASK_BACKLOG.md
09_TEST_SPECIFICATION.md
10_DEPLOYMENT_GUIDE.md
11_SECURITY_SPECIFICATION.md
12_CURRENT_STATUS.md
contracts/openapi.yaml
```
