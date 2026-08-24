# Architecture Decision Records

This directory stores Architecture Decision Records (ADRs).

ADRs document decisions that affect the long-term structure, security, persistence, integration, or deployment architecture.

## When an ADR Is Required

Create an ADR when changing or introducing:

```text
canonical persistence model
authentication model
hierarchy representation
API protocol/version strategy
document storage architecture
background-job infrastructure
form rule language
search-engine architecture
runtime AI provider architecture
multi-tenant architecture
```

## ADR Status Values

```text
PROPOSED
ACCEPTED
SUPERSEDED
REJECTED
DEPRECATED
```

## Naming

```text
ADR-0001-short-title.md
ADR-0002-short-title.md
...
```

## Required Sections

Every ADR SHALL contain:

```text
Title
Status
Date
Context
Decision
Alternatives Considered
Consequences
Migration Impact
Security Impact
Related Requirements
Supersedes / Superseded By
```

## Current ADRs

- `ADR-0008-live-references-assistance-and-versioned-snapshots.md` - ACCEPTED
- `ADR-0007-human-centered-contextual-experience.md` - ACCEPTED
- `ADR-0006-configurable-governance-authority-lanes.md` - ACCEPTED
- `ADR-0005-rtl-portal-experience.md` - ACCEPTED
- `ADR-0004-bearer-access-and-rotating-refresh-sessions.md` - ACCEPTED
- `ADR-0003-persian-first-localization.md` — ACCEPTED
- `ADR-0002-async-sqlalchemy-session-model.md` - ACCEPTED

- `ADR-0001-metadata-driven-domain-model.md` — ACCEPTED
