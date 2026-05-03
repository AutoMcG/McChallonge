# rce2sheet

Independent package that reads an `mcrobotcombatevents` JSON export and creates a
Google Sheet with one sheet per competition, one row per bot, and Yes/No dropdown
columns for Passed Weight, Passed Safety, and Paid.

## Install

```bash
pip install -e .
```

## Authentication

Supports both auth modes:

- User OAuth (recommended for "the logged-in user" behavior)
- Service account credentials

### User OAuth

Use an OAuth client secrets JSON (Desktop app) to sign in interactively. The first run
opens a browser and stores a refreshable token in your OS keyring by default
(Windows Credential Manager on Windows).

If keyring is unavailable, rce2sheet falls back to the `--oauth-token` file path.
You can force file storage by setting `RCE2SHEET_TOKEN_BACKEND=file`.

```bash
rce2sheet build/event_7187.json --oauth-client-secrets client_secret.json --oauth-token token.json
```

### Service Account

Use a service account key JSON:

```bash
rce2sheet build/event_7187.json --credentials service_account.json
```

Or set environment variable:

```bash
set GOOGLE_APPLICATION_CREDENTIALS=service_account.json
```

## Usage

```bash
rce2sheet build/event_7187.json --oauth-client-secrets client_secret.json --title "RoboRumble 2026"
```

Or as a module:

```bash
python -m rce2sheet build/event_7187.json --oauth-client-secrets client_secret.json
```
