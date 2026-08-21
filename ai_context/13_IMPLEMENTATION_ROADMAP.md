# Implementation Roadmap

**Status:** Informational / Execution Guide  
**Derived from:** `00_PROJECT_CONTEXT.md` through `12_CURRENT_STATUS.md`, `08_TASK_BACKLOG.md`, shared contracts, and accepted ADRs  
**Baseline date:** 2026-08-22

## 1. Outcome

Deliver the MVP as a Persian-first, RTL, metadata-driven enterprise architecture and project knowledge platform. The implementation is complete only when the canonical end-to-end scenario passes: authentication, workspace isolation, configurable metadata, generic hierarchy, dynamic forms, immutable document versions, safe XLSX/CSV import, phase locking, dashboards, and immutable audit history.

The architectural invariant for every milestone is:

> Domain concepts are configuration data, not application code.

## 2. Current Baseline

Architecture and specifications are complete. Runtime foundation implementation is in progress.

Repository foundation task FND-001 is complete:

- Present: `backend/`, `frontend/`, `infrastructure/`, `README.md`, `.env.example`, `contracts/`, `ADR/`, and `ai_context/`.
- FND-002 and FND-003 are complete: the backend and frontend foundations build and their automated checks pass.
- FND-004 is complete: PostgreSQL connectivity, the async SQLAlchemy session model, Alembic, required extensions, and automated disposable test-database provisioning are implemented and verified against PostgreSQL 16.
- FND-005 is complete: one health-gated Docker Compose command starts the frontend, backend, PostgreSQL, MinIO, and Redis; migrations and cross-service connectivity are verified.
- FND-006 implementation and local validation are complete. Activation remains pending: commit and push the workflow, confirm its first GitHub-hosted run, and require `Required CI Gate` in the `main` branch ruleset.
- FND-007 is complete: the current shell is Persian/RTL, platform copy uses i18n resources, MUI and Emotion are RTL-configured, Vazirmatn is bundled, public API errors are localized centrally, and Persian search normalization is tested.
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
| DG-01 | AUTH-BE-001 | Choose bearer/refresh-token or secure HTTP-only cookie strategy (OD-001) | Authentication ADR and aligned OpenAPI/security contract |
| DG-02 | FND-004 | Resolved by ADR-0002: async SQLAlchemy with psycopg 3, scoped sessions, and service-owned transactions | `ADR/ADR-0002-async-sqlalchemy-session-model.md` |
| DG-03 | FORM-BE-003 | Define deterministic JSON schema for visibility, required-if, inheritance, and read-only rules (OD-005) | Contract/spec update; no `eval` or arbitrary code |
| DG-04 | FORM-DB-001 | Confirm nested JSON storage for repeating rows (OD-006 recommendation) | ADR only if deviating from `form_instances.values_json` |
| DG-05 | DOC-BE-005 P1 | Select Office preview conversion stack (OD-008) | Document/deployment decision |
| DG-06 | DOC-BE-006 | Select malware scanner integration (OD-009) | Security/deployment decision |
| DG-07 | DR-001 | Approve production RPO/RTO (OD-013) | Operations decision and recovery plan |
| DG-08 | Date/number-intensive frontend work | Choose Jalali/Gregorian calendar and Persian/Latin display digits (OD-015) | Localization policy update and centralized formatter tests |

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
2. Resolve DG-01, then implement AUTH-BE-001 and AUTH-BE-002.
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
6. Complete TEST-HIER-001 and applicable workspace/security tests.

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
7. Complete TEST-FORM-001 across every supported field type, inheritance mode, conditional rule, and repeating table.

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
6. Complete TEST-IMP-001, including rollback and duplicate-commit cases.

Exit gate:

- Document replacement always creates a new immutable version.
- Object storage is private; download/preview authorization is backend-controlled and time-limited where presigned URLs are used.
- Upload validation covers size, extension, MIME, filename, and path safety.
- Dry run never mutates canonical data.
- Creates, updates, unchanged rows, validation errors, and conflicts are distinguishable.
- MERGE, REPLACE, and SKIP are explicit; unresolved conflicts block commit.
- Import commit is transactional, idempotent, workspace-scoped, and audited.

### M5 - Phase Control, Audit, Review, and Reporting

**Goal:** Managers control progression and can observe trusted system state.

Execution order:

1. Implement AUD-DB-001 and AUD-BE-001 early enough that all prior material mutations use the shared audit service; do not defer audit wiring to the end.
2. PHASE-DB-001, PHASE-BE-001, PHASE-BE-002, and PHASE-FE-001.
3. RPT-DB-001, RPT-BE-001, and RPT-FE-001 for server-defined MVP KPIs.
4. Complete P1 audit query/viewer work: AUD-BE-002 and AUD-FE-001.
5. Complete P1 review flow: REV-DB-001, REV-BE-001, and REV-FE-001.
6. Complete P1 configurable dashboard work only through a safe metadata-driven query model; arbitrary SQL is prohibited.
7. Complete TEST-LOCK-001 and audit/dashboard isolation tests.

Exit gate:

- Phase lock is enforced by a shared backend policy across entity update, form save, hierarchy move, and applicable document mutations.
- Only explicit permission permits unlock; lock/unlock is audited.
- Audit records are append-only and redact secrets/sensitive values.
- Dashboard KPIs are correct and cannot aggregate across workspaces.
- P1 review history preserves author, timestamp, target, status, and revisions.

### M6 - Production Hardening and Release

**Goal:** Demonstrate that the MVP is secure, recoverable, observable, and deployable.

Execution order:

1. Run QA-001 canonical and negative Playwright scenarios.
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
8. **Release slice:** full E2E, security, performance, recovery, and deployment evidence.

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

1. Activate FND-006 on GitHub and configure `Required CI Gate` as a required `main` branch status check.
2. Begin AUTH-DB-001 with the generic identity schema defined by the database specification.
3. Resolve DG-01 before implementing authentication token/session behavior.
4. Resolve DG-08 before date- or number-intensive frontend workflows.

The next implementation handoff should finish FND-006 activation before starting `AUTH-DB-001`. Authentication behavior remains blocked on DG-01.

## 9. Roadmap Maintenance

Update this roadmap and `12_CURRENT_STATUS.md` when a milestone changes, a decision gate is resolved, an ADR is accepted, a blocker appears, or scope is explicitly changed. Task completion records must use the template in `08_TASK_BACKLOG.md` and include requirements, files, migrations, API changes, tests/results, security review, limitations, and follow-up work.
