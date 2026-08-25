# Frontend Specification

**File:** `06_FRONTEND_SPECIFICATION.md`  
**Status:** Normative  
**System:** Metadata-Driven Enterprise Architecture Management Platform  
**Version:** 1.0  
**Framework:** React 19+  
**Language:** TypeScript 5+  
**Build Tool:** Vite  
**UI Library:** Material UI (MUI)  
**Server State:** TanStack Query  
**Application State:** Redux Toolkit  
**Forms:** React Hook Form  
**Validation:** Zod  
**Testing:** Vitest + React Testing Library + Playwright  
**Audience:** Frontend engineers, AI coding agents, QA engineers, UX reviewers

---

# 1. Purpose

This document defines the frontend architecture and implementation requirements for the platform.

The frontend SHALL remain generic and metadata-driven.

The central UI rule is:

> **The frontend renders domain behavior from metadata; it does not encode domain concepts in components.**

The frontend SHALL support:

- authentication,
- workspace selection,
- generic hierarchy navigation,
- generic entity details,
- metadata administration,
- dynamic forms,
- repeating sections,
- documents,
- import workflows,
- phase status,
- review comments,
- dashboards,
- permission-aware actions.

---

# 2. Normative References

Frontend implementation SHALL conform to:

```text
00_PROJECT_CONTEXT.md
01_ARCHITECTURE_RULES.md
02_SYSTEM_REQUIREMENTS.md
04_API_SPECIFICATION.md
05_BACKEND_SPECIFICATION.md
09_TEST_SPECIFICATION.md
11_SECURITY_SPECIFICATION.md
```

---

# 3. Technology Baseline

Required:

```text
React 19+
TypeScript 5+
Vite
Material UI
TanStack Query
Redux Toolkit
React Hook Form
Zod
Vitest
React Testing Library
Playwright
```

Optional libraries MAY be added only when they provide clear value and do not duplicate existing stack responsibilities.

---

# 4. Frontend Architecture Principles

## FE-RULE-001 — Generic Components Only

Prohibited:

```text
BusinessProcessForm.tsx
ApplicationDetailPage.tsx
ServerEditor.tsx
RiskPage.tsx
```

Required patterns:

```text
EntityDetailPage
DynamicFormRenderer
DynamicFieldRenderer
EntityTreeViewer
RelationshipPanel
DocumentPanel
ImportWizard
```

---

## FE-RULE-002 — Metadata Drives Rendering

UI decisions for configurable domain fields SHALL come from API metadata.

The frontend SHALL NOT infer form structure from hard-coded entity type names.

---

## FE-RULE-003 — Backend Is Authoritative

Frontend SHALL:

- improve UX with validation,
- hide unauthorized controls where known,
- show lock/read-only state,

but SHALL NOT assume these controls provide security.

Backend responses remain authoritative.

---

## FE-RULE-004 — Server State vs UI State

TanStack Query SHALL own remote/server state such as:

- workspaces,
- entities,
- metadata,
- forms,
- documents,
- imports,
- dashboards.

Redux Toolkit SHALL be reserved for cross-cutting client state such as:

- authenticated user context,
- currently selected workspace,
- persistent UI preferences,
- navigation state where justified.

Avoid duplicating server data in Redux.

---

# 5. Recommended Source Structure

```text
frontend/
├── package.json
├── vite.config.ts
├── src/
│   ├── main.tsx
│   ├── app/
│   │   ├── App.tsx
│   │   ├── router.tsx
│   │   ├── providers.tsx
│   │   └── queryClient.ts
│   ├── auth/
│   ├── layouts/
│   ├── modules/
│   │   ├── workspaces/
│   │   ├── metadata/
│   │   ├── entities/
│   │   ├── relationships/
│   │   ├── forms/
│   │   ├── documents/
│   │   ├── imports/
│   │   ├── phases/
│   │   ├── reviews/
│   │   ├── dashboards/
│   │   └── audit/
│   ├── components/
│   │   ├── common/
│   │   ├── feedback/
│   │   ├── forms/
│   │   └── guards/
│   ├── api/
│   │   ├── client.ts
│   │   ├── types.ts
│   │   └── generated/
│   ├── store/
│   ├── hooks/
│   ├── utils/
│   ├── constants/
│   └── test/
└── e2e/
```

---

# 6. Application Routing

Recommended route structure:

```text
/login

/workspaces

/workspaces/:workspaceId
/workspaces/:workspaceId/entities
/workspaces/:workspaceId/entities/:entityId
/workspaces/:workspaceId/metadata
/workspaces/:workspaceId/forms
/workspaces/:workspaceId/imports
/workspaces/:workspaceId/phases
/workspaces/:workspaceId/dashboards
/workspaces/:workspaceId/audit
```

Administration subroutes MAY include:

```text
/workspaces/:workspaceId/metadata/entity-types
/workspaces/:workspaceId/metadata/relationships
/workspaces/:workspaceId/forms/:formId/designer
```

Routes SHALL be protected by authentication and, where applicable, permission-aware route guards.

---

# 7. Application Shell

The main authenticated layout SHOULD include:

```text
┌──────────────────────────────────────────────────────────┐
│ Header / Workspace Context / User Menu                  │
├─────────────────────┬────────────────────────────────────┤
│ Navigation          │ Main Content                       │
│                     │                                    │
│ Workspace Explorer  │ Current Route/Page                 │
│                     │                                    │
└─────────────────────┴────────────────────────────────────┘
```

The shell SHALL support responsive behavior.

## 7.1 Approved RTL Portal Composition

The authenticated workspace experience SHALL follow ADR-0005. At desktop
widths it uses a persistent navigation drawer on the right and a contextual
header above the main content. At smaller widths the drawer becomes temporary
and is opened by an accessible menu control.

The workspace root route is a capability dashboard. It SHALL provide quick
access only to implemented generic platform capabilities. Planned capabilities
MAY be identified as roadmap items, but SHALL NOT appear as working links or
controls. The shell and dashboard MUST NOT contain organization-specific
business concepts, customer branding, fabricated metrics, or fabricated
notifications.

Visual styling SHALL use centralized theme tokens, Persian localized copy,
strong focus indication, deliberate empty/loading/error states, and code-native
decoration that preserves contrast and content legibility.

---

## 7.2 Project Workspace and Administration Console

The UX SHALL follow ADR-0007 and use the straightforward administrative interaction
model exemplified by WordPress without copying its visual design.

Project workspace navigation organizes user work around:

```text
Overview
Phases and milestones
Deliverables
Project structure/information
Repository
Reviews and comments
Reports
```

Administration console navigation organizes configuration around:

```text
Projects
People and organizations
Roles and access
Information types and fields
Forms
Workflows
Templates
Import profiles
Dashboards
Configuration history
System settings
```

Common screens SHOULD use list -> add -> simple editor -> preview -> save
draft/publish where publication applies. Primary forms expose the common case;
technical keys, raw configuration, versions, and integration details belong in a
clearly labelled Advanced section.

No routine UI SHALL ask users to type UUIDs. People, roles, parties, parent records,
entities, phases, deliverables, and relationship targets use authorized searchable
selectors showing names and safe disambiguating context.

---

# 8. Authentication UI

Required components:

```text
LoginPage
AuthProvider
ProtectedRoute
PermissionGuard
UserMenu
```

Login behavior:

```text
submit credentials
→ show loading state
→ receive token/user
→ initialize auth state
→ navigate to workspace selection/default workspace
```

Authentication errors SHALL not expose sensitive backend details.

---

# 9. API Client

A shared API client SHALL:

- set base URL,
- attach bearer token,
- attach request ID where appropriate,
- decode standard API envelope,
- normalize errors,
- handle 401 globally,
- support cancellation/abort.

Example logical interface:

```typescript
apiClient.get<T>()
apiClient.post<T>()
apiClient.patch<T>()
apiClient.delete<T>()
```

Components SHALL NOT call `fetch` independently throughout the codebase unless explicitly justified.

---

# 10. API Type Strategy

Preferred approach:

Generate TypeScript types/client bindings from:

```text
contracts/openapi.yaml
```

Generated files SHALL NOT be manually edited.

Local view models MAY wrap generated API types where useful.

---

# 11. Query Key Strategy

TanStack Query keys SHALL be stable and structured.

Examples:

```typescript
["workspace", workspaceId]

["entities", workspaceId, filters]

["entity", entityId]

["entity-tree", workspaceId, rootId]

["entity-types", workspaceId]

["form-render", formId, entityId]

["documents", entityId]

["import-job", importJobId]
```

Cache invalidation SHALL be explicit after mutations.

---

# 12. Workspace Selection

Required components:

```text
WorkspaceListPage
WorkspaceCard
WorkspaceSelector
WorkspaceSettingsPage
WorkspaceMemberManager
```

Only workspaces returned by the backend SHALL be displayed.

The frontend SHALL not infer access from locally cached roles alone.

---

# 13. Entity Explorer

## 13.1 EntityTreeViewer

Purpose:

Render arbitrary hierarchy.

Required props conceptually:

```typescript
type EntityTreeViewerProps = {
  workspaceId: string;
  rootId?: string;
  selectedEntityId?: string;
  onSelect: (entityId: string) => void;
};
```

Required features:

- expand/collapse,
- lazy child loading,
- node selection,
- loading indicators,
- error retry,
- context actions based on permissions,
- search/filter integration.

The component SHALL not depend on domain-specific type names.

---

# 14. Lazy Hierarchy Loading

For large workspaces, tree rendering SHOULD fetch children on expansion rather than loading the entire hierarchy.

A node MAY include:

```typescript
{
  id: string;
  name: string;
  entityType: {
    id: string;
    name: string;
    iconKey?: string;
  };
  hasChildren: boolean;
}
```

---

# 15. Entity Detail Page

Generic route:

```text
/workspaces/:workspaceId/entities/:entityId
```

Required sections/tabs:

```text
Overview
Information
Forms
Documents
Relationships
History
```

Optional:

```text
Reviews
Phase
```

The same page SHALL serve all entity types.

---

# 16. Entity Header

`EntityHeader` SHOULD display:

- entity name,
- type label,
- status,
- parent breadcrumb,
- lock/read-only indicator,
- action menu.

Actions SHALL be conditionally visible based on permissions and current state.

---

# 17. Dynamic Attribute Display

Generic component:

```text
EntityAttributePanel
```

It SHALL render configured attributes using metadata definitions.

Unknown/unrecognized field types SHALL produce a safe fallback message, not crash the page.

---

# 18. Dynamic Form Rendering Architecture

Core component tree:

```text
DynamicFormRenderer
├── FormSectionRenderer
│   ├── DynamicFieldRenderer
│   │   ├── TextFieldRenderer
│   │   ├── RichTextFieldRenderer
│   │   ├── IntegerFieldRenderer
│   │   ├── DecimalFieldRenderer
│   │   ├── BooleanFieldRenderer
│   │   ├── DateFieldRenderer
│   │   ├── DateTimeFieldRenderer
│   │   ├── EnumFieldRenderer
│   │   ├── MultiEnumFieldRenderer
│   │   ├── UserReferenceRenderer
│   │   ├── EntityReferenceRenderer
│   │   ├── FileReferenceRenderer
│   │   └── DynamicTableField
```

---

# 19. Form Render Contract

The frontend SHALL consume the normalized contract returned by:

```text
GET /forms/{form_id}/render
```

The UI SHALL use server-provided:

- key,
- label,
- type,
- required,
- read-only,
- current/default value,
- options,
- visibility result/config,
- validation metadata,
- ordering,
- section metadata.

---

# 20. React Hook Form Integration

`DynamicFormRenderer` SHOULD instantiate a single React Hook Form context per form.

Field renderers SHALL register against stable field keys.

Example:

```typescript
register("risk_level")
```

Nested/repeating rows MAY use:

```text
useFieldArray
```

---

# 21. Zod Validation

Frontend validation MAY be generated from form metadata.

However:

- frontend validation is UX-only,
- backend validation remains authoritative,
- backend validation errors SHALL be mapped back to corresponding UI fields.

---

# 22. Visibility Rules

Conditional field visibility SHALL be evaluated consistently.

Preferred approach:

- backend returns normalized rule definitions or evaluated state,
- frontend evaluates simple deterministic client-side conditions for responsiveness,
- final submit remains server-validated.

Arbitrary executable expressions SHALL NOT be used.

---

# 23. Read-Only / Inherited Fields

Fields inherited from parent/context MAY be:

```text
read-only inherited
editable default
normal editable
```

UI SHALL visually distinguish read-only inherited values.

Bindings SHALL also distinguish live reference, editable suggestion, copied value,
and snapshot-on-submit. The field decoration SHALL communicate whether a value is
current canonical context, a suggestion awaiting action, locally edited, or a
historical snapshot. Users may inspect safe provenance through concise help/popover.

---

# 23.1 Form Context Header

Every governed form SHALL render a reusable `FormContextHeader` above its configured
sections. It consumes backend-authorized display items and may show project, phase,
deliverable/work item, selected service/entity, employer, contractor, responsible
party, dates, state, and lock status. It SHALL use human-readable links/selectors and
never expose raw context IDs.

Known route/work context is not repeated as editable fields unless the form
definition explicitly requires a separate snapshot/editable value. A route-context
change while dirty must trigger safe draft handling rather than save into another
context.

---

# 23.2 Form Assistance UX

Reusable assistance components SHALL show suggestions consistently for manual forms
and import review. Each candidate shows suggested value, concise reason, source
label/provenance, AI/deterministic indicator, confidence where meaningful, and
Accept/Edit/Reject actions. Bounded bulk acceptance is permitted only when outcomes
are visible and non-destructive.

Suggestions SHALL not replace typed/imported values automatically. Accepted values
remain visually distinguishable until saved and pass ordinary validation. Rejected
suggestions should not repeatedly interrupt the user unless evidence changes or the
user regenerates them.

---

# 24. Dynamic Repeating Tables

`DynamicTableField` SHALL support:

- add row,
- remove row,
- dynamic column definitions,
- per-cell validation,
- row-level validation messages,
- keyboard navigation where practical.

Example model:

```typescript
{
  key: "stakeholders",
  columns: [
    { key: "name", type: "TEXT" },
    { key: "power", type: "ENUM" },
    { key: "interest", type: "ENUM" }
  ]
}
```

---

# 25. Form Designer

Required components:

```text
FormDesignerPage
FieldPalette
FormCanvas
FormSectionEditor
FieldConfigurationPanel
RuleEditor
FormPreview
PublishDialog
```

Initial MVP MAY use button-based/configuration-panel design rather than sophisticated drag-and-drop if necessary.

The implementation SHALL prioritize correctness and metadata quality over visual complexity.

The default designer workflow SHALL ask for human labels and behavior. Section/field
technical keys are generated automatically and hidden under Advanced settings.
Field configuration uses plain-language choices such as “نمایش اطلاعات پروژه”،
“نمایش مقدار جاری خدمت”، “پیشنهاد قابل ویرایش”، “کپی هنگام ایجاد”، and “ثبت مقدار
در زمان ارسال” rather than raw binding JSON/mode codes.

---

# 26. Form Designer Rules

Form designer SHALL support:

- create sections,
- add fields,
- reorder fields,
- configure required/read-only,
- configure options,
- configure inheritance,
- configure visibility,
- preview form,
- publish form.

Published forms SHALL be displayed as immutable.

Creating changes to a published form SHALL use the new-version flow.

---

# 27. Document Panel

Required components:

```text
DocumentPanel
DocumentList
DocumentUploader
DocumentVersionList
DocumentPreviewDialog
DocumentDownloadAction
```

Document list SHOULD show:

- title,
- document type,
- current version,
- latest uploader,
- updated time,
- scan/preview status.

---

# 28. Upload UX

Upload component SHALL:

- validate obvious client-side size/type constraints,
- show upload progress when possible,
- not treat client validation as authoritative,
- show backend scan/processing state.

For asynchronous processing:

```text
Uploading
→ Processing
→ Scan Pending
→ Ready
```

or error state.

---

# 29. Document Preview

Preview dialog behavior:

- PDF: embedded viewer/browser rendering,
- image: image viewer,
- Office: backend-generated preview when ready,
- unsupported type: metadata + download action.

The frontend SHALL not attempt insecure local execution of uploaded document content.

---

# 30. Import Wizard

Required flow:

```text
Step 1 Upload
Step 2 Inspect
Step 3 Mapping
Step 4 Dry Run
Step 5 Conflict Review
Step 6 Confirm Commit
Step 7 Completion Summary
```

The wizard SHALL prevent commit before successful dry run.

The wizard is an embeddable contextual capability. Normal users launch it from an
eligible phase, deliverable, form, or output specification. The host supplies project,
phase, deliverable, target form/entity type, permitted profiles, return path, and
lock/read-only state. Known target choices SHALL not be requested again.

Import SHALL not appear as a normal top-level Project workspace navigation item.
Import profile/mapping administration belongs in the Administration console. A
protected job deep link MAY support recovery, audit, or support.

---

# 31. Import Mapping UI

Required capabilities:

- choose sheet,
- list source columns,
- choose target fields,
- configure matching keys,
- show sample source values,
- reuse stored import profile.

Matching choices SHALL use localized intent such as “تشخیص رکورد موجود با کد” or
“تشخیص با ترکیب این فیلدها.” Raw discriminators, attribute IDs, entity IDs, and
parent IDs SHALL not appear in the normal mapping flow.

Invalid mappings SHALL be highlighted before dry run.

---

# 32. Dry-Run UI

The UI SHALL clearly display:

```text
Rows read
Valid
Invalid
Creates
Updates
Unchanged
Conflicts
```

Validation errors SHALL be browsable by row.

---

# 33. Conflict Resolver

Conflict UI SHALL display:

```text
field
existing value
imported value
decision
```

Actions:

```text
MERGE
REPLACE
SKIP
```

Bulk resolution MAY be offered.

The UI SHALL not default silently to destructive overwrite.

---

# 34. Import Commit

Before commit, show explicit confirmation summarizing impact.

Example:

```text
80 records will be created
32 records will be updated
9 conflicts resolved
4 invalid rows excluded
```

Commit button SHALL be disabled when unresolved required conflicts remain.

---

# 35. Phase UI

Required components:

```text
PhaseList
PhaseStatusBadge
PhaseDetailPanel
PhaseLockAction
DeliverableList
```

Locked state SHALL be visually clear.

Edit controls for locked content SHOULD be hidden/disabled, while backend remains authoritative.

---

# 36. Review Comments UI

Required components:

```text
ReviewCommentList
ReviewCommentComposer
ResolveCommentAction
RevisionStatusBadge
```

Comments SHALL display:

- author,
- timestamp,
- text,
- status.

Review UI SHALL identify the authority and lifecycle kind of each action. Internal
contractor feedback, formal reviewer comments, technical recommendation/sign-off,
project-manager recommendation, and employer acceptance SHALL not share ambiguous
"Approve" copy or controls.

---

# 36.1 Governed Deliverable Workspace

One metadata-driven deliverable workspace SHALL compose reusable panels for:

```text
requirements and assignment
structured data and repository files
version/package history
internal review
formal submission
external comments and revision actions
technical outcome
project-manager recommendation
acceptance status and conditions
audit timeline
```

The backend SHALL return current state and authorized available actions. Components
MAY hide unavailable actions for usability, but every action remains backend
authorized. The UI SHALL always show which artifact version a decision concerns.

---

# 36.2 Role-Appropriate Workspaces

Personal, contractor-leader, Project Officer, Project Manager, technical-reviewer,
and employer views SHALL be reusable projections/widgets over common APIs—not
persona-specific data stores or hard-coded domain pages. Each view should prioritize
assigned work, deadlines, overdue/blocking items, review queues, comments,
completeness, decisions, and notifications appropriate to the actor.

---

# 36.3 Contextual Communication and Notifications

Threads and notifications SHALL display their kind, visibility, linked target,
participants, time, read/action-required state, and safe navigation. Internal notes,
formal comments, clarifications, announcements, and reminders SHALL remain visually
and semantically distinguishable. This feature is contextual project communication,
not unrestricted chat.

---

# 37. Relationship Panel

`RelationshipPanel` SHALL support:

- incoming relationships,
- outgoing relationships,
- relationship type filtering,
- create relationship,
- delete relationship if permitted.

Entity selectors SHALL search generic entities rather than use domain-specific pickers.

Relationship UX SHALL be sentence/task oriented. From the current record it presents
only compatible configured forward/reverse labels and target types, then searches
authorized targets by name and contextual description. It SHALL not ask users to
reason about source/target direction, UUIDs, or cardinality codes. Existing links are
rendered using natural phrases and preserve identity across unrelated entity edits.

An authorized impact action MAY show where the current item is referenced throughout
active project work and which items require review after a material change. Historical
snapshots are labelled as historical and are never offered as bulk overwrite targets.

---

# 38. Dashboard Architecture

Required generic widgets:

```text
KPIWidget
TableWidget
ChartWidget
ProgressWidget
```

Dashboard components SHALL consume server-generated validated data.

The browser SHALL NOT accept arbitrary SQL or execute user-defined backend queries.

---

# 39. Dashboard Builder

P1 capability.

Authorized users SHOULD configure:

- widget type,
- metric/data source,
- filters,
- labels,
- display options,
- order/layout.

Configuration SHALL be metadata-driven.

---

# 39.1 Report Template Designer

The report designer SHALL provide a WordPress-like list/add/edit/preview/publish
experience using reusable, metadata-driven sections and widgets. Authorized users can
select required project/party details, reporting period, progress, phases,
deliverables, risks/issues, reviews, acceptance, narrative, branding, headers,
footers, and signature areas through safe human-readable bindings.

It SHALL show missing required content before generation, provide a realistic
preview, identify draft/published/retired versions, and display generation provenance.
The UI SHALL never expose SQL, executable templates, or unauthorized field paths.
Generated formal reports link to their immutable output and template/data versions.

---

# 40. Permission Guard

Generic component:

```typescript
<PermissionGuard permission="FORM_DESIGN">
  <FormDesignerAction />
</PermissionGuard>
```

Permission guards improve UX only.

They SHALL not be treated as security boundaries.

---

# 41. Workspace Guard

Routes SHALL verify that selected workspace is currently accessible.

If backend returns 403/404:

- clear invalid workspace-specific state,
- navigate to appropriate fallback,
- show safe error.

---

# 42. Locked Resource UX

When backend returns:

```text
423 RESOURCE_LOCKED
```

frontend SHALL show a clear read-only/locked message.

It SHOULD not repeatedly retry mutation requests.

---

# 43. Concurrency Conflict UX

For:

```text
409 STALE_VERSION
```

UI SHALL tell user the record changed since it was loaded.

Recommended actions:

```text
Reload latest
Review changes
Cancel local edit
```

Blind overwrite SHALL not occur automatically.

---

# 44. Standard Error Handling

Global error handling SHALL distinguish:

- network errors,
- authentication expiry,
- authorization failure,
- validation error,
- conflict,
- locked state,
- server failure.

Generic "Something went wrong" MAY be fallback only.

Field errors SHALL be attached to fields where possible.

---

# 45. Loading States

Every asynchronous screen SHALL provide appropriate loading behavior.

Avoid blank pages during:

- initial queries,
- lazy tree loading,
- document processing,
- imports,
- dashboard loading.

Skeletons/spinners MAY be used appropriately.

---

# 46. Empty States

Provide explicit empty states.

Examples:

```text
No entities yet.
No documents uploaded.
No forms configured.
No import conflicts.
```

Empty state SHOULD include permitted next action where useful.

---

# 47. Notifications

Use centralized notifications/toasts for:

- successful mutations,
- background job completion if surfaced,
- recoverable errors.

Do not use toasts as the only representation of critical validation errors.

---

# 48. Accessibility

Frontend SHOULD target WCAG 2.1 AA.

Requirements include:

- labels for form fields,
- keyboard navigation,
- focus management,
- semantic controls,
- sufficient contrast using design-system defaults,
- accessible error messages,
- table accessibility.

---

# 49. Persian-First Localization and RTL

Persian/Farsi (`fa-IR`) is the mandatory primary user-facing language for the
MVP. The document root SHALL use `lang="fa"` and `dir="rtl"`.

All platform UI copy SHALL be obtained through an internationalization resource
layer. Persian labels SHALL not be scattered as literals through components.
Metadata-provided labels and user-authored values SHALL be rendered as data and
SHALL not be passed through translation keys.

MUI SHALL be configured with:

- theme direction `rtl`,
- the `faIR` component locale,
- an Emotion cache using the approved RTL Stylis plugin,
- a Persian-capable application font,
- global RTL direction so portal-based components inherit correctly.

Navigation, dialogs, tables, forms, notifications, pagination, breadcrumbs,
tooltips, menus, focus order, and next/previous icons SHALL be tested for RTL
behavior. CSS and MUI styling SHALL prefer logical or direction-neutral
properties such as `margin-inline-start`, `padding-inline-end`, `inset-inline`,
and MUI spacing shorthands instead of physical left/right assumptions.

Validation messages, loading states, empty states, buttons, aria labels, page
titles, and user-facing safe API errors SHALL be Persian. English remains valid
for code identifiers, routes, API fields, stable error codes, logs, and developer
documentation.

Dates and numbers SHALL be formatted through centralized localization helpers;
components SHALL not choose a calendar or numeral policy independently. API ISO
timestamps and JSON numeric values SHALL not be localized in transport.

---

# 50. Responsive Design

Primary target:

```text
desktop/laptop browser
```

The system SHOULD remain usable on tablets.

Complex administration/form-designer experiences need not be fully optimized for small mobile screens in MVP.

---

# 51. Security Rules

Frontend SHALL NOT:

- store passwords,
- expose storage credentials,
- rely on hidden buttons for authorization,
- inject unsanitized HTML,
- use `eval`,
- render untrusted rich HTML without sanitization.

If rich text is supported, content SHALL be sanitized.

---

# 52. Token Storage

Token strategy SHALL follow security specification.

If bearer tokens are kept client-side, storage mechanism SHALL minimize XSS exposure.

HTTP-only secure cookies MAY be preferable depending on final auth architecture.

The frontend agent SHALL not independently choose a weaker token strategy contrary to `11_SECURITY_SPECIFICATION.md`.

---

# 53. Browser Storage

Sensitive enterprise content SHALL not be persisted unnecessarily in localStorage.

Acceptable local preferences MAY include:

- sidebar state,
- theme preference,
- last workspace ID.

Server data SHALL primarily live in query cache/memory.

---

# 54. File Access

Document downloads/previews SHALL use backend-authorized endpoints or short-lived URLs.

Permanent object URLs SHALL not be stored client-side.

---

# 55. Performance

Frontend SHALL:

- code split major routes,
- lazy-load expensive administration pages,
- paginate large lists,
- lazy-load hierarchy children,
- avoid unnecessary rerenders,
- avoid duplicate API calls.

---

# 56. Virtualization

Large tabular lists/tree views SHOULD use virtualization when performance data justifies it.

Do not introduce virtualization complexity prematurely for small datasets.

---

# 57. Metadata Caching

Entity type and form metadata MAY use longer TanStack Query stale times than rapidly changing operational data.

Metadata mutation SHALL invalidate relevant cache keys.

---

# 58. Form Draft Preservation

P1 capability:

Form drafts MAY be preserved through:

- backend draft saves,
- controlled temporary client state.

Browser-only draft persistence SHALL not become the authoritative source.

---

# 59. Testing Strategy

Frontend testing SHALL include:

```text
unit/component tests
integration-style component tests
end-to-end Playwright tests
```

---

# 60. Component Tests

Required examples:

```text
DynamicFieldRenderer renders ENUM as selector
DynamicFieldRenderer respects read-only
DynamicTableField adds/removes rows
PermissionGuard hides unauthorized action
EntityTreeViewer loads child nodes
```

---

# 61. Form Integration Tests

Test:

```text
fetch render definition
→ render fields
→ populate inherited values
→ enter values
→ submit
→ display backend validation errors correctly
```

---

# 62. Import UI Tests

Test:

```text
upload
→ map
→ dry run
→ show conflict
→ resolve
→ commit
→ completion summary
```

The commit step SHALL be impossible before dry run.

---

# 63. E2E Tests

Playwright MVP scenario SHALL cover:

```text
login
→ select/create workspace
→ create metadata
→ create entity
→ create child entity
→ fill dynamic form
→ upload document
→ import workbook
→ resolve conflict
→ manager lock phase
→ analyst edit rejected
```

---

# 64. Mocking Strategy

Component tests MAY mock API boundaries.

Critical integration/E2E flows SHALL use real backend contracts or generated API mocks matching OpenAPI.

Mock types SHALL not drift from `contracts/openapi.yaml`.

---

# 65. Frontend Code Quality

Required:

- strict TypeScript,
- no unexplained `any`,
- linting,
- deterministic formatting,
- reusable hooks/components,
- clear module boundaries.

---

# 66. Prohibited Frontend Anti-Patterns

Reject:

```text
BusinessProcessForm.tsx
ApplicationPage.tsx
```

Also reject:

- duplicate server state in Redux,
- direct object-storage credentials,
- raw `fetch` scattered across components,
- permission logic implemented differently per page,
- hard-coded attribute keys in domain-specific conditionals,
- huge single components containing API + rendering + business logic,
- client-only protection of locked data,
- silent overwrite on concurrency conflicts,
- unsafe HTML rendering,
- unbounded rendering of huge entity trees.

---

# 67. AI Frontend Agent Task Protocol

Before coding:

```text
TASK
REQUIREMENTS
ROUTES_AFFECTED
COMPONENTS_AFFECTED
API_DEPENDENCIES
STATE_IMPACT
ACCESSIBILITY_IMPACT
SECURITY_IMPACT
IMPLEMENTATION_PLAN
```

After coding:

```text
SUMMARY
FILES_CHANGED
COMPONENTS_ADDED
API_USAGE
TESTS_ADDED
TEST_RESULTS
KNOWN_LIMITATIONS
ARCHITECTURE_DEVIATIONS
```

---

# 68. Definition of Done

A frontend feature is complete only when:

- [ ] generic architecture is preserved,
- [ ] no domain-specific component was added,
- [ ] API contract is followed,
- [ ] loading/error/empty states exist,
- [ ] permissions are reflected in UX,
- [ ] backend remains authoritative,
- [ ] accessibility basics are covered,
- [ ] component tests exist,
- [ ] relevant E2E flow is updated,
- [ ] TypeScript checks pass,
- [ ] no security anti-pattern is introduced.

---

# 69. Requirement Traceability

```text
AUTH-FR-*  → auth module
WS-FR-*    → workspace pages/components
META-FR-*  → metadata admin
ENT-FR-*   → EntityTreeViewer, EntityDetailPage
HIER-FR-*  → EntityTreeViewer, reparent actions
REL-FR-*   → RelationshipPanel
FORM-FR-*  → FormDesigner, DynamicFormRenderer
DATA-FR-*  → form instance screens
DOC-FR-*   → DocumentPanel
IMP-FR-*   → ImportWizard
PHASE-FR-* → phase UI
REV-FR-*   → review components
GOV-FR-*   → governed deliverable workspace and transition history
WORK-FR-*  → personal/management queues and planning components
COM-FR-*   → contextual conversation and notification components
ACC-FR-*   → acceptance decision/condition workspace
CONF-FR-*  → configuration lifecycle UI
PARTY-FR-* → people/organization administration and selectors
CTX-FR-*   → FormContextHeader and binding-source UX
ASSIST-FR-* → suggestion components in forms/import review
REF-FR-*   → natural relationships and impact/snapshot comparison
UX-FR-*    → project/admin information architecture and progressive disclosure
RPT-FR-*   → dashboard components
AUD-FR-*   → audit viewer
```

---

# 70. Related Specifications

```text
00_PROJECT_CONTEXT.md
01_ARCHITECTURE_RULES.md
02_SYSTEM_REQUIREMENTS.md
03_DATABASE_SPECIFICATION.md
04_API_SPECIFICATION.md
05_BACKEND_SPECIFICATION.md
07_AI_AGENT_ROLES.md
08_TASK_BACKLOG.md
09_TEST_SPECIFICATION.md
10_DEPLOYMENT_GUIDE.md
11_SECURITY_SPECIFICATION.md
12_CURRENT_STATUS.md
13_IMPLEMENTATION_ROADMAP.md
14_PROJECT_USAGE_SCENARIOS.md
contracts/openapi.yaml
```
