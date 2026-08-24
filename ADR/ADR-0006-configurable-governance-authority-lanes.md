# ADR-0006: Configurable Governance with Distinct Authority Lanes

**Status:** Accepted
**Date:** 2026-08-25

## Context

The approved project usage scenarios introduce seven baseline personas and a
governed delivery chain. Contractor contributors prepare work, contractor leaders
perform internal quality control and formal submission, project officers monitor,
project managers make operational governance decisions, technical reviewers assess
technical quality, and employer representatives make contractual acceptance
decisions.

Treating every decision as one generic approval would lose authority, provenance,
and contractual meaning. Hard-coding these personas, project structures, or
business deliverable types would conflict with the metadata-driven architecture.

## Decision

The platform SHALL distinguish these authority lanes:

1. contractor preparation and internal review;
2. formal contractor submission;
3. project monitoring and completeness assessment;
4. project-manager review and recommendation;
5. technical review, recommendation, and optional technical sign-off;
6. employer phase or final acceptance, including conditional acceptance.

Each transition SHALL record its actor, authority context, target, immutable target
version where applicable, time, outcome, reason or statement, and resulting state.
Technical recommendation SHALL NOT imply contractual acceptance. Internal
contractor readiness SHALL NOT imply formal submission. Monitoring SHALL NOT grant
project-manager decision authority. Preparation permission SHALL NOT grant formal
submission permission.

The seven personas are seedable baseline role profiles, not hard-coded authorization
branches. Effective authority SHALL be expressed by workspace-scoped permissions,
membership, configurable workflow definitions, target assignments, and transition
policy. Administrators may define additional roles without application-code changes.

Project structures, deliverable categories, forms, statuses, transition graphs,
review sequences, acceptance rules, dashboards, indicators, templates, taxonomies,
and naming rules SHALL remain metadata/configuration. Backend services and frontend
components SHALL operate on generic workflow, work-item, submission, review,
decision, condition, and repository contracts rather than persona-specific pages or
domain-specific tables.

## Alternatives Considered

- One `APPROVE` action for all stages: rejected because it erases authority and
  permits technical or internal decisions to be mistaken for acceptance.
- Hard-coded workflows per persona: rejected because projects require configurable
  sequencing and roles.
- Model every scenario as an independent feature/page: rejected because scenarios
  overlap and must be delivered by reusable platform engines.

## Consequences

- Permission contracts require separate contribution, submission, review,
  recommendation, acceptance, monitoring, and configuration capabilities.
- Workflow history and acceptance records must be durable and version-addressed.
- Dashboards and personal workspaces are projections over authorized generic data,
  not separate sources of truth.
- Contextual messages, comments, reminders, and announcements require visibility
  scopes and linked project targets; the product does not become unrestricted chat.
- The backlog must add generic delivery-governance slices before production release.

## Migration Impact

No immediate database migration is introduced by this ADR. Future workflow,
submission, condition, activity, notification, and reporting tasks must provide
Alembic migrations and preserve workspace isolation.

## Security Impact

Backend transition authorization is authoritative. Every target and participant
must belong to the same workspace, object existence must not leak across workspaces,
formal decisions must be audited, and historical submissions/acceptances must not
be silently altered or deleted.

## Related Requirements

- `GOV-FR-001` through `GOV-FR-008`
- `WORK-FR-001` through `WORK-FR-004`
- `COM-FR-001` through `COM-FR-004`
- `ACC-FR-001` through `ACC-FR-006`
- `ADR-0001`
- `14_PROJECT_USAGE_SCENARIOS.md`

## Supersedes / Superseded By

Supersedes any interpretation that Project Manager and Employer Representative are
one authority or that review approval and contractual acceptance are equivalent.
Superseded by: none.
