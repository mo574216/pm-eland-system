# MVP Demo Walkthrough

This walkthrough uses the phase-level governed-delivery MVP. It intentionally does
not claim final project acceptance, exception/reopening, or non-demo capabilities.

## One-time local persona setup

Use a locally chosen password with at least 12 characters. It is not committed,
printed, or used to overwrite an existing account.

```powershell
$env:DEMO_WORKSPACE_NAME = 'فضای کاری دمو'
$env:DEMO_PASSWORD = '<choose-a-local-demo-password>'
docker compose --env-file .env -f infrastructure/compose/docker-compose.dev.yml exec -T backend python -m scripts.bootstrap_demo_personas
```

The script creates or reuses these non-production users and adds them to the named
workspace: `demo_manager`, `demo_leader`, `demo_reviewer`, and `demo_employer`.
All use the password supplied in `DEMO_PASSWORD`; it is never displayed by the
script. It is disabled in production and rejects an ambiguous workspace name.

## Demonstration sequence

1. Sign in at `http://localhost:5173` as `demo_manager`; open the demo workspace
   and create a phase. In that phase create a deliverable, choosing `demo_leader`
   as owner and internal reviewer.
2. Sign in as `demo_leader`; add a package version, request internal review, mark it
   ready, and formally submit it to `demo_manager` and/or `demo_reviewer`.
3. Sign in as `demo_reviewer` to request a revision, or as `demo_manager` to record
   a project recommendation. Return to `demo_leader` to resubmit if revision was
   requested.
4. As `demo_manager`, record the project recommendation and create the phase
   acceptance package, selecting `demo_employer` by name.
5. Sign in as `demo_employer`; record a conditional acceptance, assign the condition
   and verifier, then demonstrate evidence and verification. Close the conditional
   acceptance once all mandatory conditions are satisfied.

Every hand-off is enforced by server-side workspace membership, assignment,
permission, immutable evidence version, and audit records. Recommendation or
technical sign-off is visibly separate from employer acceptance.
