# Backend

FastAPI foundation for the metadata-driven project knowledge platform.

## Local setup

Requirements:

```text
Python 3.12+
uv
```

Install and verify:

```bash
uv sync --all-groups
uv run ruff format --check .
uv run ruff check .
uv run mypy app scripts tests
uv run pytest
uv run python -m scripts.create_test_database --admin-url postgresql+psycopg://user:password@localhost/postgres
DATABASE_URL=postgresql+psycopg://user:password@localhost/database uv run alembic upgrade head
```

Run the development server:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health endpoints:

```text
GET http://localhost:8000/health/live
GET http://localhost:8000/health/ready
```

The public API router is mounted at `/api/v1`. When `DATABASE_URL` is configured, readiness executes a real PostgreSQL probe and fails closed if the dependency is unavailable.

The runtime uses async SQLAlchemy sessions with psycopg 3. Alembic owns all relational schema changes. Services own transaction commit/rollback boundaries; repositories must not commit independently.

On Windows, the application selects Python's selector event-loop policy because psycopg async connections do not support the default Proactor event loop.

The test-database command is idempotent and accepts only lowercase database names ending in `_test`. Set `TEST_DATABASE_ADMIN_URL` and optionally `TEST_DATABASE_NAME` instead of passing command-line arguments when preferred.
