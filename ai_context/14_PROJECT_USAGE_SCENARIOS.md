# Project Usage Scenario Baseline

**Status:** Normative Product Input
**Date accepted:** 2026-08-25
**Source:** User-provided `PROJECT_USAGE_SCENARIOS.md`
**Scope:** 343 actor scenarios and their cross-role authority boundaries

The complete accepted scenario text is preserved in
`15_DETAILED_USAGE_SCENARIOS.md`; this file defines its normative interpretation and
traceability into the architecture package.

---

# 1. Purpose

This document incorporates the approved usage-scenario catalog into the repository
specification set. It is a traceability and interpretation boundary: detailed
requirements live in `02_SYSTEM_REQUIREMENTS.md`, implementation work lives in
`08_TASK_BACKLOG.md`, and authority architecture is accepted by `ADR-0006`.

The source scenarios express user intent and outcomes. They do not prescribe screen
layouts, database tables, API payloads, or implementation instructions.

---

# 2. Actor Inventory

| Actor | Scenario range | Count | Authority boundary |
|---|---:|---:|---|
| Administrator | ADM-01..ADM-32 | 32 | Configures system and project capabilities |
| Project Manager | PM-01..PM-40 | 40 | Governs project execution and recommendations |
| Project Officer | PO-01..PO-52 | 52 | Monitors, follows up, checks completeness, reports |
| Technical Reviewer | TR-01..TR-30 | 30 | Assesses technical quality and may sign off |
| Contractor Project Leader | CPL-01..CPL-66 | 66 | Controls contractor execution and formal submission |
| Contractor Team Member | CTM-01..CTM-70 | 70 | Produces and revises assigned work |
| Employer Representative | ER-01..ER-53 | 53 | Provides oversight and contractual acceptance |

The baseline roles are seedable profiles. They do not prevent administrators from
defining additional project roles or narrower permission combinations.

---

# 3. Non-Negotiable Authority Principles

- Administrator configuration defines what a project can do; project actors operate
  only within that published configuration.
- Project Officers may monitor, record internal observations, flag, remind, and
  report, but do not inherit Project Manager decisions.
- Technical assessment, recommendation, conditional technical recommendation, and
  sign-off remain separate from contractual acceptance.
- Contractor internal review and readiness remain separate from formal contractor
  submission.
- Contractor Team Members normally prepare and return work for internal review;
  formal external submission requires separately granted authority.
- Employer Representatives have high acceptance and oversight authority but no
  implied day-to-day contractor-management authority.
- Every role is restricted by active workspace membership, object scope, assignment,
  lifecycle state, and explicit backend permission.

---

# 4. Capability Traceability

| Scenario capability | Representative scenarios | Requirements/backlog area |
|---|---|---|
| Project/configuration lifecycle | ADM-01..ADM-31, PM-01 | `CONF-FR-*`, CONFIG tasks |
| Archive/closure | ADM-32, PM-40, ER-27..ER-35 | `GOV-FR-*`, `ACC-FR-*` |
| Metadata, forms, taxonomies, relationships | ADM-02..ADM-07, CTM-28..CTM-34 | META, FORM, REL |
| Repository, templates, immutable versions | ADM-08..ADM-11, CTM-09..CTM-27 | DOC, TEMPLATE tasks |
| Controlled imports | ADM-12..ADM-15, CPL-38..CPL-40, CTM-35..CTM-38 | IMP |
| Membership and scoped authority | ADM-20..ADM-23, PM-02..PM-04, CPL-04..CPL-07 | AUTH, WS, GOV |
| Phases, milestones, activities, dependencies | ADM-26, PM-05..PM-14, CPL-08..CPL-15 | PHASE, WORK |
| Deliverables and formal submissions | PM-15..PM-21, CPL-16..CPL-33 | DEL, SUB |
| Comments, revisions, technical review | PM-18..PM-24, TR-03..TR-20, CTM-39..CTM-50 | REV, GOV |
| Monitoring, completeness, timelines | PO-01..PO-52, PM-27..PM-39 | MON, RPT |
| Contextual communication and notifications | PM-25..PM-26 and corresponding role scenarios | COM, NOTIF |
| Risks, issues, escalation, extensions | PM-32..PM-35, CPL-43..CPL-50, ER-36..ER-38 | RISK, GOV |
| Phase/final acceptance and conditions | ER-18..ER-35, ER-50..ER-53 | ACC |
| Role-specific dashboards and reports | PM-30..PM-37, TR-30, CPL-57..CPL-60, ER-39..ER-45 | RPT |

---

# 5. Canonical Governance Flow

```text
Contractor Team Member prepares / uploads / revises
    -> Contractor Project Leader performs internal QA
    -> Contractor Project Leader formally submits
    -> Project Officer monitors and checks completeness
    -> Project Manager reviews and recommends
    -> Technical Reviewer assesses where configured
    -> Project Manager recommends acceptance
    -> Employer Representative decides phase acceptance
    -> all required phases and conditions close
    -> Employer Representative decides final acceptance
```

Projects may configure optional stages, multiple reviewers, conditions, and
transition rules, but may not reinterpret one authority lane as another.

---

# 6. Product Boundary

The approved scenarios add lightweight project execution, delivery governance,
monitoring, and acceptance to product scope. They do not authorize a general-purpose
ERP or unrestricted collaboration suite. Budgeting, payroll, timesheets, billing,
CRM, resource optimization, and arbitrary chat remain out of scope unless separately
approved. Contextual project threads, announcements, reminders, dates, dependencies,
and workload projections are in scope because they support governed delivery.

---

# 7. Implementation Interpretation

- Scenario names are not table, service, route, or page names.
- Repeated behaviors across roles SHALL share generic engines and UI components.
- Persona dashboards are permission-aware projections over canonical records.
- Workflow states and transitions SHALL be metadata, except stable engine-level
  record states required for integrity and idempotency.
- Reports use safe server-defined or metadata-validated query definitions; browser
  supplied SQL is prohibited.
- All formal submissions, recommendations, sign-offs, acceptance decisions,
  conditions, reopenings, assignment changes, and deadline changes are auditable.

---

# 8. Delivery Priority

The first scenario-aligned demo should prove one end-to-end governed deliverable:

```text
contractor contributor draft
-> contractor leader internal review and formal submission
-> project-manager / technical review
-> revision and resubmission
-> employer phase acceptance
```

Dashboards, notifications, repository context, comments, and audit history should
support that vertical slice before broad report catalogs or advanced configuration
builders are expanded.
