# ADR-0005: RTL Portal Experience

**Status:** Accepted
**Date:** 2026-08-23

## Context

The Persian/RTL foundation established direction, localization, and component
behavior, but the initial authenticated frontend remained a development shell.
It did not communicate the intended product as a mature project knowledge
portal: workspace context was weak, navigation was route-specific, and there
was no useful landing page.

The approved visual direction is a Persian portal with a persistent right-side
navigation area, a contextual header, clear workspace identity, quick access to
available services, card-based content, and deliberate loading and empty states.
The direction is structural and experiential; organization-specific logos,
names, illustrations, and unimplemented modules from visual references are not
product requirements.

## Decision

Authenticated workspace routes SHALL use one reusable portal shell with:

- a persistent right-side navigation drawer at desktop widths and a temporary
  drawer on smaller screens;
- a compact product identity, workspace context, user controls, and responsive
  menu control;
- a workspace landing route at `/workspaces/:workspaceId`;
- generic navigation descriptors for implemented platform capabilities;
- a card-based dashboard that exposes only implemented routes as actions;
- explicit roadmap labels for unavailable capabilities, without dead links;
- shared tokens for color, typography, spacing, radius, elevation, and focus;
- subtle code-native background decoration that does not obscure content;
- Persian localized copy and correct RTL interaction/focus behavior.

The shell SHALL remain domain-agnostic. Navigation items describe platform
engines such as entities and metadata, never configurable business concepts.
Authorization remains authoritative on the backend; frontend visibility is only
a usability aid. Workspace identifiers continue to come from the current route
and authenticated API data.

The reference appearance is not copied pixel-for-pixel. Product branding uses
generic repository-owned marks and tokens until approved brand assets are
provided.

## Alternatives Considered

- Keep the minimal top bar until reporting work: rejected because it delays
  product coherence and makes each new frontend module converge independently.
- Implement reference modules as placeholders with working-looking controls:
  rejected because it would misrepresent unavailable behavior.
- Build separate shells for administration and daily work: deferred because the
  MVP benefits from one consistent, permission-aware navigation model.

## Consequences

- New workspace modules register a navigation descriptor instead of creating a
  new application frame.
- Dashboard cards and navigation can grow with the backlog without redesigning
  the shell.
- Visual regression, responsive navigation, Persian copy, and route highlighting
  become frontend acceptance concerns.
- A future approved brand package can replace the generic mark and palette
  without changing route or component architecture.

## Migration Impact

No database or API migration is required. Existing workspace routes move inside
the new shell, and workspace entry actions target the dashboard route instead of
the entity tree directly.

## Security Impact

The shell does not grant access. Protected routes, API authorization, active
membership, permissions, and workspace isolation remain authoritative. The UI
must not expose cross-workspace cached data while route context changes.

## Related Requirements

- `FE-RULE-001` through `FE-RULE-004`
- Frontend Specification sections 6, 7, 11, 49, and 50
- `FND-007`
- `UX-FE-001`

## Supersedes / Superseded By

Supersedes the visual composition of the initial minimal application shell.
The shell composition remains accepted. Its project-versus-administration
information architecture and contextual-capability navigation are refined by
ADR-0007; in particular, operational import no longer belongs in normal top-level
project navigation.
