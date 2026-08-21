# ADR-0003: Persian-First Localization Boundary

**Status:** Accepted  
**Date:** 2026-08-22

## Context

The MVP is intended for Persian-speaking end users. The existing frontend
foundation was created in English and left-to-right direction, while public API
error messages and search behavior did not define a Persian localization policy.
Treating this as label replacement would leave layout, accessibility, component
locales, search equivalence, and future maintainability inconsistent.

## Decision

The application SHALL be Persian-first with locale `fa-IR` and global RTL
direction.

Developer-facing contracts remain English: source identifiers, routes, API field
names, enum values, permission names, stable error codes, database identifiers,
logs, and developer documentation. End-user platform copy and safe API error
messages are Persian. User-authored and metadata-configured values may contain
Persian Unicode and are not translation keys.

The React frontend SHALL use an i18n resource layer even while Persian is the
only mandatory locale. MUI SHALL use its Persian locale, RTL theme direction,
and the supported Emotion RTL transformation. A Persian-capable font SHALL be
bundled with the application.

The backend SHALL separate stable error codes from localized public messages.
Persian search SHALL use a shared normalization utility without changing the
canonical stored display value.

API timestamps remain ISO 8601 and numeric values remain JSON numbers. The exact
user-facing calendar and digit policy remains an explicit product decision and
must be consumed through centralized formatting helpers once resolved.

## Consequences

- Every new end-user string requires a Persian translation resource entry.
- RTL and untranslated-copy checks become part of the frontend regression gate.
- Search implementations must normalize both indexed content and queries using
  the same policy.
- Adding English UI later does not require changing API or database identifiers.
- Date/number-heavy UI cannot choose an independent calendar or numeral policy.

## Alternatives Rejected

- Hard-coded Persian strings in components: rejected because it prevents a
  maintainable localization boundary.
- Translating API field names or database identifiers: rejected because it makes
  developer contracts unstable and locale-dependent.
- Deferring RTL until later: rejected because direction affects the design-system
  foundation and component behavior.

## Migration Impact

No database migration is required by this decision. The existing frontend shell
must migrate its copy, document attributes, theme, style cache, locale, and font.
Existing public error messages must migrate to the centralized Persian catalog.
Future normalized search columns or indexes require their own Alembic migration.

## Security Impact

Persian and other Unicode text remains untrusted input. Existing escaping,
sanitization, CSP, authorization, and validation rules remain mandatory. Stable
English error codes support safe client branching without exposing diagnostics.

## Related Requirements

- `I18N-FR-001` through `I18N-FR-006`
- `TEST-I18N-001` through `TEST-I18N-005`
- `FND-007`

## Supersedes / Superseded By

Supersedes the former frontend statement that the MVP may be English-only and
that RTL may be deferred. Superseded by: none.
