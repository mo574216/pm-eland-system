# ADR-0001 — Metadata-Driven Domain Model

**Status:** ACCEPTED  
**Date:** 2026-08-21  
**Decision Owners:** Project Architecture  
**Related Files:** `01_ARCHITECTURE_RULES.md`, `03_DATABASE_SPECIFICATION.md`

---

# 1. Context

The platform must support different enterprise architecture, process-analysis, transformation, and consulting projects.

Potential user-defined concepts include:

```text
Business Service
Business Process
Application
Data Entity
Technology Component
Server
Stakeholder
Risk
Control
```

The names, attributes, hierarchy, and relationships vary between projects.

A conventional domain-specific relational schema would require source-code changes and database migrations every time a new project introduces a new business concept.

That conflicts with the intended low-code/configurable nature of the platform.

---

# 2. Decision

The platform SHALL use a metadata-driven generic domain model.

User-configurable business concepts SHALL be represented through:

```text
entity_types
attribute_definitions
entity_objects
relationship_types
entity_relationships
```

For MVP, dynamic entity property values are preferably stored in:

```text
entity_objects.attributes JSONB
```

and validated against `attribute_definitions`.

No dedicated table/model/page SHALL be created merely because a customer introduces a concept such as `Business Process`.

---

# 3. Example

Correct:

```text
entity_types:
  key = business_process
  name = Business Process
```

Then:

```text
entity_objects:
  entity_type_id = <business_process UUID>
  name = Permit Approval Process
```

Incorrect:

```sql
CREATE TABLE business_processes (...);
```

Incorrect:

```python
class BusinessProcess(Base):
    ...
```

Incorrect:

```text
BusinessProcessForm.tsx
```

---

# 4. Alternatives Considered

## Alternative A — Dedicated Domain Tables

Advantages:

- straightforward SQL for a fixed domain,
- strong typed schema per concept.

Rejected because:

- inflexible,
- migration-heavy,
- domain-specific,
- incompatible with configurable project structures.

---

## Alternative B — Fully Schemaless Document Database

Advantages:

- flexible schema.

Rejected for MVP because:

- platform still has stable relational concerns,
- PostgreSQL provides relational integrity plus JSONB,
- transactions, hierarchy, RBAC, audit, and reporting benefit from relational storage.

---

## Alternative C — Graph Database as Primary Store

Advantages:

- natural relationship traversal.

Rejected for MVP because:

- adds operational complexity,
- hierarchy/relationship needs are manageable in PostgreSQL,
- reporting and transactional requirements fit PostgreSQL,
- no demonstrated need justifies a second primary persistence model.

---

# 5. Consequences

Positive:

- new entity types require configuration, not migrations,
- same backend/frontend works across industries/projects,
- AI agents have clear anti-hardcoding rule,
- Excel import can target metadata-defined fields,
- form rendering remains generic.

Negative:

- metadata validation becomes critical,
- reporting over arbitrary JSONB requires careful indexing,
- schema mistakes can move from compile-time to runtime configuration,
- generic UI may require more sophisticated metadata contracts.

---

# 6. Implementation Consequences

Backend SHALL provide:

```text
MetadataService
MetadataValidationService
EntityService
generic relationship services
```

Frontend SHALL provide:

```text
EntityTreeViewer
EntityDetailPage
DynamicFormRenderer
DynamicFieldRenderer
```

Database SHALL avoid domain-specific tables.

---

# 7. Migration Impact

Initial implementation shall start directly with the generic model.

If a future requirement demands normalized dynamic values, migration SHALL be performed through a new ADR and Alembic migration.

The system SHALL NOT maintain JSONB and normalized values as independent concurrent sources of truth.

---

# 8. Security Impact

Positive:

- centralized authorization can operate on generic resources.

Risks:

- generic APIs may accidentally expose attributes across workspaces if scoping is weak.

Controls:

- mandatory workspace authorization,
- server-side metadata validation,
- bounded queries,
- audit logging.

---

# 9. Related Requirements

```text
META-FR-001 through META-FR-009
ENT-FR-001 through ENT-FR-007
HIER-FR-001 through HIER-FR-007
REL-FR-001 through REL-FR-005
FORM-FR-001 through FORM-FR-012
```

---

# 10. Supersession

Supersedes:

```text
None
```

Superseded by:

```text
None
```
