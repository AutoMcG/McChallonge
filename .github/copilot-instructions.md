# McChallonge agent guidelines

## Scope and repository map

This repository is a Python monorepo with three packages:

- `mcchallonge`: Challonge API integration + Flask dashboard
- `mcrobotcombatevents`: Robot Combat Events scraper
- `rce2sheet`: Google Sheets integration

Most shared workflow and commands are documented in the root [README](../README.md).

## Safe defaults for agent changes

- Make focused, minimal changes; avoid broad refactors unless requested.
- Do not commit or print secrets from `.env` or credential files.
- Prefer package-local edits over cross-package rewrites unless required.
- If behavior is ambiguous, ask before changing public CLI or API contracts.

## High-risk areas and invariants

- Loopback-only admin/cache mutations must remain restricted in `mcchallonge/app.py`.
  - Endpoints that mutate cache should continue to enforce loopback checks.
- Cache payload shape in `mcchallonge/services/local_cache.py` must preserve multi-tournament compatibility.
  - Keep legacy migration behavior (`tournament` -> `tournaments`) intact.
- Dashboard shell/client contract must remain stable.
  - Template config object and client script expectations must stay aligned.

## Validation expectations

Use the smallest targeted test command that covers the change:

- Full default suite: `pytest -q`
- `mcchallonge` focused: `pytest -q mcchallonge/tests`
- `mcrobotcombatevents` focused: `pytest -q mcrobotcombatevents/tests`
- `rce2sheet` focused: `pytest -q rce2sheet/tests`

Integration tests are excluded by default (`-m "not integration"` in [pytest.ini](../pytest.ini)).
Run integration tests only when the task explicitly requires them and credentials are configured.

## Local environment gotchas

- `build/` artifacts are normal; avoid treating generated files as source edits.
- If `.pytest_cache` is permission-locked on local machines, run tests with cache disabled:
  - `pytest -q -p no:cacheprovider`

