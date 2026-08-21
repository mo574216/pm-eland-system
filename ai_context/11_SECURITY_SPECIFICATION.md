# Security Specification

**File:** `11_SECURITY_SPECIFICATION.md`  
**Status:** Normative  
**System:** Metadata-Driven Enterprise Architecture Management Platform  
**Version:** 1.0  
**Audience:** Security engineers, backend/frontend engineers, DevOps engineers, AI coding agents, QA engineers, reviewers

---

# 1. Purpose

This document defines mandatory security requirements for the platform.

Security controls SHALL protect:

- user identities,
- enterprise architecture data,
- workspace boundaries,
- structured metadata and forms,
- imported Excel/CSV content,
- document binaries,
- document versions,
- review comments,
- audit history,
- background jobs,
- secrets and infrastructure credentials.

The platform SHALL follow:

> **Fail closed, least privilege, defense in depth, and server-side enforcement.**

---

# 2. Normative References

Security implementation SHALL conform to:

```text
01_ARCHITECTURE_RULES.md
02_SYSTEM_REQUIREMENTS.md
03_DATABASE_SPECIFICATION.md
04_API_SPECIFICATION.md
05_BACKEND_SPECIFICATION.md
06_FRONTEND_SPECIFICATION.md
09_TEST_SPECIFICATION.md
10_DEPLOYMENT_GUIDE.md
```

Security requirements override implementation convenience.

---

# 3. Security Objectives

The system SHALL protect:

## Confidentiality

Prevent unauthorized access to:

- workspaces,
- entities,
- forms,
- documents,
- dashboards,
- audit data,
- secrets.

## Integrity

Prevent unauthorized or silent modification of:

- entity data,
- metadata definitions,
- imports,
- document versions,
- phase lock state,
- permissions,
- audit history.

## Availability

Reduce risk of service disruption caused by:

- malformed input,
- large uploads,
- abusive imports,
- runaway jobs,
- dependency outages.

## Accountability

Ensure material user actions are attributable through immutable audit records.

---

# 4. Threat Model

Primary threat categories include:

```text
credential theft
broken authentication
broken object-level authorization
cross-workspace data leakage
privilege escalation
SQL injection
XSS
CSRF where cookie auth is used
malicious file upload
MIME confusion
path traversal
malware
import-based data corruption
mass assignment
unsafe deserialization
secret leakage
dependency vulnerabilities
audit tampering
denial of service
background job abuse
presigned URL abuse
```

AI-related threats are future P2 scope, including:

```text
prompt injection
data exfiltration through LLM tools
unauthorized retrieval
model-provider privacy leakage
```

---

# 5. Security Classification

Recommended internal classification:

```text
PUBLIC
INTERNAL
CONFIDENTIAL
RESTRICTED
```

Most workspace content SHOULD be treated as at least:

```text
INTERNAL
```

Sensitive enterprise architecture projects MAY be:

```text
CONFIDENTIAL
```

Security classification MAY later become configurable metadata.

---

# 6. Authentication Security

# SEC-AUTH-001 — Password Storage

Passwords SHALL:

- never be stored plaintext,
- never be reversibly encrypted,
- use a modern password hashing function.

Recommended:

```text
Argon2id
```

Acceptable alternative:

```text
bcrypt
```

with appropriate work factor.

---

# SEC-AUTH-002 — Credential Verification

Credential comparison SHALL use vetted library functions.

Agents SHALL NOT implement custom cryptographic password logic.

---

# SEC-AUTH-003 — Login Error Messages

Invalid credentials SHALL return a generic error.

Do not distinguish publicly between:

```text
username does not exist
password incorrect
```

---

# SEC-AUTH-004 — Rate Limiting

Login endpoint SHOULD be rate-limited.

Recommended controls:

- per IP,
- per account identifier,
- exponential backoff or temporary throttling.

---

# SEC-AUTH-005 — Account Status

Inactive/suspended accounts SHALL not authenticate.

---

# SEC-AUTH-006 — Last Login / Failed Login

Authentication system SHOULD track:

- `last_login_at`,
- failed login count,
- security-relevant login events.

---

# 7. Token / Session Security

The final session architecture SHALL be implemented consistently.

Two supported approaches:

## Option A — Short-Lived Bearer Access Token

- access token short-lived,
- refresh mechanism protected,
- token not permanently stored in insecure browser storage.

## Option B — Secure HTTP-Only Cookies

If cookies are used:

```text
HttpOnly
Secure
SameSite
```

must be configured appropriately.

CSRF protection SHALL be implemented for state-changing requests if SameSite policy alone is insufficient.

---

# 8. JWT Security

If JWT is used:

- strong signing secret or asymmetric key,
- short access-token lifetime,
- validate issuer if configured,
- validate audience if configured,
- validate expiration,
- reject algorithm confusion,
- do not accept `alg=none`.

JWT SHALL contain minimal claims.

Sensitive workspace data SHALL not be embedded in tokens.

---

# 9. Refresh Tokens

If implemented, refresh tokens SHALL:

- have longer but bounded expiration,
- be revocable,
- rotate where practical,
- be stored securely,
- be invalidated on logout/security events where appropriate.

---

# 10. Authorization Model

Authorization SHALL combine:

```text
authentication
+ permission
+ workspace membership
+ object scope
+ lock state
```

No single role label is sufficient.

---

# 11. RBAC

Initial roles MAY include:

```text
SYSTEM_ADMIN
PROJECT_MANAGER
ANALYST
VIEWER
```

Permissions SHALL be explicit and stable.

Examples:

```text
WORKSPACE_CREATE
WORKSPACE_MANAGE
ENTITY_CREATE
ENTITY_READ
ENTITY_UPDATE
ENTITY_ARCHIVE
METADATA_MANAGE
FORM_DESIGN
FORM_SUBMIT
DOCUMENT_UPLOAD
DOCUMENT_READ
IMPORT_EXECUTE
PHASE_LOCK
PHASE_UNLOCK
AUDIT_READ
```

---

# 12. Server-Side Authorization

Every protected API SHALL enforce authorization server-side.

Frontend guards are informational/UX controls only.

This is prohibited:

```text
if button hidden => resource secure
```

---

# 13. Object-Level Authorization

For each resource request, backend SHALL verify:

- caller may access workspace,
- resource belongs to accessible workspace,
- required action permitted,
- lock policy permits mutation.

A valid UUID is not proof of authorization.

---

# 14. Workspace Isolation

Workspace isolation is a critical security boundary.

Every workspace-owned query SHALL filter or validate:

```text
workspace_id
```

The system SHALL prevent:

```text
User in Workspace A → Entity in Workspace B
User in Workspace A → Document in Workspace B
User in Workspace A → Import Job in Workspace B
```

---

# 15. Resource Existence Leakage

For resources outside caller scope, API MAY return:

```text
404
```

instead of 403 when needed to avoid leaking resource existence.

The behavior SHALL be consistent.

---

# 16. Privilege Escalation Protection

Users SHALL NOT be able to:

- assign themselves higher roles,
- add themselves to unauthorized workspaces,
- grant permissions they do not possess authority to manage,
- unlock phases without explicit permission.

Role/permission changes SHALL be audited.

---

# 17. Mass Assignment Protection

API update schemas SHALL explicitly whitelist mutable fields.

Clients SHALL NOT be able to set protected properties such as:

```text
created_by
locked_by
workspace_id
owner_id
is_system
password_hash
audit fields
```

unless endpoint explicitly authorizes that operation.

---

# 18. Input Validation

All request data SHALL be validated server-side.

Validation categories include:

- types,
- lengths,
- allowed enum values,
- UUID format,
- metadata structure,
- import mappings,
- relationship constraints,
- filenames,
- MIME types.

Malformed requests SHALL fail safely.

---

# 19. SQL Injection Protection

Backend SHALL use SQLAlchemy parameter binding or equivalent prepared statements.

Prohibited:

```python
sql = "SELECT ... WHERE name = '" + user_input + "'"
```

Dynamic reporting/filtering SHALL whitelist columns/operators.

User-supplied SQL is prohibited.

---

# 20. XSS Protection

Frontend SHALL escape untrusted text by default.

Rich-text rendering SHALL be sanitized with a vetted sanitizer.

Imported Excel values, comments, metadata labels, filenames, and entity names SHALL all be treated as untrusted content.

---

# 21. CSP

Production SHOULD define a Content Security Policy.

Recommended starting posture:

```text
default-src 'self'
object-src 'none'
frame-ancestors 'self'
```

Exact policy SHALL account for:

- document preview,
- CDN,
- API origin,
- analytics if any.

Unsafe inline/eval allowances SHOULD be avoided.

---

# 22. Clickjacking

Use:

```text
Content-Security-Policy: frame-ancestors ...
```

and/or:

```text
X-Frame-Options
```

as appropriate.

---

# 23. MIME Sniffing

Responses SHOULD include:

```text
X-Content-Type-Options: nosniff
```

---

# 24. CORS

Production CORS SHALL use explicit trusted origins.

Prohibited:

```text
Access-Control-Allow-Origin: *
```

with authenticated credential flow.

---

# 25. CSRF

If authentication uses cookies for state-changing requests, CSRF controls SHALL be enabled.

Possible controls:

- SameSite cookies,
- CSRF tokens,
- origin checking.

---

# 26. File Upload Threat Model

Uploaded files SHALL be assumed hostile.

Threats include:

```text
malware
polyglot files
MIME mismatch
oversized files
zip bombs
path traversal names
malicious macros
script-bearing SVG
malformed Office/PDF files
```

---

# 27. File Size Limits

Maximum upload size SHALL be configured consistently across:

- reverse proxy,
- backend,
- frontend UX.

Server-side limit is authoritative.

---

# 28. Filename Security

Original filename SHALL be treated as metadata only.

Storage object keys SHALL be server-generated.

Prohibited:

```text
../../uploads/file.docx
```

from user-provided filename.

---

# 29. Extension Validation

Allowed extensions SHALL be configured centrally.

Extension checks alone are insufficient.

---

# 30. MIME Validation

Backend SHALL compare:

- declared MIME,
- inferred/file-signature MIME where practical,
- allowed type policy.

Mismatches SHALL be rejected or quarantined.

---

# 31. Malware Scanning

Production P1 requirement:

Uploaded binaries SHOULD be scanned using an approved malware scanner.

Possible implementation:

```text
ClamAV
managed malware scanning service
```

Scan states:

```text
PENDING
CLEAN
INFECTED
FAILED
```

---

# 32. Quarantine

Files pending scan SHOULD be stored or treated as quarantined.

Normal download/preview SHOULD be blocked until policy allows access.

---

# 33. SVG Security

SVG may contain active content.

If SVG preview is supported:

- sanitize,
- rasterize,
- or serve with safe content policy.

Raw untrusted SVG SHALL not be embedded blindly.

---

# 34. Office File Security

DOCX/XLSX/PPTX may contain macros or embedded content.

The system SHALL not execute macros.

Preview conversion SHALL occur in an isolated worker environment.

---

# 35. PDF Security

PDF previews SHALL not rely on unsafe server-side execution.

Use browser PDF viewers or isolated conversion libraries.

---

# 36. Object Storage Security

Buckets SHALL be private.

Permanent public access is prohibited.

---

# 37. Presigned URLs

Presigned URLs SHALL:

- be short-lived,
- be generated only after authorization,
- scope to exact object/action,
- avoid excessive validity windows.

Recommended default:

```text
5–15 minutes
```

depending on deployment needs.

---

# 38. Direct-to-S3 Upload

Direct browser upload MAY be used only if:

- backend first authorizes request,
- backend generates scoped short-lived presigned upload,
- file metadata/size policy enforced,
- completion is verified server-side,
- scan workflow still applies.

Permanent client storage credentials are prohibited.

---

# 39. Import Security

Excel/CSV import SHALL treat all imported content as untrusted.

The import system SHALL protect against:

- formula injection,
- malicious strings,
- oversized workbooks,
- malformed XML,
- unsafe external links,
- accidental cross-workspace references,
- destructive overwrite.

---

# 40. Spreadsheet Formula Injection

When exporting data to CSV/XLSX, cells beginning with:

```text
=
+
-
@
```

MAY need neutralization depending on export behavior.

Imported formulas SHALL not be executed by the backend.

---

# 41. XLSX Parser Security

Parser configuration SHALL avoid unsafe XML entity processing.

Dependencies SHALL be patched against known archive/XML vulnerabilities.

---

# 42. Import Overwrite Protection

The platform SHALL never silently overwrite existing canonical records.

Required:

```text
dry run
diff
conflict detection
explicit MERGE/REPLACE/SKIP
```

---

# 43. Import Authorization

Import job, profile, mapping, and commit SHALL all verify workspace access.

A user SHALL not import into a workspace using another workspace's import profile.

---

# 44. Import Idempotency

Commit SHALL prevent duplicate side effects on retry.

Repeated commit of same completed job SHALL not create duplicates.

---

# 45. Hierarchy Security

Reparent operations SHALL verify:

- source access,
- target parent access,
- same workspace,
- no cycle,
- lock state.

---

# 46. Relationship Security

Relationship creation SHALL verify both source and target entities are authorized.

Do not leak target names/types from inaccessible workspaces.

---

# 47. Metadata Administration Security

Creating/changing entity types and attributes is privileged.

`METADATA_MANAGE` SHALL be required.

Changes SHALL be audited.

---

# 48. Form Designer Security

Form design/publish SHALL require:

```text
FORM_DESIGN
```

Published forms SHALL be immutable.

This prevents silent reinterpretation of historical submissions.

---

# 49. Phase Lock Security

Only explicitly permitted users SHALL lock/unlock phases.

Unlock is especially sensitive and SHALL be audited.

---

# 50. Audit Security

Audit records SHALL be append-only.

Normal APIs SHALL not allow:

```text
UPDATE audit_logs
DELETE audit_logs
```

---

# 51. Audit Content

Audit records SHOULD include:

```text
request_id
user_id
workspace_id
action
resource_type
resource_id
before_state
after_state
client_ip
user_agent
timestamp
```

---

# 52. Audit Redaction

Audit SHALL NOT store:

```text
passwords
access tokens
refresh tokens
JWT secrets
S3 secret keys
database passwords
```

Sensitive personal fields MAY require redaction policy if introduced.

---

# 53. Audit Availability

Audit failure policy SHALL be explicit.

For critical mutations such as:

- permission changes,
- phase unlock,
- imports,

failure to record required audit SHOULD fail the transaction.

---

# 54. Logging Security

Application logs SHALL not contain secrets.

Redact:

```text
Authorization header
cookies
password fields
tokens
secret config
raw credentials
```

---

# 55. PII / Sensitive Data

The initial system is not designed specifically for highly regulated personal data.

If sensitive personal data is introduced, additional requirements MAY include:

- field-level access,
- retention,
- encryption,
- masking,
- data residency,
- legal compliance review.

---

# 56. Encryption in Transit

Production SHALL use TLS for:

- browser ↔ reverse proxy,
- backend ↔ managed database where supported,
- backend ↔ object storage where supported.

---

# 57. Encryption at Rest

Production SHOULD use encryption at rest for:

- PostgreSQL storage,
- object storage,
- backups,
- secret store.

Implementation depends on hosting environment.

---

# 58. Secret Management

Secrets SHALL be supplied via:

```text
secret manager
protected CI/CD variables
Kubernetes Secret with controls
Vault
```

Never commit real secrets.

---

# 59. Secret Rotation

Production secrets SHOULD be rotatable.

High-value secrets:

```text
JWT signing key
DB password
S3 credentials
API keys
```

Rotation procedure SHALL avoid prolonged downtime where practical.

---

# 60. Default Credentials

Default credentials SHALL not exist in production.

Initial admin bootstrapping SHALL require secure explicit setup.

---

# 61. Dependency Security

CI SHOULD scan:

```text
Python packages
npm packages
container images
OS packages
```

Known critical vulnerabilities SHALL block release unless explicitly risk-accepted.

---

# 62. Dependency Pinning

Production dependencies SHOULD be version-pinned or lockfile-controlled.

Use:

```text
poetry.lock / uv.lock / requirements lock
package-lock.json / pnpm-lock.yaml
```

depending on chosen package manager.

---

# 63. Container Security

Production containers SHOULD:

- run as non-root,
- use minimal base images,
- avoid shell/tooling not needed at runtime,
- have read-only filesystem where practical,
- define resource limits.

---

# 64. Network Security

Public access SHOULD be limited to:

```text
reverse proxy / frontend
API
```

PostgreSQL, Redis, and MinIO internal endpoints SHALL not be exposed publicly.

---

# 65. Database Least Privilege

Application DB role SHALL not have:

```text
CREATE DATABASE
ALTER ROLE
SUPERUSER
```

Schema migration role SHALL be separate where practical.

---

# 66. Redis Security

Redis SHALL:

- not be public,
- use authentication/TLS when deployment supports it,
- avoid storing permanent secrets.

---

# 67. Background Job Security

Workers SHALL validate job payloads and authorization assumptions.

Do not trust a queued payload merely because it originated internally.

Jobs SHOULD pass resource IDs and re-resolve current state.

---

# 68. Job Abuse Prevention

Expensive operations SHOULD be rate-limited or permission-controlled.

Examples:

```text
large import
document conversion
future AI query
bulk export
```

---

# 69. Denial-of-Service Controls

Controls MAY include:

- upload size limits,
- request body limits,
- API rate limiting,
- pagination limits,
- job quotas,
- worker concurrency limits,
- query timeout limits.

---

# 70. Query Safety

Dynamic filters/reports SHALL use:

- whitelisted fields,
- whitelisted operators,
- bounded result sizes.

Arbitrary SQL from browser is prohibited.

---

# 71. Error Message Security

Client-facing errors SHALL not reveal:

```text
stack traces
SQL text
filesystem paths
secret values
internal hostnames
```

Detailed errors belong in protected logs.

---

# 72. Security Headers

Production SHOULD configure:

```text
Strict-Transport-Security
Content-Security-Policy
X-Content-Type-Options
Referrer-Policy
Permissions-Policy
```

Where compatible.

---

# 73. Session Termination

Administrative capability SHOULD exist to revoke sessions/tokens for:

- disabled user,
- credential compromise,
- role changes where required.

---

# 74. Account Recovery

If password reset is implemented later:

- use single-use expiring tokens,
- avoid account enumeration,
- invalidate/reset securely,
- audit security-relevant events.

---

# 75. Administrative Actions

High-impact actions SHOULD be separately permissioned:

```text
user role change
workspace membership change
metadata publication
phase unlock
audit access
bulk import
```

---

# 76. Security Event Audit

Recommended events:

```text
LOGIN_SUCCESS
LOGIN_FAILURE
LOGOUT
ROLE_CHANGED
WORKSPACE_MEMBER_ADDED
WORKSPACE_MEMBER_REMOVED
PHASE_LOCKED
PHASE_UNLOCKED
IMPORT_COMMITTED
DOCUMENT_VERSION_CREATED
FORM_PUBLISHED
METADATA_CHANGED
```

---

# 77. Security Monitoring

Production SHOULD monitor for:

```text
repeated login failures
repeated 403 responses
unusual download volume
import failures
malware detections
excessive job creation
unexpected admin changes
```

---

# 78. Security Test Requirements

Security test suite SHALL cover at minimum:

```text
BOLA / IDOR
workspace isolation
privilege escalation
SQL injection
XSS
CORS
file upload attacks
MIME mismatch
path traversal
formula injection
presigned URL authorization
audit tamper attempts
secret exposure
```

See `09_TEST_SPECIFICATION.md`.

---

# 79. OWASP Alignment

Security review SHOULD consider:

```text
OWASP Top 10
OWASP API Security Top 10
OWASP ASVS principles
```

The project does not need formal certification unless required, but controls SHOULD align with these standards.

---

# 80. Security Severity

Suggested severity model:

```text
Critical — direct data breach, auth bypass, destructive corruption
High — serious privilege escalation, major integrity risk
Medium — exploitable issue with limited impact
Low — defense-in-depth weakness
```

---

# 81. Release Security Gate

Production release SHALL be blocked by unresolved:

```text
Critical
High authentication
High authorization
High cross-workspace leakage
High data-integrity
```

findings unless explicitly risk-accepted by authorized project owner.

---

# 82. Security Review Triggers

Mandatory security review when changing:

```text
authentication
authorization
workspace scope
file upload
presigned URLs
import commit
secret handling
external integrations
AI provider integration
```

---

# 83. Security Agent Pre-Review Checklist

```text
TASK
THREAT SURFACE
AUTHENTICATION_IMPACT
AUTHORIZATION_IMPACT
DATA_CONFIDENTIALITY
DATA_INTEGRITY
FILE/IMPORT_RISK
SECRETS
LOGGING/AUDIT
DEPENDENCY_IMPACT
```

---

# 84. Security Agent Completion Report

```text
REVIEW_SCOPE
THREATS_REVIEWED
FINDINGS
SEVERITY
REPRODUCTION
RECOMMENDATIONS
BLOCKING_FINDINGS
RESIDUAL_RISK
RELEASE_RECOMMENDATION
```

---

# 85. Secure Coding Rules for AI Agents

AI coding agents SHALL NOT:

- weaken permission checks to fix failing tests,
- disable TLS/security headers for production convenience,
- hard-code secrets,
- expose S3 credentials,
- bypass malware/file checks,
- remove audit calls,
- trust client-supplied workspace ownership,
- use `eval` for form rules,
- concatenate SQL,
- silently ignore security exceptions.

---

# 86. Security Exception Procedure

If a security rule must be temporarily deviated from:

1. document rationale,
2. define risk,
3. define compensating control,
4. assign expiry/remediation date,
5. obtain explicit approval.

Temporary security exceptions SHALL not become undocumented permanent design.

---

# 87. Future AI Security Requirements

Before runtime AI features are enabled, create an ADR/security design covering:

- provider/data residency,
- prompt injection,
- document exfiltration,
- workspace-aware retrieval,
- model logging,
- prompt/version audit,
- user approval for write actions,
- token/cost controls.

AI SHALL not receive unrestricted database access.

---

# 88. Definition of Security Compliance

A feature is security-compliant when:

- [ ] authentication requirement is correct,
- [ ] authorization enforced server-side,
- [ ] workspace isolation tested,
- [ ] input validated,
- [ ] output safely encoded,
- [ ] no secrets exposed,
- [ ] audit added where required,
- [ ] file/import risks addressed,
- [ ] error messages safe,
- [ ] tests include negative security cases,
- [ ] no unresolved critical/high finding exists.

---

# 89. Related Specifications

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
10_DEPLOYMENT_GUIDE.md
12_CURRENT_STATUS.md
```
