# AI Agent Instructions

This repository implements a metadata-driven enterprise architecture and project knowledge platform.

The core architectural invariant is:

> Domain concepts are data, not code.

Before making any change:

1. Read `ai_context/00_PROJECT_CONTEXT.md`.
2. Read `ai_context/01_ARCHITECTURE_RULES.md`.
3. Read `ai_context/02_SYSTEM_REQUIREMENTS.md`.
4. Read `ai_context/12_CURRENT_STATUS.md`.
5. Read all specification files relevant to the task.
6. Read relevant ADRs under `ADR/`.
7. Read shared contracts under `contracts/` when the task affects APIs, permissions, or errors.

## Mandatory Rules

- Do not invent product requirements.
- Do not violate architectural constraints.
- Do not create domain-specific tables, ORM models, services, or UI pages for configurable business concepts.
- Prefer reusable, generic, metadata-driven components.
- Do not hard-code configurable attribute names or entity-type names into business logic.
- Backend authorization is authoritative; frontend guards are UX only.
- Preserve workspace isolation for every workspace-scoped resource.
- Never silently overwrite existing data during imports.
- Preserve immutable document version history.
- Respect phase/resource locking rules.
- Material mutations must be audited where required by the specifications.
- Do not modify published API contracts without updating the relevant specification and contract files.
- Do not make database schema changes without Alembic migrations.
- Do not modify unrelated functionality.
- Never commit passwords, tokens, API keys, certificates, or other secrets.
- Do not weaken security controls merely to make tests pass.

## Shared Contracts

When relevant, treat these files as authoritative integration contracts:

- `contracts/openapi.yaml`
- `contracts/error-codes.yaml`
- `contracts/permissions.yaml`

Do not independently invent API payloads, error codes, or permission names when these contracts already define them.

## Architecture Decisions

Important architectural decisions are recorded under:

`ADR/`

If a required implementation conflicts with an accepted ADR or would materially change the architecture, do not silently implement the deviation. Document the issue and propose a new ADR.

## Before Coding

For every non-trivial task, identify:

- requirements being implemented,
- files/modules affected,
- database impact,
- API impact,
- security impact,
- test plan,
- assumptions.

Prefer the smallest change that completely satisfies the task.

## Testing

Implement tests alongside functionality.

Before completing an implementation task, run all applicable:

- lint
- formatting checks
- type checking
- unit tests
- integration tests
- frontend tests
- build
- migration validation

Do not claim completion if required checks fail.

## Completion Report

At the end of an implementation task, report:

- `SUMMARY`
- `FILES_CHANGED`
- `DATABASE_CHANGES`
- `API_CHANGES`
- `TESTS_ADDED`
- `TEST_RESULTS`
- `SECURITY_IMPACT`
- `KNOWN_LIMITATIONS`
- `ARCHITECTURE_DEVIATIONS`

If there are no architecture deviations, state:

`ARCHITECTURE_DEVIATIONS: None`
