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

**First authorization** (explicit argument or env var):

```bash
# Explicit argument
rce2sheet build/event_7187.json --oauth-client-secrets client_secret.json --title "..."
```

Or set in `.env` (repo root) to avoid repeating it:

```bash
# Add to .env:
GOOGLE_OAUTH_CLIENT_SECRETS=client_secret.json

# Then run without the flag:
rce2sheet build/event_7187.json --title "..."
```

See `../.env.example` for setup instructions.

**Subsequent runs** (token automatically loaded from keyring):

```bash
rce2sheet build/event_7187.json --title "..."
```

**Advanced options:**

- Force file storage instead of keyring: `RCE2SHEET_TOKEN_BACKEND=file`
- Specify token path: `--oauth-token /path/to/token.json`

### Service Account

Use a service account key JSON:

```bash
rce2sheet build/event_7187.json --credentials service_account.json
```

Or set environment variable in `.env`:

```bash
# Add to .env:
GOOGLE_APPLICATION_CREDENTIALS=path/to/service_account.json

# Then run:
rce2sheet build/event_7187.json
```

## Usage

```bash
rce2sheet build/event_7187.json --oauth-client-secrets client_secret.json --title "RoboRumble 2026"
```

Or with env var (after setting `GOOGLE_OAUTH_CLIENT_SECRETS` in `.env`):

```bash
rce2sheet build/event_7187.json --title "RoboRumble 2026"
```

Or as a module:

```bash
python -m rce2sheet build/event_7187.json --oauth-client-secrets client_secret.json
```
