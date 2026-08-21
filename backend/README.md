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
uv run mypy app tests
uv run pytest
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

The public API router is mounted at `/api/v1`. Database connectivity is intentionally injected as a readiness probe and will be wired by FND-004.
