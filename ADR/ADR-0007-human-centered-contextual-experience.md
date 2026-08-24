# ADR-0007: Human-Centered Contextual Experience

**Status:** Accepted
**Date:** 2026-08-25

## Context

The metadata-driven implementation currently exposes internal concepts such as
stable keys, UUIDs, entity types, source/target direction, relationship cardinality,
and import matching mechanics directly in primary workflows. Workspace membership
asks users for user and role IDs. Import appears as a standalone module even though
project users import specifications while working on a phase deliverable.

This is technically accurate but operationally awkward. The approved product
direction is comparable to the administrative clarity of WordPress: recognizable
sections, list/add/edit flows, sensible defaults, human-readable selectors,
progressive disclosure, preview/publish lifecycles, contextual help, and advanced
technical controls only when needed. This is an interaction reference, not a visual
copy or a requirement to use WordPress technology.

## Decision

The application SHALL separate two coherent experiences:

1. a **Project workspace** for phases, deliverables, project information,
   repository content, forms, reviews, and reports;
2. an **Administration console** for projects, people/organizations, roles/access,
   information structure, forms, workflows, templates, import profiles, dashboards,
   configuration history, and system settings.

Primary workflows SHALL use user intent and business labels. UUIDs, internal foreign
keys, stable technical keys, storage keys, relationship direction/cardinality, and
matching-strategy structures SHALL not be required as raw user input.

- People, roles, organizations, entities, parents, and targets use authorized
  searchable selectors with human-readable identity and disambiguating context.
- Stable technical keys are generated automatically from a safe server-controlled
  strategy. They may be visible in an Advanced section and editable only where the
  lifecycle/integration contract safely permits it.
- Relationship creation is expressed as a natural-language action from the current
  item, with compatible relation and target choices filtered by metadata.
- Common operations follow list -> add -> simple configuration -> preview -> save
  draft/publish where publication applies.
- Advanced settings use progressive disclosure and explain consequences.
- Navigation exposes user goals, not platform-engine terminology.

Import is a reusable contextual capability, not a normal top-level project module.
Operational import SHALL be launched from an eligible phase, deliverable, form, or
output specification and inherit known project, phase, deliverable, target type/form,
and allowed profile. Central import-profile/mapping administration remains available
only in the administration console. The existing wizard becomes an embeddable
component and may have a protected deep link for recovery, audit, or support without
appearing as ordinary standalone navigation.

## Alternatives Considered

- Keep technical administration visible because users are administrators: rejected;
  administrators still need task-oriented, safe workflows.
- Remove all technical details permanently: rejected; advanced diagnostics and
  integrations sometimes require stable identifiers.
- Build a separate custom page for each project concept: rejected because project
  concepts remain metadata and must use reusable components.
- Keep import as a global module: rejected because it forces users to reconstruct
  context the system already knows and weakens phase/deliverable governance.

## Consequences

- Existing metadata, membership, relationship, form-designer, and import interfaces
  require a demo-blocking usability remediation.
- APIs may continue to exchange UUIDs, but list/lookup contracts must provide safe
  display labels and enough context for selectors.
- Route and navigation design must preserve administration/project context.
- Technical keys remain stable integration contracts without becoming routine UX.
- Contextual import requires explicit phase/deliverable binding and lock enforcement.

## Migration Impact

No immediate schema migration. Later PARTY, contextual-import, and technical-key
generation tasks may add schema/defaults and must migrate existing records safely.

## Security Impact

Selectors SHALL return only authorized options and SHALL not become enumeration
endpoints. Generated keys require server-side uniqueness. Hiding an ID or action is
not authorization. Context inheritance and import targets are revalidated by the
backend, and locked phases remain immutable regardless of UI placement.

## Related Requirements

- `UX-FR-001` through `UX-FR-008`
- `IMP-FR-013`
- `PARTY-FR-001` through `PARTY-FR-005`
- `ADR-0003`, `ADR-0005`, and `ADR-0006`

## Supersedes / Superseded By

Supersedes the assumption that internal metadata/API vocabulary is acceptable as
primary user-facing terminology or that import belongs in top-level navigation.
Superseded by: none.
