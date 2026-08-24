# Database Specification

**File:** `03_DATABASE_SPECIFICATION.md`  
**Status:** Normative  
**System:** Metadata-Driven Enterprise Architecture Management Platform  
**Version:** 1.0  
**Database:** PostgreSQL 16+  
**ORM Target:** SQLAlchemy 2.x  
**Migration Tool:** Alembic  
**Audience:** Database engineers, backend developers, AI coding agents, QA engineers, reviewers

---

# 1. Purpose

This document defines the normative relational database design for the platform.

The database SHALL preserve the core architectural rule:

> **User-configurable domain concepts are data, not schema.**

Therefore:

- platform concerns use fixed relational tables,
- user-defined enterprise concepts use generic metadata-driven tables,
- documents are stored in private object storage,
- PostgreSQL stores document metadata and references,
- all schema changes are migration-controlled.

This specification SHALL be read together with:

- `01_ARCHITECTURE_RULES.md`
- `02_SYSTEM_REQUIREMENTS.md`
- `04_API_SPECIFICATION.md`
- `05_BACKEND_SPECIFICATION.md`
- `11_SECURITY_SPECIFICATION.md`

---

# 2. Database Design Principles

## DB-RULE-001 — UUID Primary Keys

All externally addressable records SHALL use UUID primary keys.

Preferred PostgreSQL type:

```sql
uuid
```

Application UUID generation MAY use:

- UUIDv4, or
- UUIDv7 if adopted consistently.

---

## DB-RULE-002 — Timestamps

All persisted timestamps SHALL use:

```sql
timestamptz
```

and SHALL be stored in UTC.

Application presentation layers MAY convert to user-local time.

---

## DB-RULE-003 — Soft Deletion

Enterprise knowledge SHOULD be soft-deleted rather than physically deleted.

Where supported, tables SHALL use:

```sql
deleted_at timestamptz NULL
```

and optionally:

```sql
deleted_by uuid NULL
```

Hard deletion is reserved for disposable technical data.

---

## DB-RULE-004 — Optimistic Concurrency

Mutable core records SHOULD contain:

```sql
version integer NOT NULL DEFAULT 1
```

or an equivalent concurrency field.

Every successful update increments the version.

---

## DB-RULE-005 — Workspace Scoping

Workspace-owned records SHALL contain:

```sql
workspace_id uuid NOT NULL
```

unless their scope is explicitly global.

Indexes SHALL support workspace-filtered access.

---

## DB-RULE-006 — JSONB Use

JSONB MAY be used for:

- metadata configuration,
- validation configuration,
- rule expressions,
- schema snapshots,
- dynamic attribute values where appropriate,
- audit snapshots.

JSONB SHALL NOT be used to avoid modeling stable platform relationships.

---

## DB-RULE-007 — Persian Unicode and Search Values

PostgreSQL text, `varchar`, and JSONB fields containing user-authored or
metadata-configured labels SHALL accept Persian Unicode and SHALL NOT apply
ASCII-only constraints.

Canonical display values SHALL be preserved as entered. Search normalization
SHALL be performed separately so Arabic/Persian forms of Yeh (`ي`/`ی`) and Kaf
(`ك`/`ک`), zero-width non-joiner variants, diacritics, whitespace, and
Persian/Arabic numeral variants can match consistently. A normalized search
column or index MAY be introduced only with an Alembic migration and measured
query justification; it SHALL NOT replace the canonical display value.

---

# 3. PostgreSQL Extensions

Recommended extensions:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;
```

Optional future extensions:

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

`pg_trgm` MAY be used for fuzzy search.

---

# 4. Logical Schemas

The production database SHOULD use logical PostgreSQL schemas:

```text
core
security
metadata
content
workflow
audit
integration
```

For MVP, a single `public` schema MAY be used if migration complexity must remain low, but table names and module ownership SHALL remain consistent.

---

# 5. Security and Identity Tables

# 5.1 users

Purpose:

Store application users.

```sql
CREATE TABLE users (
    id uuid PRIMARY KEY,
    username citext NOT NULL UNIQUE,
    email citext NOT NULL UNIQUE,
    password_hash text NOT NULL,
    first_name varchar(120),
    last_name varchar(120),
    display_name varchar(255),
    is_active boolean NOT NULL DEFAULT true,
    failed_login_count integer NOT NULL DEFAULT 0,
    last_login_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    version integer NOT NULL DEFAULT 1
);
```

Indexes:

```sql
CREATE INDEX idx_users_active ON users(is_active);
```

Constraints:

- username unique,
- email unique,
- inactive users SHALL not authenticate.

---

# 5.2 roles

```sql
CREATE TABLE roles (
    id uuid PRIMARY KEY,
    code varchar(100) NOT NULL UNIQUE,
    name varchar(150) NOT NULL,
    description text,
    is_system boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now()
);
```

Initial role codes MAY include:

```text
SYSTEM_ADMIN
PROJECT_MANAGER
ANALYST
VIEWER
```

---

# 5.3 permissions

```sql
CREATE TABLE permissions (
    id uuid PRIMARY KEY,
    code varchar(150) NOT NULL UNIQUE,
    resource varchar(100) NOT NULL,
    action varchar(100) NOT NULL,
    description text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(resource, action)
);
```

Examples:

```text
ENTITY:CREATE
ENTITY:UPDATE
DOCUMENT:UPLOAD
PHASE:LOCK
PHASE:UNLOCK
FORM:DESIGN
```

---

# 5.4 user_roles

```sql
CREATE TABLE user_roles (
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id uuid NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, role_id)
);
```

---

# 5.5 role_permissions

```sql
CREATE TABLE role_permissions (
    role_id uuid NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id uuid NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (role_id, permission_id)
);
```

---

# 5.6 auth_sessions

`auth_sessions` stores revocable refresh-session state approved by ADR-0004.
Raw refresh tokens SHALL NOT be persisted; `token_hash` is the SHA-256 digest of a
cryptographically random opaque token.

```sql
CREATE TABLE auth_sessions (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash varchar(64) NOT NULL UNIQUE,
    token_family_id uuid NOT NULL,
    expires_at timestamptz NOT NULL,
    absolute_expires_at timestamptz NOT NULL,
    last_used_at timestamptz,
    revoked_at timestamptz,
    replaced_by_id uuid REFERENCES auth_sessions(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_auth_sessions_family ON auth_sessions(token_family_id);
CREATE INDEX idx_auth_sessions_expires ON auth_sessions(expires_at);
```

Refresh rotation and family revocation SHALL be transactional.

---

# 6. Workspace Tables

# 6.1 workspaces

```sql
CREATE TABLE workspaces (
    id uuid PRIMARY KEY,
    name varchar(255) NOT NULL,
    slug varchar(160) NOT NULL UNIQUE,
    description text,
    owner_id uuid REFERENCES users(id) ON DELETE SET NULL,
    status varchar(30) NOT NULL DEFAULT 'DRAFT',
    configuration jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    archived_at timestamptz,
    deleted_at timestamptz,
    version integer NOT NULL DEFAULT 1,
    CHECK (status IN ('DRAFT','ACTIVE','ARCHIVED'))
);
```

Indexes:

```sql
CREATE INDEX idx_workspaces_status ON workspaces(status);
CREATE INDEX idx_workspaces_owner ON workspaces(owner_id);
```

---

# 6.2 workspace_memberships

Workspace-specific access SHALL not rely solely on global roles.

```sql
CREATE TABLE workspace_memberships (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id uuid REFERENCES roles(id) ON DELETE SET NULL,
    status varchar(30) NOT NULL DEFAULT 'ACTIVE',
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(workspace_id, user_id),
    CHECK (status IN ('ACTIVE','SUSPENDED'))
);
```

Indexes:

```sql
CREATE INDEX idx_workspace_memberships_user
ON workspace_memberships(user_id);

CREATE INDEX idx_workspace_memberships_workspace
ON workspace_memberships(workspace_id);
```

---

# 7. Metadata Tables

# 7.1 entity_types

Defines all user-configurable enterprise concepts.

```sql
CREATE TABLE entity_types (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    key varchar(120) NOT NULL,
    name varchar(180) NOT NULL,
    plural_name varchar(180),
    description text,
    icon_key varchar(100),
    is_active boolean NOT NULL DEFAULT true,
    configuration jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_by uuid REFERENCES users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    version integer NOT NULL DEFAULT 1,
    UNIQUE(workspace_id, key)
);
```

Indexes:

```sql
CREATE INDEX idx_entity_types_workspace
ON entity_types(workspace_id);

CREATE INDEX idx_entity_types_active
ON entity_types(workspace_id, is_active);
```

Rules:

- `key` is stable and machine-oriented.
- `name` is user-facing and may change.
- hard deletion SHOULD be blocked when entities reference the type.

---

# 7.2 attribute_definitions

```sql
CREATE TABLE attribute_definitions (
    id uuid PRIMARY KEY,
    entity_type_id uuid NOT NULL
        REFERENCES entity_types(id) ON DELETE CASCADE,
    key varchar(120) NOT NULL,
    label varchar(180) NOT NULL,
    description text,
    data_type varchar(40) NOT NULL,
    is_required boolean NOT NULL DEFAULT false,
    is_read_only boolean NOT NULL DEFAULT false,
    default_value jsonb,
    validation_config jsonb NOT NULL DEFAULT '{}'::jsonb,
    display_config jsonb NOT NULL DEFAULT '{}'::jsonb,
    inheritance_config jsonb NOT NULL DEFAULT '{}'::jsonb,
    display_order integer NOT NULL DEFAULT 0,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    version integer NOT NULL DEFAULT 1,
    UNIQUE(entity_type_id, key),
    CHECK (
        data_type IN (
            'TEXT',
            'RICH_TEXT',
            'INTEGER',
            'DECIMAL',
            'BOOLEAN',
            'DATE',
            'DATETIME',
            'ENUM',
            'MULTI_ENUM',
            'USER_REFERENCE',
            'ENTITY_REFERENCE',
            'FILE_REFERENCE',
            'JSON',
            'TABLE'
        )
    )
);
```

Indexes:

```sql
CREATE INDEX idx_attribute_definitions_type
ON attribute_definitions(entity_type_id);

CREATE INDEX idx_attribute_definitions_active
ON attribute_definitions(entity_type_id, is_active);
```

---

# 8. Generic Entity Storage

# 8.1 entity_objects

Core table for all user-defined domain objects.

```sql
CREATE TABLE entity_objects (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL
        REFERENCES workspaces(id) ON DELETE CASCADE,
    entity_type_id uuid NOT NULL
        REFERENCES entity_types(id) ON DELETE RESTRICT,
    parent_id uuid
        REFERENCES entity_objects(id) ON DELETE RESTRICT,
    name varchar(255) NOT NULL,
    description text,
    status varchar(40) NOT NULL DEFAULT 'ACTIVE',
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_by uuid REFERENCES users(id) ON DELETE SET NULL,
    updated_by uuid REFERENCES users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    archived_at timestamptz,
    deleted_at timestamptz,
    version integer NOT NULL DEFAULT 1,
    CHECK (status IN ('ACTIVE','ARCHIVED','DELETED'))
);
```

Important note:

The preferred implementation MAY store dynamic properties in the indexed `attributes` JSONB column for MVP simplicity and performance.

If the project chooses a normalized value table, `entity_attribute_values` defined below MAY be used.

The implementation SHALL choose one canonical write model and SHALL NOT maintain two independent sources of truth.

Indexes:

```sql
CREATE INDEX idx_entity_objects_workspace
ON entity_objects(workspace_id)
WHERE deleted_at IS NULL;

CREATE INDEX idx_entity_objects_type
ON entity_objects(workspace_id, entity_type_id)
WHERE deleted_at IS NULL;

CREATE INDEX idx_entity_objects_parent
ON entity_objects(parent_id)
WHERE deleted_at IS NULL;

CREATE INDEX idx_entity_objects_name
ON entity_objects(workspace_id, name);

CREATE INDEX idx_entity_objects_attributes_gin
ON entity_objects USING gin(attributes);
```

Optional fuzzy search:

```sql
CREATE INDEX idx_entity_objects_name_trgm
ON entity_objects USING gin(name gin_trgm_ops);
```

The value indexed for Persian search SHALL use the shared backend search
normalization policy. Raw `lower(name)` or collation alone is not sufficient to
make Arabic/Persian code-point variants equivalent.

---

# 8.2 Optional entity_attribute_values

Use only if the architecture team chooses normalized dynamic values rather than the canonical JSONB strategy.

```sql
CREATE TABLE entity_attribute_values (
    id uuid PRIMARY KEY,
    entity_id uuid NOT NULL
        REFERENCES entity_objects(id) ON DELETE CASCADE,
    attribute_definition_id uuid NOT NULL
        REFERENCES attribute_definitions(id) ON DELETE RESTRICT,
    value_json jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(entity_id, attribute_definition_id)
);
```

The application SHALL NOT write the same logical attribute independently to both this table and `entity_objects.attributes`.

---

# 9. Hierarchy Integrity

# 9.1 Parent Workspace Rule

A child entity and parent entity SHALL belong to the same workspace.

This rule SHALL be enforced in service logic and SHOULD additionally be enforced by a database trigger if practical.

---

# 9.2 Cycle Prevention

Cycle prevention SHALL be implemented before parent changes.

Canonical database validation query:

```sql
WITH RECURSIVE ancestors AS (
    SELECT id, parent_id
    FROM entity_objects
    WHERE id = :new_parent_id

    UNION ALL

    SELECT e.id, e.parent_id
    FROM entity_objects e
    JOIN ancestors a ON e.id = a.parent_id
)
SELECT 1
FROM ancestors
WHERE id = :entity_id
LIMIT 1;
```

If a row is returned, reparenting SHALL be rejected.

---

# 9.3 Recursive Tree Query

Preferred pattern:

```sql
WITH RECURSIVE tree AS (
    SELECT
        id,
        parent_id,
        entity_type_id,
        name,
        0 AS depth,
        ARRAY[id] AS path
    FROM entity_objects
    WHERE id = :root_id
      AND deleted_at IS NULL

    UNION ALL

    SELECT
        child.id,
        child.parent_id,
        child.entity_type_id,
        child.name,
        tree.depth + 1,
        tree.path || child.id
    FROM entity_objects child
    JOIN tree ON child.parent_id = tree.id
    WHERE child.deleted_at IS NULL
)
SELECT *
FROM tree
ORDER BY path;
```

---

# 10. Relationship Model

# 10.1 relationship_types

```sql
CREATE TABLE relationship_types (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL
        REFERENCES workspaces(id) ON DELETE CASCADE,
    key varchar(120) NOT NULL,
    name varchar(180) NOT NULL,
    description text,
    directionality varchar(20) NOT NULL DEFAULT 'DIRECTED',
    source_type_id uuid REFERENCES entity_types(id) ON DELETE SET NULL,
    target_type_id uuid REFERENCES entity_types(id) ON DELETE SET NULL,
    configuration jsonb NOT NULL DEFAULT '{}'::jsonb,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(workspace_id, key),
    CHECK (directionality IN ('DIRECTED','UNDIRECTED'))
);
```

---

# 10.2 entity_relationships

```sql
CREATE TABLE entity_relationships (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL
        REFERENCES workspaces(id) ON DELETE CASCADE,
    relationship_type_id uuid NOT NULL
        REFERENCES relationship_types(id) ON DELETE RESTRICT,
    source_entity_id uuid NOT NULL
        REFERENCES entity_objects(id) ON DELETE CASCADE,
    target_entity_id uuid NOT NULL
        REFERENCES entity_objects(id) ON DELETE CASCADE,
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_by uuid REFERENCES users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    CHECK (source_entity_id <> target_entity_id)
);
```

Indexes:

```sql
CREATE INDEX idx_relationships_source
ON entity_relationships(source_entity_id)
WHERE deleted_at IS NULL;

CREATE INDEX idx_relationships_target
ON entity_relationships(target_entity_id)
WHERE deleted_at IS NULL;

CREATE INDEX idx_relationships_type
ON entity_relationships(relationship_type_id)
WHERE deleted_at IS NULL;
```

Optional uniqueness rule:

```sql
CREATE UNIQUE INDEX uq_relationship_active
ON entity_relationships(
    relationship_type_id,
    source_entity_id,
    target_entity_id
)
WHERE deleted_at IS NULL;
```

---

# 11. Dynamic Form Model

# 11.1 form_definitions

```sql
CREATE TABLE form_definitions (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL
        REFERENCES workspaces(id) ON DELETE CASCADE,
    entity_type_id uuid
        REFERENCES entity_types(id) ON DELETE RESTRICT,
    key varchar(120) NOT NULL,
    name varchar(255) NOT NULL,
    description text,
    version_number integer NOT NULL,
    lifecycle_status varchar(30) NOT NULL DEFAULT 'DRAFT',
    schema_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_by uuid REFERENCES users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    published_at timestamptz,
    retired_at timestamptz,
    UNIQUE(workspace_id, key, version_number),
    CHECK (version_number > 0),
    CHECK (lifecycle_status IN ('DRAFT','PUBLISHED','RETIRED'))
);
```

Rules:

- published forms are immutable,
- editing a published form creates another version.

---

# 11.2 form_fields

```sql
CREATE TABLE form_fields (
    id uuid PRIMARY KEY,
    form_definition_id uuid NOT NULL
        REFERENCES form_definitions(id) ON DELETE CASCADE,
    attribute_definition_id uuid
        REFERENCES attribute_definitions(id) ON DELETE SET NULL,
    key varchar(120) NOT NULL,
    label varchar(180) NOT NULL,
    field_type varchar(40) NOT NULL,
    section_key varchar(120),
    display_order integer NOT NULL DEFAULT 0,
    is_required boolean NOT NULL DEFAULT false,
    is_read_only boolean NOT NULL DEFAULT false,
    configuration jsonb NOT NULL DEFAULT '{}'::jsonb,
    visibility_rule jsonb NOT NULL DEFAULT '{}'::jsonb,
    validation_rule jsonb NOT NULL DEFAULT '{}'::jsonb,
    inheritance_rule jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE(form_definition_id, key)
);
```

---

# 11.3 form_instances

```sql
CREATE TABLE form_instances (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL
        REFERENCES workspaces(id) ON DELETE CASCADE,
    form_definition_id uuid NOT NULL
        REFERENCES form_definitions(id) ON DELETE RESTRICT,
    entity_id uuid NOT NULL
        REFERENCES entity_objects(id) ON DELETE CASCADE,
    status varchar(30) NOT NULL DEFAULT 'DRAFT',
    values_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    submitted_by uuid REFERENCES users(id) ON DELETE SET NULL,
    submitted_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    version integer NOT NULL DEFAULT 1,
    CHECK (status IN ('DRAFT','SUBMITTED','APPROVED','REVISION_REQUESTED'))
);
```

Indexes:

```sql
CREATE INDEX idx_form_instances_entity
ON form_instances(entity_id);

CREATE INDEX idx_form_instances_form
ON form_instances(form_definition_id);

CREATE INDEX idx_form_instances_values_gin
ON form_instances USING gin(values_json);
```

---

# 12. Repeating Sections

Repeating sections MAY be stored as nested arrays inside `form_instances.values_json` for MVP.

Example:

```json
{
  "stakeholders": [
    {
      "name": "Ministry A",
      "power": "HIGH",
      "interest": "MEDIUM"
    }
  ]
}
```

If row-level relational querying becomes a primary requirement, a normalized repeating-table model MAY later be introduced through an ADR.

The MVP SHALL NOT maintain duplicated row state in both JSONB and normalized tables.

---

# 13. Document Model

# 13.1 documents

Represents the logical document.

```sql
CREATE TABLE documents (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL
        REFERENCES workspaces(id) ON DELETE CASCADE,
    entity_id uuid
        REFERENCES entity_objects(id) ON DELETE CASCADE,
    title varchar(255) NOT NULL,
    description text,
    document_type varchar(100),
    lifecycle_status varchar(30) NOT NULL DEFAULT 'ACTIVE',
    current_version_id uuid,
    created_by uuid REFERENCES users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    CHECK (lifecycle_status IN ('ACTIVE','ARCHIVED','DELETED'))
);
```

`current_version_id` FK SHALL be added after `document_versions` exists.

---

# 13.2 document_versions

```sql
CREATE TABLE document_versions (
    id uuid PRIMARY KEY,
    document_id uuid NOT NULL
        REFERENCES documents(id) ON DELETE CASCADE,
    version_number integer NOT NULL,
    object_key text NOT NULL,
    original_file_name varchar(500) NOT NULL,
    content_type varchar(255),
    file_extension varchar(50),
    file_size_bytes bigint NOT NULL,
    checksum_sha256 varchar(64),
    storage_provider varchar(30) NOT NULL DEFAULT 'MINIO',
    scan_status varchar(30) NOT NULL DEFAULT 'PENDING',
    preview_status varchar(30) NOT NULL DEFAULT 'NOT_REQUESTED',
    uploaded_by uuid REFERENCES users(id) ON DELETE SET NULL,
    uploaded_at timestamptz NOT NULL DEFAULT now(),
    comment text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE(document_id, version_number),
    CHECK (file_size_bytes >= 0),
    CHECK (scan_status IN ('PENDING','CLEAN','INFECTED','FAILED')),
    CHECK (preview_status IN (
        'NOT_REQUESTED',
        'QUEUED',
        'READY',
        'FAILED'
    ))
);
```

Indexes:

```sql
CREATE INDEX idx_document_versions_document
ON document_versions(document_id, version_number DESC);

CREATE UNIQUE INDEX uq_document_object_key
ON document_versions(object_key);
```

Add current version FK:

```sql
ALTER TABLE documents
ADD CONSTRAINT fk_documents_current_version
FOREIGN KEY (current_version_id)
REFERENCES document_versions(id)
ON DELETE SET NULL;
```

---

# 14. Import Model

# 14.1 import_profiles

```sql
CREATE TABLE import_profiles (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL
        REFERENCES workspaces(id) ON DELETE CASCADE,
    entity_type_id uuid NOT NULL
        REFERENCES entity_types(id) ON DELETE RESTRICT,
    name varchar(255) NOT NULL,
    description text,
    source_type varchar(20) NOT NULL,
    matching_strategy jsonb NOT NULL DEFAULT '{}'::jsonb,
    configuration jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_by uuid REFERENCES users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (source_type IN ('XLSX','CSV'))
);
```

---

# 14.2 import_mappings

```sql
CREATE TABLE import_mappings (
    id uuid PRIMARY KEY,
    import_profile_id uuid NOT NULL
        REFERENCES import_profiles(id) ON DELETE CASCADE,
    source_sheet varchar(255),
    source_column varchar(255) NOT NULL,
    target_attribute_definition_id uuid
        REFERENCES attribute_definitions(id) ON DELETE RESTRICT,
    target_system_field varchar(120),
    transformation_config jsonb NOT NULL DEFAULT '{}'::jsonb,
    display_order integer NOT NULL DEFAULT 0,
    CHECK (
        target_attribute_definition_id IS NOT NULL
        OR target_system_field IS NOT NULL
    )
);
```

---

# 14.3 import_jobs

```sql
CREATE TABLE import_jobs (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL
        REFERENCES workspaces(id) ON DELETE CASCADE,
    import_profile_id uuid
        REFERENCES import_profiles(id) ON DELETE SET NULL,
    source_object_key text NOT NULL,
    status varchar(30) NOT NULL DEFAULT 'UPLOADED',
    dry_run_summary jsonb,
    final_summary jsonb,
    requested_by uuid REFERENCES users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    started_at timestamptz,
    completed_at timestamptz,
    idempotency_key varchar(255),
    error_message text,
    CHECK (status IN (
        'UPLOADED',
        'ANALYZING',
        'READY_FOR_REVIEW',
        'VALIDATION_FAILED',
        'READY_TO_COMMIT',
        'COMMITTING',
        'COMPLETED',
        'FAILED',
        'CANCELLED'
    ))
);
```

Optional uniqueness:

```sql
CREATE UNIQUE INDEX uq_import_jobs_idempotency
ON import_jobs(workspace_id, idempotency_key)
WHERE idempotency_key IS NOT NULL;
```

---

# 14.4 import_conflicts

```sql
CREATE TABLE import_conflicts (
    id uuid PRIMARY KEY,
    import_job_id uuid NOT NULL
        REFERENCES import_jobs(id) ON DELETE CASCADE,
    row_number integer,
    entity_id uuid REFERENCES entity_objects(id) ON DELETE SET NULL,
    attribute_key varchar(120),
    existing_value jsonb,
    imported_value jsonb,
    resolution varchar(20),
    resolved_by uuid REFERENCES users(id) ON DELETE SET NULL,
    resolved_at timestamptz,
    CHECK (
        resolution IS NULL
        OR resolution IN ('MERGE','REPLACE','SKIP')
    )
);
```

Indexes:

```sql
CREATE INDEX idx_import_conflicts_job
ON import_conflicts(import_job_id);
```

---

# 15. Phase and Workflow Model

# 15.1 phases

```sql
CREATE TABLE phases (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL
        REFERENCES workspaces(id) ON DELETE CASCADE,
    key varchar(120) NOT NULL,
    name varchar(255) NOT NULL,
    description text,
    sequence_number integer NOT NULL,
    status varchar(30) NOT NULL DEFAULT 'PLANNED',
    is_locked boolean NOT NULL DEFAULT false,
    locked_by uuid REFERENCES users(id) ON DELETE SET NULL,
    locked_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    version integer NOT NULL DEFAULT 1,
    UNIQUE(workspace_id, key),
    UNIQUE(workspace_id, sequence_number),
    CHECK (status IN ('PLANNED','IN_PROGRESS','COMPLETED','ARCHIVED'))
);
```

---

# 15.2 phase_deliverables

```sql
CREATE TABLE phase_deliverables (
    id uuid PRIMARY KEY,
    phase_id uuid NOT NULL
        REFERENCES phases(id) ON DELETE CASCADE,
    entity_id uuid
        REFERENCES entity_objects(id) ON DELETE CASCADE,
    document_id uuid
        REFERENCES documents(id) ON DELETE CASCADE,
    form_instance_id uuid
        REFERENCES form_instances(id) ON DELETE CASCADE,
    is_required boolean NOT NULL DEFAULT true,
    status varchar(30) NOT NULL DEFAULT 'PENDING',
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (
        ((entity_id IS NOT NULL)::integer
        + (document_id IS NOT NULL)::integer
        + (form_instance_id IS NOT NULL)::integer) = 1
    ),
    CHECK (status IN (
        'PENDING',
        'SUBMITTED',
        'APPROVED',
        'REVISION_REQUESTED'
    ))
);
```

The initial `phase_deliverables` structure is an MVP association. Before governed
delivery is implemented, `DEL-DB-001` SHALL evolve it through Alembic into a generic
versioned deliverable/submission model. The four-state check above SHALL NOT be used
as the full contractor-review, external-review, or acceptance workflow.

---

# 15.3 Versioned Governance Model

`GOV-DB-001`, `DEL-DB-001`, and `ACC-DB-001` SHALL define normalized generic records
for:

```text
workflow definitions and immutable published versions
state/transition definitions and policy configuration
workflow instances and append-only transition events
generic deliverables and scoped assignments
immutable submission/resubmission packages and withdrawals
version-bound review outcomes and sign-offs
phase/final acceptance packages and decisions
acceptance conditions, evidence, verification, and closure
```

Every operational record SHALL carry `workspace_id` directly when needed for secure
querying and composite workspace integrity. Referenced entities, documents, forms,
phases, users, and configuration SHALL belong to the same workspace. Transition and
decision history SHALL not be updated in place.

Workflow status names and transition graphs are metadata. Stable engine-level states
MAY be constrained where required for idempotency, publication, or immutable event
integrity, but project-specific workflow labels SHALL NOT become SQL check values.

`WORK-DB-001` and `COM-DB-001` SHALL similarly use generic workspace-scoped work
items/dependencies/risks/issues and explicit-kind communication/notification records.
Dependencies require cycle prevention. Notification and thread targets require
validated polymorphic references or a supported typed target registry.

---

# 16. Review and Comment Model

# 16.1 review_comments

```sql
CREATE TABLE review_comments (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL
        REFERENCES workspaces(id) ON DELETE CASCADE,
    resource_type varchar(50) NOT NULL,
    resource_id uuid NOT NULL,
    author_id uuid REFERENCES users(id) ON DELETE SET NULL,
    comment_text text NOT NULL,
    status varchar(30) NOT NULL DEFAULT 'OPEN',
    created_at timestamptz NOT NULL DEFAULT now(),
    resolved_at timestamptz,
    resolved_by uuid REFERENCES users(id) ON DELETE SET NULL,
    CHECK (status IN ('OPEN','RESOLVED'))
);
```

Indexes:

```sql
CREATE INDEX idx_review_comments_resource
ON review_comments(resource_type, resource_id);
```

Because `resource_id` is polymorphic, referential integrity SHALL be enforced in service logic.

---

# 17. Dashboard Model

# 17.1 dashboards

```sql
CREATE TABLE dashboards (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL
        REFERENCES workspaces(id) ON DELETE CASCADE,
    name varchar(255) NOT NULL,
    description text,
    configuration jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_by uuid REFERENCES users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    version integer NOT NULL DEFAULT 1
);
```

---

# 18. Audit Model

# 18.1 audit_logs

Audit logs are append-only.

```sql
CREATE TABLE audit_logs (
    id uuid PRIMARY KEY,
    request_id uuid,
    workspace_id uuid,
    user_id uuid,
    action varchar(80) NOT NULL,
    resource_type varchar(100) NOT NULL,
    resource_id uuid,
    source varchar(40) NOT NULL DEFAULT 'API',
    before_state jsonb,
    after_state jsonb,
    client_ip inet,
    user_agent text,
    created_at timestamptz NOT NULL DEFAULT now()
);
```

Indexes:

```sql
CREATE INDEX idx_audit_workspace_time
ON audit_logs(workspace_id, created_at DESC);

CREATE INDEX idx_audit_resource
ON audit_logs(resource_type, resource_id, created_at DESC);

CREATE INDEX idx_audit_user
ON audit_logs(user_id, created_at DESC);
```

Rules:

- no application UPDATE endpoint,
- no application DELETE endpoint,
- database role used by application SHOULD not have UPDATE/DELETE privileges on audit logs if operationally practical.

---

# 19. Background Job Model

# 19.1 background_jobs

```sql
CREATE TABLE background_jobs (
    id uuid PRIMARY KEY,
    workspace_id uuid REFERENCES workspaces(id) ON DELETE CASCADE,
    job_type varchar(100) NOT NULL,
    status varchar(30) NOT NULL DEFAULT 'QUEUED',
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    result jsonb,
    error_message text,
    requested_by uuid REFERENCES users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    started_at timestamptz,
    completed_at timestamptz,
    retry_count integer NOT NULL DEFAULT 0,
    idempotency_key varchar(255),
    CHECK (status IN (
        'QUEUED',
        'RUNNING',
        'SUCCEEDED',
        'FAILED',
        'CANCELLED'
    ))
);
```

---

# 20. Referential Actions

Recommended default rules:

| Relationship | ON DELETE |
|---|---|
| workspace → workspace-owned records | CASCADE |
| entity_type → entity_objects | RESTRICT |
| entity → child entity parent_id | RESTRICT |
| entity → entity_relationships | CASCADE |
| entity → documents | CASCADE or soft delete policy |
| form definition → instances | RESTRICT |
| document → versions | CASCADE |
| user → authored business data | SET NULL |
| role → membership | CASCADE |

Production deletion policy SHALL favor soft deletion for workspace and entity records before physical deletion is attempted.

---

# 21. Indexing Strategy

Mandatory indexes SHALL cover:

- workspace foreign keys,
- entity type filters,
- hierarchy parent lookup,
- entity names,
- relationship source/target,
- document version lookup,
- form instance lookup,
- import conflict lookup,
- audit resource/user/time lookup.

GIN indexes SHOULD support JSONB query patterns only where actual query use cases justify them.

Agents SHALL NOT add large numbers of speculative indexes without query evidence.

---

# 22. Unique Constraint Strategy

Stable keys SHALL be unique in their intended scope.

Examples:

```text
entity_types: workspace_id + key
attribute_definitions: entity_type_id + key
relationship_types: workspace_id + key
form_definitions: workspace_id + key + version_number
phases: workspace_id + key
workspace membership: workspace_id + user_id
```

---

# 23. JSONB Configuration Conventions

JSONB configuration objects SHALL:

- use snake_case keys,
- use explicit versionable structures,
- avoid embedding secrets,
- avoid embedding unbounded binary data.
- preserve Persian Unicode in user-facing labels and option text.

Example:

```json
{
  "options": [
    {"value": "LOW", "label": "کم"},
    {"value": "MEDIUM", "label": "متوسط"},
    {"value": "HIGH", "label": "زیاد"}
  ]
}
```

---

# 24. Entity Attribute Storage Decision

For MVP, the preferred canonical model is:

```text
entity_objects.attributes JSONB
```

Reasons:

- simpler dynamic schema,
- easier import,
- lower join count,
- flexible form persistence,
- strong PostgreSQL JSONB indexing support.

However:

- `attribute_definitions` remains authoritative metadata,
- backend validation SHALL enforce allowed keys/types,
- frontend SHALL never treat raw JSONB as schema.

If later reporting requires heavy per-attribute indexing, the architecture team MAY adopt normalized values through an ADR.

---

# 25. Data Validation Responsibilities

Database SHALL enforce:

- primary keys,
- foreign keys,
- uniqueness,
- basic enum/check constraints,
- non-null platform invariants.

Backend service layer SHALL enforce:

- metadata-driven validation,
- hierarchy cycle rules,
- relationship type constraints,
- form validation,
- lock rules,
- workspace authorization,
- import merge logic.

---

# 26. Locking and Phase Protection

The database stores lock state in `phases.is_locked`.

Backend SHALL determine whether a target entity/document/form instance belongs to a locked phase before mutation.

For high-assurance deployments, database-level policies or triggers MAY supplement service checks, but service-layer enforcement is mandatory.

---

# 27. Transaction Boundaries

The following operations MUST be transactional:

- entity creation plus attributes,
- hierarchy reparenting,
- relationship creation with validation,
- form submission,
- phase lock/unlock,
- document version metadata commit,
- import final commit,
- role/permission mutation.

---

# 28. Import Transaction Strategy

Dry-run operations MUST NOT mutate production entity data.

Commit behavior:

1. acquire/validate import job state,
2. verify conflict resolutions,
3. start transaction,
4. create/update entities,
5. write audit records,
6. update import summary,
7. commit,
8. mark job completed.

Failure before commit SHALL roll back the transaction.

---

# 29. Migration Order

Initial migrations SHOULD follow:

```text
001 extensions
002 users
003 roles_permissions
004 workspaces
005 workspace_memberships
006 entity_types
007 attribute_definitions
008 entity_objects
009 relationships
010 forms
011 documents
012 imports
013 phases
014 comments
015 dashboards
016 audit
017 background_jobs
018 seed_permissions
019 seed_roles
```

Migration IDs MAY differ, but dependency order SHALL remain valid.

---

# 30. Seed Data

System seed data MAY include:

Roles:

```text
SYSTEM_ADMIN
PROJECT_MANAGER
ANALYST
VIEWER
```

Permissions:

```text
WORKSPACE_CREATE
WORKSPACE_MANAGE
ENTITY_CREATE
ENTITY_READ
ENTITY_UPDATE
ENTITY_ARCHIVE
METADATA_MANAGE
FORM_DESIGN
FORM_SUBMIT
DOCUMENT_UPLOAD
DOCUMENT_READ
IMPORT_EXECUTE
PHASE_LOCK
PHASE_UNLOCK
DASHBOARD_READ
DASHBOARD_MANAGE
AUDIT_READ
```

Seed operations SHALL be idempotent.

---

# 31. Database User Separation

Production SHOULD use separate roles such as:

```text
platform_app
platform_migration
platform_readonly
```

`platform_app` SHALL not have schema-altering privileges.

Only `platform_migration` SHOULD execute Alembic DDL migrations.

---

# 32. Backup Requirements

PostgreSQL production backup SHALL support:

- scheduled full backups,
- WAL/PITR where required,
- documented restore procedure.

A backup is not considered valid until restore has been tested.

---

# 33. Performance Baseline

Database implementation SHOULD support:

- 10,000+ entities per workspace,
- 100,000+ attribute values/configured properties,
- thousands of documents,
- relationship-heavy models.

Critical queries SHALL be EXPLAIN-tested before production hardening.

---

# 34. Prohibited Database Anti-Patterns

The following are prohibited:

```text
business_processes table
applications table
servers table
stakeholders table
```

when those concepts are administrator-defined.

Also prohibited:

- direct production schema edits,
- storing passwords in plaintext,
- storing large document binaries in PostgreSQL without ADR,
- unbounded JSONB without validation,
- duplicate sources of truth for dynamic attributes,
- recursive hierarchy assembly via N+1 queries,
- deleting audit logs through application APIs,
- public object-storage credentials in database records.

---

# 35. Acceptance Criteria

Database implementation is complete when:

- [ ] all P0 tables exist through Alembic migrations,
- [ ] all PK/FK constraints are present,
- [ ] workspace-scoped indexes exist,
- [ ] hierarchy traversal uses recursive SQL,
- [ ] cycle prevention is implemented,
- [ ] entity type creation requires no migration,
- [ ] generic entity data is stored without domain tables,
- [ ] form versions are immutable after publication,
- [ ] document versions are append-only,
- [ ] imports have dry-run and conflict persistence,
- [ ] audit logs are append-only,
- [ ] transaction boundaries are tested,
- [ ] migration-from-empty succeeds,
- [ ] downgrade strategy is documented,
- [ ] seed data is idempotent.

---

# 36. Requirement Traceability

Key mappings:

```text
META-FR-*  → entity_types, attribute_definitions
ENT-FR-*   → entity_objects
HIER-FR-*  → entity_objects.parent_id + recursive CTEs
REL-FR-*   → relationship_types, entity_relationships
FORM-FR-*  → form_definitions, form_fields, form_instances
DOC-FR-*   → documents, document_versions
IMP-FR-*   → import_profiles, import_mappings, import_jobs, import_conflicts
PHASE-FR-* → phases, phase_deliverables
REV-FR-*   → review_comments
GOV-FR-*   → workflow definitions/versions/instances/transition events, deliverables/submissions
WORK-FR-*  → generic work items/dependencies/risks/issues
COM-FR-*   → typed threads/messages/announcements/notifications
ACC-FR-*   → acceptance packages/decisions/conditions/evidence
CONF-FR-*  → versioned configuration packages/change history
RPT-FR-*   → dashboards
AUD-FR-*   → audit_logs
```

---

# 37. Related Specifications

```text
00_PROJECT_CONTEXT.md
01_ARCHITECTURE_RULES.md
02_SYSTEM_REQUIREMENTS.md
04_API_SPECIFICATION.md
05_BACKEND_SPECIFICATION.md
06_FRONTEND_SPECIFICATION.md
08_TASK_BACKLOG.md
09_TEST_SPECIFICATION.md
10_DEPLOYMENT_GUIDE.md
11_SECURITY_SPECIFICATION.md
12_CURRENT_STATUS.md
13_IMPLEMENTATION_ROADMAP.md
14_PROJECT_USAGE_SCENARIOS.md
```
