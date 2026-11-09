---
description: "Use when editing dashboard templates, static JavaScript, or CSS under mcchallonge/web/, especially tournament dashboard and underway pages."
applyTo:
  - "mcchallonge/web/templates/**/*.jinja.html"
  - "mcchallonge/web/static/js/**/*.js"
  - "mcchallonge/web/static/css/**/*.css"
---
# Dashboard web change guidance

- Keep server-template and client-script config contracts in sync.
  - If template keys change, update JS consumers in the same commit.
- Preserve endpoint URL generation via server-side helpers (avoid hard-coded API paths when templated values are provided).
- Maintain loopback/admin UX constraints:
  - Admin actions should remain unavailable/non-functional for non-loopback users.

- Prefer targeted validation after web changes:
  - `pytest -q mcchallonge/tests/test_app_endpoints.py`
  - `pytest -q mcchallonge/tests/test_cli.py`

