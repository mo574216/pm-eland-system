# ADR-0002 - Async SQLAlchemy Session Model

**Status:** ACCEPTED  
**Date:** 2026-08-21  
**Decision Owners:** Project Architecture  
**Related Files:** `ai_context/03_DATABASE_SPECIFICATION.md`, `ai_context/05_BACKEND_SPECIFICATION.md`

## Context

The FastAPI backend requires PostgreSQL 16+, SQLAlchemy 2.x, request-scoped sessions, explicit transaction boundaries, background-job compatibility, health checks, and Alembic migrations. The session and driver model must be fixed before FND-004 because it affects dependency injection, service transaction ownership, tests, and deployment.

## Decision

The application shall use:

- SQLAlchemy 2.x asynchronous engines and `AsyncSession` for runtime API and worker operations;
- psycopg 3 through the `postgresql+psycopg` dialect;
- one `AsyncSession` per request or explicit background-job unit of work;
- service-owned transactions, with repositories prohibited from committing independently;
- application-lifespan ownership of the engine and session factory;
- synchronous Alembic execution using SQLAlchemy and psycopg 3 for predictable migration tooling;
- explicit engine disposal during application shutdown.

Database readiness shall execute `SELECT 1` through the runtime async engine. It shall fail closed when PostgreSQL is configured but unavailable.

## Alternatives Considered

### Synchronous SQLAlchemy runtime

Rejected because it would require thread-pool execution for database work in the async FastAPI application and would provide a less direct foundation for concurrent I/O-heavy workflows.

### asyncpg driver

Rejected for the initial baseline because psycopg 3 supports both async runtime access and synchronous Alembic migration execution, reducing driver duplication.

### Globally shared sessions

Rejected because sessions are mutable units of work and must not be shared across requests or jobs.

### Repository-owned commits

Rejected because multi-repository operations such as import commit, document version creation, and entity-plus-audit mutations require service-level atomic transactions.

## Consequences

Positive:

- runtime database I/O aligns with FastAPI's async model;
- one PostgreSQL driver supports runtime and migrations;
- transaction ownership remains explicit and testable;
- request and background-job isolation are preserved.

Negative:

- service and repository code must consistently use async SQLAlchemy APIs;
- accidental lazy loading can cause async-context failures and shall be avoided;
- tests require PostgreSQL for integration behavior; SQLite is not an acceptable substitute.

## Migration Impact

FND-004 initializes Alembic and the runtime database foundation. All future relational schema changes must use Alembic revisions. Moving to a different driver or synchronous runtime model requires a superseding ADR.

## Security Impact

- Database URLs remain external configuration and must never be logged or committed with credentials.
- Production application and migration database roles should be separated.
- Readiness reports only dependency state and never connection details.
- Request-scoped sessions reduce cross-request state leakage risk.

## Related Requirements

```text
DB-RULE-005
DB-RULE-006
MAINT-NFR-001
MAINT-NFR-003
REL-NFR-001
OBS-NFR-003
```

## Supersedes / Superseded By

Supersedes: None  
Superseded by: None
