# ADR-0004 - Bearer Access Tokens and Rotating Refresh Sessions

**Status:** ACCEPTED  
**Date:** 2026-08-22  
**Decision Owners:** Project Architecture  
**Related Files:** `ai_context/04_API_SPECIFICATION.md`, `ai_context/11_SECURITY_SPECIFICATION.md`

## Context

OD-001 requires one consistent browser session strategy. The published API already
requires bearer authentication, while the React client must not persist credentials in
JavaScript-accessible browser storage. Logout, account deactivation, and
credential-compromise response also require revocable long-lived sessions.

## Decision

Protected API requests shall use short-lived JWT bearer access tokens. The frontend shall
hold access tokens only in process memory. A cryptographically random opaque refresh token
shall be stored in a `Secure`, `HttpOnly`, `SameSite=Strict` cookie and represented in the
database only by its SHA-256 digest.

Refresh tokens shall rotate on every successful refresh. Reuse of an already rotated token
shall revoke its complete token family. Sessions shall have configurable idle and absolute
expiration and shall be revoked on logout and relevant security events.

Access JWTs shall use an explicit algorithm allowlist and contain only `sub`, `jti`, `iss`,
`aud`, `iat`, and `exp`. Roles, permissions, workspace identifiers, personal data, and
secrets shall not be embedded. Effective authorization shall be resolved server-side.

The API shall provide `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, and
`GET /auth/me`. Cookie-bearing refresh requests shall validate their origin. Tokens and
passwords shall never be logged or written to audit state.

## Alternatives Considered

Long-lived bearer tokens were rejected because exposure lasts too long and revocation is
delayed. Browser web storage was rejected because application-origin JavaScript can read
it. Stateless refresh JWTs were rejected because reliable revocation and reuse detection
require server-side state. Cookie authentication for every API request was rejected because
it conflicts with the bearer contract and expands the CSRF surface.

## Consequences

The frontend must restore sessions through the refresh endpoint after reload and keep the
returned access token in memory. The backend must persist refresh sessions, rotate tokens
atomically, validate JWT issuer/audience/algorithm/expiry, and resolve current roles and
permissions from PostgreSQL.

## Migration Impact

Add an `auth_sessions` table through Alembic. Expand the API specification and OpenAPI
contract with the refresh operation and refresh-cookie behavior.

## Security Impact

Refresh-token theft is limited by HttpOnly cookie storage, bounded expiry, rotation, reuse
detection, and family revocation. XSS can still act while a page is compromised, so CSP,
output encoding, dependency hygiene, and short access-token lifetimes remain necessary.
Cookie-bearing refresh requests require origin validation and TLS outside local development.

## Related Requirements

```text
AUTH-FR-001
AUTH-FR-002
AUTH-FR-003
SEC-AUTH-001 through SEC-AUTH-006
```

## Supersedes / Superseded By

Supersedes: OD-001  
Superseded by: None
