# Implementation Roadmap

**Status:** Informational / Execution Guide
**Derived from:** `00_PROJECT_CONTEXT.md` through `15_DETAILED_USAGE_SCENARIOS.md`, `08_TASK_BACKLOG.md`, shared contracts, and accepted ADRs
**Baseline date:** 2026-08-22

## 1. Outcome

Deliver the MVP as a Persian-first, RTL, metadata-driven enterprise architecture and project knowledge platform, then deliver the approved governed-project scenarios through reusable workflow engines. The first technical MVP remains proven by authentication, workspace isolation, configurable metadata, generic hierarchy, dynamic forms, immutable document versions, safe XLSX/CSV import, phase locking, dashboards, and immutable audit history. The governed-delivery release additionally requires the authority-separated submission, review, revision, acceptance, communication, monitoring, and configuration-lifecycle scenarios in `14_PROJECT_USAGE_SCENARIOS.md`.

The architectural invariant for every milestone is:

> Domain concepts are configuration data, not application code.

## 2. Current Baseline

Architecture and specifications are complete. Runtime foundation implementation is in progress.

Repository foundation task FND-001 is complete:

- Present: `backend/`, `frontend/`, `infrastructure/`, `README.md`, `.env.example`, `contracts/`, `ADR/`, and `ai_context/`.
- FND-002 and FND-003 are complete: the backend and frontend foundations build and their automated checks pass.
- FND-004 is complete: PostgreSQL connectivity, the async SQLAlchemy session model, Alembic, required extensions, and automated disposable test-database provisioning are implemented and verified against PostgreSQL 16.
- FND-005 is complete: one health-gated Docker Compose command starts the frontend, backend, PostgreSQL, MinIO, and Redis; migrations and cross-service connectivity are verified.
- FND-006 is complete: its Linux portability fix is merged, hosted CI is green, and the active `main` branch ruleset requires `Required CI Gate`.
- FND-007 is complete: the current shell is Persian/RTL, platform copy uses i18n resources, MUI and Emotion are RTL-configured, Vazirmatn is bundled, public API errors are localized centrally, and Persian search normalization is tested.
- UX-FE-001 is complete: the approved ADR-0005 portal composition provides a responsive right-side navigation shell, contextual workspace header, honest capability dashboard, and browser-tested Persian RTL flow.
- Local-only state: `.vscode/` is untracked and is outside this roadmap unless explicitly added.

The repository uses `ai_context/`. Canonical repository guidance now references that path; do not duplicate the specification set.

## 3. Delivery Principles

- Execute tasks in dependency order from `08_TASK_BACKLOG.md`.
- Treat `contracts/openapi.yaml`, `contracts/error-codes.yaml`, and `contracts/permissions.yaml` as integration boundaries.
- Use PostgreSQL and Alembic for all relational schema work; SQLite is not sufficient for integration verification.
- Keep backend authorization authoritative and test every workspace-scoped resource for cross-workspace denial.
- Store MVP dynamic entity attributes in `entity_objects.attributes JSONB`; do not create a parallel normalized source of truth.
- Use generic backend services and frontend renderers. Never add domain-specific models, tables, services, or pages.
- Add tests with each task. A feature is not complete without negative authorization, validation, isolation, audit, and lock tests where relevant.
- Keep developer-facing contracts in English and all end-user platform UI in Persian (`fa-IR`) and RTL.
- Require an ADR for architecture changes and resolve security-sensitive open decisions before dependent implementation begins.

## 4. Decision Gates

| Gate | Required before | Decision | Expected artifact |
|---|---|---|---|
| DG-01 | AUTH-BE-001 | Resolved by ADR-0004: short-lived bearer access tokens with rotating opaque refresh sessions | `ADR/ADR-0004-bearer-access-tokens-and-rotating-refresh-sessions.md` and aligned contracts |
| DG-02 | FND-004 | Resolved by ADR-0002: async SQLAlchemy with psycopg 3, scoped sessions, and service-owned transactions | `ADR/ADR-0002-async-sqlalchemy-session-model.md` |
| DG-03 | FORM-BE-003 | Define deterministic JSON schema for visibility, required-if, inheritance, and read-only rules (OD-005) | Contract/spec update; no `eval` or arbitrary code |
| DG-04 | FORM-DB-001 | Confirm nested JSON storage for repeating rows (OD-006 recommendation) | ADR only if deviating from `form_instances.values_json` |
| DG-05 | DOC-BE-005 P1 | Select Office preview conversion stack (OD-008) | Document/deployment decision |
| DG-06 | DOC-BE-006 | Select malware scanner integration (OD-009) | Security/deployment decision |
| DG-07 | DR-001 | Approve production RPO/RTO (OD-013) | Operations decision and recovery plan |
| DG-08 | Date/number-intensive frontend work | Choose Jalali/Gregorian calendar and Persian/Latin display digits (OD-015) | Localization policy update and centralized formatter tests |
| DG-09 | GOV-DB-001 / AUTH-DB-002 | Resolved by ADR-0006 and AUTH-DB-002: distinct contribution, internal-review, submission, monitoring, project-review/recommendation, technical-review/sign-off, acceptance, condition-verification, communication, and workflow-configuration permissions | `contracts/permissions.yaml`, migration 0014, and authority-matrix tests |
| DG-10 | UX-BE-001 | Define server-generated stable-key format, collision policy, explicit-key lifecycle, and compatibility for existing API clients | API/spec update and key-generation tests |
| DG-11 | CTX-BE-001 | Finalize explicit live/reference/suggestion/copy/snapshot binding schema and compatibility mapping from current inheritance rules | Contract/spec update; ADR-0008 is authoritative |
| DG-12 | RPT-BE-004 | Select restricted report renderer/output formats and resource limits; prohibit template SQL/code | Deployment/security decision and renderer contract |

OD-002 is resolved for the MVP by the accepted architecture direction: JSONB is canonical. OD-003, OD-004, OD-007, OD-010, OD-011, OD-012, and OD-014 do not block foundation work and must not expand MVP scope.

## 5. Milestone Roadmap

### M0 - Repository and Engineering Foundation

**Goal:** A clean clone starts, builds, migrates, and runs automated checks.

Execution order:

1. Complete FND-001: establish `backend/`, `frontend/`, and `infrastructure/`; add `.env.example`; reconcile documentation paths; preserve existing contracts and ADRs.
2. Run FND-002 and FND-003 in parallel: FastAPI foundation and React/Vite application shell.
3. Complete DG-02 and FND-004: PostgreSQL connection, SQLAlchemy session model, Alembic, disposable test database.
4. Complete FND-005: Docker Compose for frontend, backend, PostgreSQL, MinIO, and Redis.
5. Complete FND-006: CI for lint, formatting, type checks, tests, migration-from-empty, secret scanning, and builds.
6. Complete FND-007: Persian i18n resources, global RTL, localized MUI/font, safe API messages, search normalization, and RTL tests.

Exit gate:

- Clean-clone build succeeds.
- `/health/live` and `/health/ready` behave as specified.
- Frontend shell builds under strict TypeScript.
- Alembic upgrades an empty PostgreSQL database.
- Docker Compose validates service connectivity.
- CI blocks failures and contains no committed secrets.
- Core routes render Persian copy and pass automated RTL browser checks.

### M1 - Identity, Workspace, and Security Foundation

**Goal:** Authenticated users operate only within authorized workspaces.

Execution order:

1. AUTH-DB-001 and WS-DB-001 database foundations.
2. Complete AUTH-BE-001 and AUTH-BE-002 using the authentication model accepted in ADR-0004.
3. Implement WS-BE-001 with centralized authorization and audited membership changes.
4. Implement AUTH-FE-001 and WS-FE-001 against stable API contracts.
5. Complete TEST-AUTH-001 and TEST-WS-001 continuously, not at milestone end.

Exit gate:

- Login, logout, expiry, inactive-user, and failure behavior pass.
- Permission resolution is centralized server-side.
- Cross-workspace list, read, and mutation attempts are denied without information leakage.
- Initial role/permission seeding is idempotent and matches `contracts/permissions.yaml`.
- Authentication and membership mutations are audited.

### M2 - Metadata and Generic Entity Platform

**Goal:** Administrators configure arbitrary concepts; users manage generic entities, hierarchy, and relationships.

Execution order:

1. META-DB-001, META-BE-001, META-BE-002, and META-BE-003.
2. ENT-DB-001, then ENT-BE-001 through ENT-BE-003.
3. HIER-BE-001 and HIER-BE-002 using recursive PostgreSQL CTEs and cycle prevention.
4. REL-DB-001 and REL-BE-001.
5. META-FE-001, ENT-FE-001, ENT-FE-002, and REL-FE-001 once payload contracts stabilize.
6. Resolve DG-10 and complete UX-BE-001, UX-FE-002, and REL-FE-002 before the next
   stakeholder demo so technical keys/IDs and relationship mechanics no longer leak.
7. Complete TEST-HIER-001 and applicable workspace/security/UX tests.

Exit gate:

- `Network Security Zone` can be configured without code or migration changes.
- Dynamic values are validated from metadata and stored canonically in JSONB.
- Entity updates use optimistic concurrency and return `STALE_VERSION` conflicts.
- Hierarchy traversal has no N+1 behavior; cycles and cross-workspace parenting are rejected.
- Relationship operations are generic and workspace-scoped.
- Material changes generate immutable audit records.

### M3 - Dynamic Forms and Structured Data

**Goal:** Generic forms render and persist metadata-defined structured data.

Execution order:

1. Resolve DG-03 and DG-04.
2. Implement FORM-DB-001 and FORM-BE-001.
3. Implement FORM-BE-003 rule evaluation and FORM-BE-004 render contract.
4. Implement DATA-BE-001 and DATA-BE-002 with authoritative backend validation and lock checks.
5. Implement FORM-FE-001 through FORM-FE-004.
6. Complete P1 versioning work FORM-BE-002 and FORM-FE-005 before production release.
7. Resolve DG-11; implement PARTY and CTX services so governed forms carry project,
   phase, service/entity, and organization context with explicit snapshot semantics.
8. Implement deterministic ASSIST-BE/FE-001 for explainable manual/import suggestions;
   AI remains deferred behind AI-001.
9. Complete TEST-FORM-001 across every supported field type, binding mode,
   inheritance/context mode, conditional rule, and repeating table.

Exit gate:

- A configured form renders without domain-specific frontend branches.
- Parent/current/reference/static/user-context prefill follows metadata.
- Read-only inherited values cannot be changed through direct API calls.
- Repeating rows persist and reload correctly.
- Published forms are immutable; historical instances retain their definition version.
- Backend validation errors map to exact fields/rows.

### M4 - Documents and Import

**Goal:** Preserve immutable files and safely migrate offline structured data.

Documents stream:

1. DOC-DB-001 and DOC-BE-001.
2. DOC-BE-002 through DOC-BE-005 for upload, immutable versions, authorized download, and PDF/image preview.
3. DOC-FE-001 and DOC-FE-002.
4. Resolve DG-05 and DG-06 for production P1 Office preview and malware scanning.
5. Complete TEST-DOC-001.

Import stream, started after metadata/entity validation is stable:

1. IMP-DB-001 and IMP-BE-001.
2. IMP-BE-002 and IMP-BE-003 for profiles, mapping, and matching.
3. IMP-BE-004 dry run and IMP-BE-005 explicit conflict resolution.
4. IMP-BE-006 transactional, idempotent commit with audit summary.
5. IMP-FE-001 through IMP-FE-005 as each backend contract stabilizes.
6. After phase/deliverable foundations, implement IMP-BE-007/IMP-FE-006 so the wizard
   is embedded in governed context and removed from normal top-level navigation.
7. Complete TEST-IMP-001, including rollback, duplicate commit, contextual lock,
   association, and relationship-preservation cases.

Exit gate:

- Document replacement always creates a new immutable version.
- Object storage is private; download/preview authorization is backend-controlled and time-limited where presigned URLs are used.
- Upload validation covers size, extension, MIME, filename, and path safety.
- Dry run never mutates canonical data.
- Creates, updates, unchanged rows, validation errors, and conflicts are distinguishable.
- MERGE, REPLACE, and SKIP are explicit; unresolved conflicts block commit.
- Import commit is transactional, idempotent, workspace-scoped, and audited.

### M5 - Phase Control, Governed Delivery, Review, Acceptance, and Reporting

**Goal:** Each actor can perform its governed project role without crossing authority
lanes, and managers can observe trusted system state.

Execution order:

1. Implement AUD-DB-001 and AUD-BE-001 early enough that all prior material mutations use the shared audit service; do not defer audit wiring to the end.
2. PHASE-DB-001, PHASE-BE-001, PHASE-BE-002, and PHASE-FE-001.
3. RPT-DB-001, RPT-BE-001, and RPT-FE-001 for server-defined MVP KPIs.
4. Complete P1 audit query/viewer work: AUD-BE-002 and AUD-FE-001.
5. Resolve DG-09 and implement AUTH-DB-002 before exposing governed transitions.
6. Implement GOV-DB-001/GOV-BE-001, then the DEL/SUB deliverable vertical slice.
7. Extend review with version-bound outcomes; implement ACC phase/final acceptance
   and conditions without conflating technical recommendation with acceptance.
8. Add generic WORK, COM, and notification engines, then role-appropriate projections.
9. Implement REF-BE-001 for current change-impact visibility and immutable snapshot
   comparison without cascading data copies.
10. Complete P1 configurable dashboard work only through a safe metadata-driven query model; arbitrary SQL is prohibited.
11. Resolve DG-12 and implement versioned report templates/generation with required
   project and contractor details and immutable provenance.
12. Complete TEST-LOCK-001, QA-002, and audit/dashboard/isolation tests.

Exit gate:

- Phase lock is enforced by a shared backend policy across entity update, form save, hierarchy move, and applicable document mutations.
- Only explicit permission permits unlock; lock/unlock is audited.
- Audit records are append-only and redact secrets/sensitive values.
- Dashboard KPIs are correct and cannot aggregate across workspaces.
- P1 review history preserves author, timestamp, target, status, and revisions.
- A contractor contributor cannot formally submit unless separately authorized.
- Contractor readiness, formal submission, project review, technical recommendation,
  and employer acceptance are distinct, version-bound, audited transitions.
- Conditional phase acceptance creates verifiable obligations and cannot become full
  acceptance while mandatory conditions remain open.
- Project Officers can monitor and flag without acquiring Project Manager decisions.
- Current service/entity changes are observable through authorized relationships and
  impact projections while formal historical artifacts remain stable.
- Governed forms automatically display project/phase/service/party context and use
  explicit live/suggestion/copy/snapshot semantics.
- Report templates can require project and contractor information and produce
  immutable, versioned, provenance-bearing outputs without SQL/code execution.

### M6 - Production Hardening and Release

**Goal:** Demonstrate that the MVP is secure, recoverable, observable, and deployable.

Execution order:

1. Run QA-001 and QA-002 canonical and negative Playwright scenarios.
2. Run SEC-001 across authentication, BOLA/IDOR, workspace isolation, uploads, imports, XSS, CORS, secrets, object storage, and audit tampering.
3. Complete PERF-001 with representative entity, hierarchy, form, relationship, audit, import, and dashboard data.
4. Complete OBS-001 for structured logs, correlation IDs, metrics, health/readiness, and error monitoring.
5. Resolve DG-07 and complete DR-001; test PostgreSQL restore and object-reference consistency.
6. Complete DEP-001 only after QA-001 and SEC-001 pass.

Release gate:

- Every P0 task is complete and traceable to requirements/tests.
- Lint, formatting, backend/frontend type checks, unit, integration, frontend, E2E, build, migration, and security checks pass.
- Workspace isolation, phase locking, import rollback/idempotency, document versioning, and audit immutability are verified.
- No unresolved critical or high authentication, authorization, cross-workspace, or data-integrity finding remains.
- Deployment pipeline works; backups are configured and restore is tested.

### M7 - Deferred AI Enhancements

Do not start runtime AI work as part of MVP. AI-001 must first define provider/privacy, workspace-aware retrieval, prompt/version audit, injection defenses, cost controls, and mandatory user approval for write actions. AI-002 through AI-004 remain P2 and may not bypass platform APIs or authorization.

## 6. Recommended Delivery Slices

Use thin, demonstrable slices within each milestone:

1. **Foundation slice:** clean clone to running empty shell.
2. **Secure workspace slice:** login to isolated workspace list.
3. **Generic entity slice:** configure type, create entity, display hierarchy.
4. **Structured data slice:** configure form, inherit parent values, save and reload.
5. **Document slice:** upload, version, preview, and authorize download.
6. **Import slice:** inspect, map, dry-run, resolve, commit, and audit.
7. **Control slice:** dashboard, phase lock, rejected analyst edit.
8. **Governed deliverable slice:** contributor draft, internal review, leader
   submission, external review, revision, recommendation, and phase acceptance.
9. **Context and assistance slice:** project/phase/service header, live bindings,
   explainable manual/import suggestions, and historical snapshot proof.
10. **Connected-report slice:** service change impact, required party/project report
   template, preview, generation, and immutable provenance.
11. **Operations slice:** personal/monitoring queues, contextual notifications,
   risks/issues, readiness, and acceptance status.
12. **Release slice:** full E2E, security, performance, recovery, and deployment evidence.

Each slice must preserve the API envelope, permission registry, workspace scope, audit expectations, and test traceability.

## 7. Cross-Cutting Verification Matrix

| Concern | Continuous evidence | Final gate |
|---|---|---|
| Architecture | No domain-specific schema/services/pages; contract review | ADR review and generic-type acceptance test |
| Database | Alembic migration and PostgreSQL integration tests | Empty-db upgrade plus representative downgrade/restore |
| API | Contract tests, standard envelopes, documented errors | OpenAPI validation and no undocumented public behavior |
| Authorization | Permission and object-level negative tests | BOLA/IDOR and cross-workspace security review |
| Data integrity | Transactions, optimistic concurrency, immutability tests | Import rollback/idempotency and document history verification |
| Frontend | Strict TS, component/integration tests, Persian copy and RTL checks | Canonical, negative, and localization Playwright scenarios |
| Operations | Container health, logs, secret scanning | Observability, backup/restore, deployment pipeline |

## 8. Immediate Next Actions

1. Resolve DG-10 and complete UX-BE-001/UX-FE-002 plus REL-FE-002 as the
   demo-blocking usability pass (no raw IDs/keys; natural relationship flow).
2. Finish IMP-FE-005 as an embeddable wizard component and preserve focused import
   E2E/TEST-WS-001 coverage; remove top-level navigation when IMP-FE-006 lands.
3. Implement phase/deliverable foundations and contextual IMP-BE/FE-007/006.
4. Resolve DG-09, then begin the generic governed-deliverable slice with
   GOV-DB-001/GOV-BE-001 rather than adding persona-specific pages.
5. Resolve DG-08 before deadline-heavy work-planning and monitoring UI.

The next implementation handoff is the P0 usability remediation beginning with
DG-10/UX-BE-001 and UX-FE-002. IMP-FE-005 follows as an embeddable component. The
first scenario-aligned demo then integrates that component inside the governed
phase/deliverable flow defined in `14_PROJECT_USAGE_SCENARIOS.md` and QA-002.

## 9. Roadmap Maintenance

Update this roadmap and `12_CURRENT_STATUS.md` when a milestone changes, a decision gate is resolved, an ADR is accepted, a blocker appears, or scope is explicitly changed. Task completion records must use the template in `08_TASK_BACKLOG.md` and include requirements, files, migrations, API changes, tests/results, security review, limitations, and follow-up work.
