---
description: "Use when editing mcchallonge Flask routes, endpoint behavior, cache APIs, loopback/admin restrictions, or dashboard page wiring in mcchallonge/app.py."
applyTo: "mcchallonge/app.py"
---
# mcchallonge app route guardrails

- Keep cache-mutating endpoints loopback-restricted.
  - `/api/cache/update`
  - `/api/cache/clear`
  - `/api/cache/match/underway`
  - `/api/cache/match/underway/clear`
- Preserve the `403` behavior for non-loopback callers.
- Preserve actionable error messages for missing local cache file.

- Keep client-rendered dashboard route behavior aligned:
  - `/index.html`, `/participants`, `/matches`, `/queue`, `/underway`
  - `tournament_dashboard.jinja.html` config object must stay compatible with client JS.

- If route behavior changes, validate with:
  - `pytest -q mcchallonge/tests/test_app_endpoints.py`
  - Add/adjust endpoint tests in the same change set when semantics change.

