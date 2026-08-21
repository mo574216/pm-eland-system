# Infrastructure

This directory contains container and local-development infrastructure.

## Local development stack

Copy the repository `.env.example` to `.env`, replace every placeholder, and run from the repository root:

```powershell
docker compose -f infrastructure/compose/docker-compose.dev.yml up --build -d
```

The command starts PostgreSQL, MinIO, Redis, applies Alembic migrations, and then starts the backend and frontend. Host ports bind to `127.0.0.1` only. Open:

- frontend: `http://localhost:5173`
- backend documentation: `http://localhost:8000/docs`
- MinIO console: `http://localhost:9001`

Verify the running environment:

```powershell
powershell -ExecutionPolicy Bypass -File infrastructure/scripts/smoke-test.ps1
```

Stop containers while preserving named-volume data:

```powershell
docker compose -f infrastructure/compose/docker-compose.dev.yml down
```

Removing named volumes with `down -v` permanently deletes local PostgreSQL, MinIO, Redis, and frontend dependency data.

FND-006 will add the CI baseline. Production deployment, observability, backup, and restore procedures remain M6 work.
