# Deployment Guide

**File:** `10_DEPLOYMENT_GUIDE.md`  
**Status:** Normative  
**System:** Metadata-Driven Enterprise Architecture Management Platform  
**Version:** 1.0  
**Audience:** DevOps engineers, AI DevOps agents, backend engineers, security engineers, release managers

---

# 1. Purpose

This document defines the deployment architecture, environment strategy, CI/CD flow, secrets management, observability, backup, restore, scaling, and release procedures for the platform.

The deployment model SHALL support:

- local development,
- CI testing,
- staging,
- production.

The initial implementation SHOULD prioritize a simple containerized deployment while preserving a path toward horizontal scaling.

---

# 2. Normative References

Deployment SHALL conform to:

```text
01_ARCHITECTURE_RULES.md
02_SYSTEM_REQUIREMENTS.md
03_DATABASE_SPECIFICATION.md
04_API_SPECIFICATION.md
05_BACKEND_SPECIFICATION.md
09_TEST_SPECIFICATION.md
11_SECURITY_SPECIFICATION.md
```

---

# 3. Deployment Principles

## DEP-RULE-001 — Containerized Services

Application services SHOULD be packaged as containers.

Core services:

```text
frontend
backend
worker
postgres
minio
redis
```

---

## DEP-RULE-002 — Immutable Application Images

Application code SHALL be deployed through versioned container images.

Production servers SHALL NOT be patched by manually editing application source inside containers.

---

## DEP-RULE-003 — Externalized Configuration

Environment-specific settings SHALL be injected at runtime.

Secrets SHALL not be embedded in images or source control.

---

## DEP-RULE-004 — Automated Migrations

Database schema changes SHALL use Alembic.

Production migration execution SHALL be explicit and controlled.

---

## DEP-RULE-005 — Separate Environments

At minimum:

```text
development
staging
production
```

Production SHALL not share database/storage credentials with development.

---

# 4. Repository Deployment Structure

Recommended:

```text
infrastructure/
├── docker/
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   └── worker.Dockerfile
├── compose/
│   ├── docker-compose.dev.yml
│   └── docker-compose.test.yml
├── k8s/
│   └── future/
├── scripts/
│   ├── migrate.sh
│   ├── backup-db.sh
│   ├── restore-db.sh
│   └── smoke-test.sh
└── monitoring/
```

Exact locations MAY differ.

---

# 5. Local Development Topology

Recommended Docker Compose topology:

```text
Browser
   |
   v
Frontend :5173
   |
   v
Backend :8000
   |
   +---------------------+
   |          |          |
PostgreSQL   MinIO      Redis
:5432        :9000      :6379
                         |
                         v
                       Worker
```

---

# 6. Local Compose Services

## 6.1 frontend

Responsibilities:

- run Vite dev server,
- connect to backend API,
- hot reload in development.

---

## 6.2 backend

Responsibilities:

- FastAPI,
- API endpoints,
- database access,
- storage authorization,
- job submission.

---

## 6.3 worker

Responsibilities:

- document conversion,
- file scans,
- large imports,
- report jobs,
- future AI tasks.

---

## 6.4 postgres

Development PostgreSQL version SHALL match production major version where practical.

Target:

```text
PostgreSQL 16+
```

---

## 6.5 minio

Development object storage.

Buckets MAY include:

```text
documents
previews
imports
temporary
```

Buckets SHALL remain private.

---

## 6.6 redis

Used for:

- background queue,
- optional caching,
- optional rate-limiting state.

---

# 7. Development Startup

Recommended command:

```bash
docker compose -f infrastructure/compose/docker-compose.dev.yml up --build
```

Expected startup sequence:

```text
postgres healthy
→ minio healthy
→ redis healthy
→ migration/init step
→ backend ready
→ worker ready
→ frontend ready
```

---

# 8. Environment Variable Contract

A `.env.example` SHALL document all required variables with safe placeholders.

Recommended variables:

```text
APP_ENV
APP_NAME
API_V1_PREFIX

DATABASE_URL

JWT_SECRET
JWT_ALGORITHM
JWT_EXPIRY_SECONDS

S3_ENDPOINT
S3_REGION
S3_BUCKET_DOCUMENTS
S3_BUCKET_PREVIEWS
S3_BUCKET_IMPORTS
S3_ACCESS_KEY
S3_SECRET_KEY
S3_USE_SSL

REDIS_URL

MAX_UPLOAD_SIZE_BYTES
ALLOWED_MIME_TYPES

CORS_ALLOWED_ORIGINS

LOG_LEVEL

CELERY_BROKER_URL
CELERY_RESULT_BACKEND

MALWARE_SCAN_ENABLED
PREVIEW_WORKER_ENABLED
```

Production secrets SHALL come from an approved secret-management mechanism.

---

# 9. Secrets Management

Allowed production approaches include:

- Kubernetes Secrets with appropriate encryption controls,
- cloud secret manager,
- HashiCorp Vault,
- CI/CD protected secret store.

Prohibited:

```text
committed .env
hard-coded JWT secrets
hard-coded DB passwords
hard-coded MinIO credentials
```

---

# 10. Frontend Build

Production frontend SHALL be built as static assets.

Typical flow:

```text
npm ci
npm run typecheck
npm run test
npm run build
```

The image SHOULD serve static assets through:

- nginx,
- CDN,
- approved static hosting layer.

---

# 11. Backend Image Build

Backend image SHOULD:

- use pinned base image,
- install only required runtime dependencies,
- run as non-root user where practical,
- exclude development tooling from final runtime layer,
- define health endpoint access.

Multi-stage build is recommended.

---

# 12. Worker Image

Worker MAY reuse backend code image with different command.

Example:

```text
same code artifact
different process command
```

This reduces image drift.

---

# 13. Staging Topology

Staging SHOULD resemble production.

Recommended:

```text
Load Balancer / Reverse Proxy
         |
    -------------
    |           |
Frontend      Backend
                |
              Worker
                |
      ---------------------
      |         |         |
PostgreSQL    Object     Redis
              Storage
```

Staging SHALL use separate:

- database,
- storage buckets,
- secrets,
- domains.

---

# 14. Production Topology

Recommended first production topology:

```text
Internet/User
     |
     v
Reverse Proxy / Load Balancer
     |
     +---------------------+
     |                     |
Frontend                Backend API
                           |
                 ---------------------
                 |         |         |
             PostgreSQL  Redis   Object Storage
                           |
                         Workers
```

---

# 15. Reverse Proxy

Responsibilities:

- TLS termination,
- HTTPS redirect,
- request size limit,
- proxy headers,
- optional rate limiting,
- routing frontend/API.

Possible implementations:

```text
nginx
Traefik
cloud load balancer
```

---

# 16. TLS

Production SHALL use HTTPS.

Certificates SHALL:

- be valid,
- be renewed automatically where practical,
- avoid weak protocols/ciphers.

HTTP SHOULD redirect to HTTPS.

---

# 17. CORS

Production backend SHALL allow only explicit frontend origins.

Example:

```text
https://ea.example.com
```

Wildcard:

```text
*
```

SHALL not be used with credentials in production.

---

# 18. Database Deployment

Production PostgreSQL SHOULD use:

- managed PostgreSQL, or
- controlled dedicated instance.

Requirements:

```text
regular backups
restricted network access
TLS where supported
non-superuser app role
migration role separation
monitoring
```

---

# 19. Database Roles

Recommended:

```text
platform_app
platform_migration
platform_readonly
```

`platform_app`:

- DML only,
- no schema modification.

`platform_migration`:

- migration permissions.

---

# 20. Migration Release Procedure

Recommended sequence:

```text
1. Build release images
2. Run tests
3. Backup database if required
4. Execute Alembic migration
5. Verify migration
6. Deploy backend/workers
7. Deploy frontend
8. Run smoke tests
```

Backward-incompatible migrations require explicit rollout strategy.

---

# 21. Zero/Low Downtime Migration Guidance

Prefer:

```text
additive schema changes
nullable columns first
backfill
application rollout
constraint tightening later
```

Avoid:

```text
rename/remove column used by active old version
```

in a single deployment without compatibility planning.

---

# 22. CI/CD Pipeline

Recommended stages:

```text
Checkout
  ↓
Secret Scan
  ↓
Backend Lint/Type Check
  ↓
Frontend Lint/Type Check
  ↓
Unit Tests
  ↓
Integration Tests
  ↓
Migration Test
  ↓
Frontend Build
  ↓
Backend Image Build
  ↓
Frontend Image Build
  ↓
Container Scan
  ↓
Deploy Staging
  ↓
Smoke/E2E
  ↓
Production Approval
  ↓
Deploy Production
```

---

# 23. Branch Protection

Protected branches SHOULD require:

- passing CI,
- code review,
- no unresolved critical security finding,
- migration review if schema changed.

---

# 24. Image Tagging

Do not rely only on:

```text
latest
```

Production images SHOULD be immutable and versioned using:

```text
git SHA
release version
```

Example:

```text
platform-backend:1.3.0
platform-backend:4f3d91a
```

---

# 25. Deployment Configuration by Environment

Example:

```text
development:
debug true
local minio
verbose logs

staging:
debug false
production-like dependencies

production:
debug false
strict CORS
secure secrets
TLS
monitoring
backups
```

---

# 26. Health Checks

Backend:

```text
GET /health/live
GET /health/ready
```

Liveness:

- process responsive.

Readiness:

- critical database connectivity,
- optionally required queue/storage dependencies.

---

# 27. Worker Health

Workers SHOULD expose or emit health state through:

- queue heartbeat,
- process monitoring,
- job telemetry.

A worker outage SHOULD not necessarily make read-only API unavailable.

---

# 28. Startup and Readiness

Application SHALL not advertise readiness before:

- required configuration loaded,
- database reachable,
- schema at expected version.

---

# 29. Logging

Production logs SHOULD be structured JSON.

Include:

```text
timestamp
level
service
request_id
user_id when appropriate
workspace_id when appropriate
path
status
duration
```

Do not log:

```text
passwords
tokens
secret keys
raw sensitive uploads
```

---

# 30. Centralized Logging

Recommended future/production options:

```text
ELK/OpenSearch
Loki
cloud logging
```

Exact stack MAY vary.

---

# 31. Metrics

Recommended metrics:

```text
request rate
request latency
5xx rate
4xx rate
DB connections
DB query latency
queue depth
worker failures
job duration
object storage errors
import failure rate
document preview failure rate
```

---

# 32. Monitoring

Recommended:

```text
Prometheus
Grafana
```

or cloud-equivalent services.

Alerting SHOULD cover:

```text
backend unavailable
DB unavailable
high error rate
queue backlog
worker down
disk/storage pressure
backup failure
```

---

# 33. Error Monitoring

Application exceptions SHOULD be centrally observable.

Possible tools:

```text
Sentry
OpenTelemetry collector
cloud APM
```

Sensitive data redaction SHALL be configured.

---

# 34. OpenTelemetry

P1 recommendation:

Instrument:

- API requests,
- database queries,
- background jobs.

This improves cross-service traceability.

---

# 35. Object Storage Deployment

Production object storage MAY use:

```text
MinIO
AWS S3
Azure-compatible abstraction only if StorageProvider supports it
```

Requirements:

- private buckets,
- version-safe object keys,
- backup/replication strategy,
- lifecycle policies for temporary objects.

---

# 36. Object Storage Buckets

Recommended separation:

```text
documents
previews
imports
quarantine
temporary
```

Temporary content SHALL have retention/cleanup policies.

---

# 37. Backup Strategy — PostgreSQL

Production SHALL have scheduled backups.

Recommended baseline:

```text
daily full/logical or base backup
continuous WAL/PITR where required
```

Exact RPO drives frequency.

---

# 38. Backup Strategy — Object Storage

Document data SHALL have:

- replication,
- backup,
- provider durability guarantees,

according to production environment.

Database backup alone is insufficient.

---

# 39. Restore Testing

Backups SHALL be periodically restored into a clean environment.

Validation SHALL include:

```text
database starts
migrations consistent
users/workspaces/entities present
document metadata valid
sample object files retrievable
```

---

# 40. RPO and RTO

Before production approval, organization SHOULD define:

```text
RPO — Recovery Point Objective
RTO — Recovery Time Objective
```

Illustrative starting target:

```text
RPO: 1 hour
RTO: 4 hours
```

These are not contractual until project owner approves them.

---

# 41. Disaster Recovery Procedure

Document:

```text
incident declaration
database restoration
object storage restoration
secret restoration
service redeployment
smoke validation
traffic restoration
post-incident review
```

---

# 42. Horizontal Scaling

Backend SHOULD remain stateless so multiple replicas can run.

Scaling:

```text
Backend replicas ↑
Worker replicas ↑
```

Shared state remains in:

```text
PostgreSQL
Redis
Object storage
```

---

# 43. Worker Scaling

Different queues MAY be introduced for:

```text
imports
document previews
malware scans
AI jobs
```

to prevent one workload starving another.

---

# 44. Redis Reliability

If Redis is required for critical queued jobs, deployment SHALL use persistence/managed service appropriate to desired reliability.

Loss of queue data impact SHALL be understood.

---

# 45. Kubernetes

Kubernetes is NOT required for MVP.

It MAY be introduced when:

- multiple backend/worker replicas required,
- enterprise orchestration needed,
- managed cluster already exists.

Do not introduce Kubernetes only for architectural fashion.

---

# 46. Future Kubernetes Objects

If adopted:

```text
Deployment frontend
Deployment backend
Deployment worker
Service frontend
Service backend
Ingress
ConfigMap
Secret
HorizontalPodAutoscaler
CronJob backup/maintenance if appropriate
```

Managed PostgreSQL/object storage are preferred over running stateful infrastructure in-cluster unless intentionally designed.

---

# 47. Release Versioning

Recommended semantic versioning:

```text
MAJOR.MINOR.PATCH
```

Examples:

```text
0.1.0 MVP internal
1.0.0 first production
1.1.0 compatible feature
1.1.1 bug fix
```

---

# 48. Release Notes

Every release SHOULD document:

```text
version
features
fixed issues
database migrations
breaking changes
known limitations
rollback considerations
```

---

# 49. Smoke Tests

After deployment, smoke tests SHALL verify:

```text
health
login
workspace list
basic entity read
database connectivity
object storage access
queue availability where required
```

Production smoke tests SHALL avoid destructive sample mutations unless explicitly isolated.

---

# 50. Rollback Strategy

Application rollback SHALL use previous immutable images.

Database rollback requires caution.

If migration is backward-compatible:

```text
roll back app images
```

may be sufficient.

If schema rollback needed:

- use reviewed Alembic downgrade,
- restore backup if necessary.

Never automatically downgrade production DB without explicit procedure.

---

# 51. Failed Deployment Procedure

If release validation fails:

```text
stop rollout
capture logs
evaluate DB migration state
restore previous app image
run smoke tests
escalate if data migration occurred
```

---

# 52. Maintenance Mode

P1:

Support optional maintenance mode for disruptive operations.

Could return:

```text
503 Service Unavailable
```

with appropriate frontend maintenance page.

---

# 53. Scheduled Jobs

Periodic jobs MAY include:

```text
temporary object cleanup
expired import cleanup
preview cleanup
audit archival policy
backup verification
```

Scheduling mechanism MAY be:

- Celery Beat,
- Kubernetes CronJob,
- platform scheduler.

---

# 54. Temporary Data Cleanup

The platform SHALL define retention for:

```text
failed imports
temporary upload parts
expired previews
quarantine files
```

Cleanup SHALL never remove active document versions.

---

# 55. Production Security Hardening

Before production:

- disable debug mode,
- enforce TLS,
- set secure CORS,
- rotate default credentials,
- restrict network access,
- enforce strong secrets,
- scan images,
- run dependency checks,
- validate file upload limits.

---

# 56. Network Segmentation

Production SHOULD restrict:

```text
PostgreSQL
Redis
MinIO internal endpoints
```

from direct public internet exposure.

Only required frontend/reverse-proxy endpoints should be public.

---

# 57. Database Connection Pool

Backend connection pool SHALL be tuned to deployment replica count.

Avoid:

```text
replicas × oversized pool > DB max connections
```

Pool sizing SHALL be documented per environment.

---

# 58. Resource Limits

Production containers SHOULD define CPU/memory requests/limits or equivalent host constraints.

Worker resource requirements MAY differ from API.

Document conversion workers may require more memory/CPU.

---

# 59. Large Upload Limits

Limits SHALL be coordinated across:

```text
reverse proxy
backend
frontend UX
object storage
```

A proxy limit smaller than backend limit causes inconsistent behavior.

---

# 60. CDN

A CDN MAY serve frontend static assets.

Private enterprise documents SHALL NOT be placed on public CDN without explicit security architecture.

---

# 61. Environment Promotion

Recommended:

```text
development
→ staging
→ production
```

Production SHALL deploy the same tested image digest/artifact used in staging.

Do not rebuild different production code after staging approval.

---

# 62. Infrastructure as Code

P1 recommendation:

Represent production infrastructure through:

```text
Terraform
Pulumi
CloudFormation
or approved equivalent
```

Manual setup SHOULD be minimized.

---

# 63. CI Secret Safety

CI logs SHALL not print protected secrets.

Masked variables SHALL be used.

Pull requests from untrusted forks SHALL not receive production secrets.

---

# 64. Dependency Updates

Dependency update workflow SHOULD include:

```text
automated PR
tests
security scan
review
```

Do not automatically deploy major dependency upgrades to production.

---

# 65. Database Maintenance

Production plan SHOULD include:

```text
VACUUM/autovacuum monitoring
index health
storage growth
slow query review
backup size/growth
```

---

# 66. Object Storage Monitoring

Monitor:

```text
capacity
error rate
latency
failed uploads
failed downloads
replication/backup state
```

---

# 67. Queue Monitoring

Monitor:

```text
queue depth
oldest job age
failed tasks
retry count
worker heartbeat
```

---

# 68. Deployment Acceptance Criteria

A production deployment process is ready when:

- [ ] local Compose environment works,
- [ ] staging exists,
- [ ] production secrets are externalized,
- [ ] TLS configured,
- [ ] migrations automated and reviewed,
- [ ] images are immutable/versioned,
- [ ] health checks implemented,
- [ ] monitoring/logging configured,
- [ ] backups configured,
- [ ] restore tested,
- [ ] smoke tests automated,
- [ ] rollback procedure documented,
- [ ] security review passed,
- [ ] E2E release gate passes.

---

# 69. DevOps Agent Pre-Change Report

Before infrastructure changes:

```text
TASK
ENVIRONMENTS_AFFECTED
FILES_AFFECTED
SERVICE_IMPACT
DATABASE_IMPACT
SECRET_IMPACT
DOWNTIME_RISK
ROLLBACK_PLAN
TEST_PLAN
```

---

# 70. DevOps Agent Completion Report

After change:

```text
SUMMARY
FILES_CHANGED
IMAGES_BUILT
ENVIRONMENT_CHANGES
MIGRATIONS
SECRETS_CHANGED
TESTS_RUN
SMOKE_RESULTS
MONITORING_STATUS
BACKUP_IMPACT
ROLLBACK_STATUS
KNOWN_LIMITATIONS
```

---

# 71. Related Specifications

```text
00_PROJECT_CONTEXT.md
01_ARCHITECTURE_RULES.md
02_SYSTEM_REQUIREMENTS.md
03_DATABASE_SPECIFICATION.md
04_API_SPECIFICATION.md
05_BACKEND_SPECIFICATION.md
06_FRONTEND_SPECIFICATION.md
07_AI_AGENT_ROLES.md
08_TASK_BACKLOG.md
09_TEST_SPECIFICATION.md
11_SECURITY_SPECIFICATION.md
12_CURRENT_STATUS.md
```
