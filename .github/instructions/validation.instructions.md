---
description: "Use when deciding how to validate changes in this monorepo, including targeted pytest selection, integration-test handling, and docs-only change expectations."
---
# Validation matrix for agent changes

Choose the smallest command that fully covers touched behavior.

## Fast selectors

- `pytest -q mcchallonge/tests`
- `pytest -q mcrobotcombatevents/tests`
- `pytest -q rce2sheet/tests`
- `pytest -q` (full default suite)

## By change type

- `mcchallonge/app.py`, templates, static JS/CSS:
  - `pytest -q mcchallonge/tests/test_app_endpoints.py mcchallonge/tests/test_cli.py`
- `mcchallonge/services/*`:
  - `pytest -q mcchallonge/tests`
- `mcrobotcombatevents/src/*`:
  - `pytest -q mcrobotcombatevents/tests`
- `rce2sheet/src/*`:
  - `pytest -q rce2sheet/tests`
- Cross-package behavior or dependency updates:
  - `pytest -q`

## Integration tests

- Integration tests are intentionally deselected by default.
- Run `-m integration` only when the task requires live integration behavior and credentials are available.

