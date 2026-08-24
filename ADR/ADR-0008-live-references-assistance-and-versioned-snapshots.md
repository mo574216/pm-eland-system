# ADR-0008: Live References, Assistance, and Versioned Snapshots

**Status:** Accepted
**Date:** 2026-08-25

## Context

Project information is reused across forms, deliverables, imports, and reports. A
service change must be observable throughout current project work, while submitted,
approved, and accepted evidence must not be silently rewritten. Users also need
suggestions when completing forms manually or through import, automatic project and
service context above a form, and configurable report templates that can require
project, employer, contractor, and other details.

Copying values into every form causes drift. Treating every value as live destroys
historical evidence. Hard-coded suggestions and report layouts violate the
metadata-driven architecture.

## Decision

Canonical entities and typed relationships remain the live source of truth for
current project information. Configured consumers SHALL explicitly choose one of
these binding semantics:

- **LIVE_REFERENCE** — resolve the current authorized canonical value;
- **READ_ONLY_INHERITED** — display a live referenced value as non-editable context;
- **EDITABLE_SUGGESTION** — initialize or suggest a value that the user may change;
- **COPY_ON_CREATE** — deliberately copy a value once and then treat it independently;
- **SNAPSHOT_ON_SUBMIT** — capture the resolved value and source/version when a form,
  submission, decision, or generated report becomes formal evidence.

The default for reusable project/service/organization information is a live
reference, not an untracked copy. Formal historical artifacts use immutable,
version-addressed snapshots. Current views may show that a historical snapshot is
older than its canonical source, but SHALL not mutate the snapshot.

Material canonical changes SHALL be observable through a generic dependency/impact
projection based on relationships, bindings, assignments, and governed artifacts.
Authorized users may see affected current forms, deliverables, reports, and project
areas. Configured changes may create notifications or a `REVIEW_REQUIRED` marker;
propagation SHALL not blindly rewrite user-entered or historical values.

Forms opened from project context SHALL render a server-authorized context header
above the form. It may include project, phase, selected service/entity, employer,
contractor, responsible parties, dates, and state according to configuration. Users
SHALL not re-enter or select context already established by the route/work item.

A generic assistance engine SHALL provide candidates consistently for manual entry
and import review. Candidate sources include configured defaults, project/parent/
related entities, taxonomies, previously accepted values, deterministic rules,
duplicate/matching analysis, and optional AI providers. Every suggestion records
value, reason, source/provenance, confidence where meaningful, and status. Suggestions
never overwrite data automatically and require explicit accept/edit/reject except for
configured read-only live bindings.

Reports SHALL be generated from versioned metadata-defined templates using safe,
allowlisted data bindings and reusable sections/widgets. Templates may require
project, employer, contractor, reporting-period, progress, deliverable, risk/issue,
review, acceptance, narrative, branding, header/footer, and signature information.
They SHALL support preview and publish; generated formal reports retain template
version, data-as-of time, source references/versions, and output artifact.

Employer, contractor, reviewer, and other organizations SHALL be reusable generic
party records linked to projects and memberships. They SHALL not be repeated as
uncontrolled text in every form or report.

## Alternatives Considered

- Copy all inherited values: rejected because changes become inconsistent.
- Resolve all historical artifacts live: rejected because evidence changes after
  submission or acceptance.
- Automatically apply every suggestion: rejected because it creates silent mutation
  and weak provenance.
- Hard-code process/service suggestions or report layouts: rejected because forms,
  information types, and reports are configurable.
- Permit template SQL or executable scripts: rejected for security and portability.

## Consequences

- Binding mode and provenance become explicit contracts across forms, imports, and
  reports.
- Entity/service changes require impact queries and notification integration, not
  cascading data copies.
- Form render contracts include contextual display data and suggestion policies.
- Report templates and generated reports require versioned persistence.
- Organization/party records become a prerequisite for useful membership, context,
  deliverable, and report UX.

## Migration Impact

No immediate database migration. PARTY, context binding, suggestion/provenance,
impact projection, and report-template tasks require Alembic migrations. Existing
inheritance rules require a compatibility mapping to the explicit binding modes.

## Security Impact

Reference resolution, impact lists, suggestion sources, and report bindings SHALL be
workspace/object authorized and field-level redacted where required. AI suggestions
must use the future approved AI architecture and may not send unauthorized project
data. Report templates cannot execute arbitrary SQL/code. Snapshots and provenance
are immutable and audited when used as formal evidence.

## Related Requirements

- `CTX-FR-001` through `CTX-FR-006`
- `ASSIST-FR-001` through `ASSIST-FR-008`
- `REF-FR-001` through `REF-FR-006`
- `RPT-FR-007` through `RPT-FR-012`
- `ADR-0001` and `ADR-0006`

## Supersedes / Superseded By

Supersedes ambiguous use of “prefill” where live-reference, editable suggestion,
copy, and formal snapshot behavior were not distinguished. Superseded by: none.
