---
description: "Use when editing tournament cache load/save/refresh logic, cache schema migration, underway state mutation, or local cache file behavior in mcchallonge/services/local_cache.py."
applyTo: "mcchallonge/services/local_cache.py"
---
# Local cache invariants

- Preserve cache compatibility:
  - Existing single-tournament payloads with `tournament` must still migrate to `tournaments`.
  - Multi-tournament payload shape must remain stable for dashboard client rendering.

- Preserve explicit failure behavior:
  - Missing cache file should raise/return actionable guidance (not silent defaults).
  - Tournament/match lookup failures should stay explicit and user-readable.

- Preserve global underway exclusivity behavior in cache mutation flows unless intentionally changing product behavior.

- Validate cache changes with:
  - `pytest -q mcchallonge/tests/test_app_endpoints.py`
  - `pytest -q mcchallonge/tests/test_cli.py mcchallonge/tests/test_data_mocks.py`

