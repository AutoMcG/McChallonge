# McChallonge

A monorepo of tools for running robot combat events end-to-end — from scraping event
registrations through check-in tracking, bracket population, and a live match dashboard.

## Packages

| Package | Purpose |
|---|---|
| `mcrobotcombatevents` | Scrapes a Robot Combat Events page into a structured JSON file |
| `rce2sheet` | Turns that JSON into a Google Sheet for check-in tracking |
| `mcchallonge` | Reads the approved list from the sheet, populates Challonge brackets, and serves a match dashboard |

---

## Event Day Workflow

### Step 1 — Export event data from Robot Combat Events

Scrape a Robot Combat Events page into a local JSON file using the event ID from the URL.

```bash
python -m mcrobotcombatevents 12345 -o build/event_12345.json
```

Or using the installed console script:

```bash
rce-export 12345 -o build/event_12345.json
```

This produces a file containing each competition and its registered bots.

---

### Step 2 — Create the check-in Google Sheet

Turn the event JSON into a Google Sheet. One tab is created per competition. Each row is
a registered bot with Yes/No dropdowns for **Passed Weight**, **Passed Safety**, and **Paid**.

**Option A: Explicit argument (first time)**

```bash
rce2sheet build/event_12345.json \
    --oauth-client-secrets client_secret.json \
    --title "RoboRumble 2026"
```

**Option B: Set in `.env` (for convenience)**

Add to the repo-root `.env`:

```text
GOOGLE_OAUTH_CLIENT_SECRETS=path/to/client_secret.json
```

Then on any machine with that `.env`, use the simpler form:

```bash
rce2sheet build/event_12345.json --title "RoboRumble 2026"
```

**Subsequent runs (any approach)**

After first authorization, the token is stored in your OS keyring.
Subsequent runs need no auth flags at all:

```bash
rce2sheet build/event_12345.json --title "RoboRumble 2026"
```

---

**Note:** On first run, a browser window opens for Google sign-in. The resulting token is stored
securely in your OS keyring (Windows Credential Manager on Windows).
To override to file storage: `RCE2SHEET_TOKEN_BACKEND=file`

---

### Step 3 — Check-in: organizers update the sheet

Event organizers open the spreadsheet and update the dropdown columns for each bot as
teams complete weight check, safety inspection, and registration payment. No tooling is
needed for this step — it is a direct Google Sheets edit.

---

### Step 4 — Export approved participants

Once check-in is complete, read the sheet and export a JSON list of bots that passed all
three checks.

If a token is already stored in keyring from a previous `rce2sheet` run, no auth flags
are needed:

```bash
rce2sheet-read "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OlCBKDMds" \
    -o approved_participants.json
```

First time on a new machine (browser opens for authorization):

```bash
rce2sheet-read "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OlCBKDMds" \
    --oauth-client-secrets client_secret.json \
    -o approved_participants.json
```

Output format:

```json
{
  "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OlCBKDMds",
  "competitions": [
    {
      "sheet_title": "Fairyweight",
      "approved_participants": [
        { "bot_name": "Tiny Terror", "team_name": "Team Voltage", "image_url": null },
        { "bot_name": "Spark Plug",  "team_name": "High Voltage",  "image_url": null }
      ]
    }
  ]
}
```

---

### Step 5 — Bulk-add robots to Challonge brackets

Add the approved robots to their respective Challonge tournaments. The tournament ID or
URL slug for each competition must already exist in Challonge.

Add all competitions:

```bash
mcchallonge-bulk-add approved_participants.json abc123def
```

Add a single competition by name:

```bash
mcchallonge-bulk-add approved_participants.json abc123def --competition "Fairyweight"
```

With verbose output to confirm each participant added:

```bash
mcchallonge-bulk-add approved_participants.json abc123def --competition "Fairyweight" -v
```

---

### Step 6 — Run the match dashboard

Start the Flask dashboard to show match status across all brackets.

```bash
python -m mcchallonge.app
```

Then open:

- http://127.0.0.1:5000/ — overview
- http://127.0.0.1:5000/participants — participant list
- http://127.0.0.1:5000/matches — match list, filterable by bracket and status

The dashboard loads from a local JSON cache (`build/tournament_cache.json` by default).
Use the **Update Local Cache** button in the UI to pull fresh data from Challonge.

---

## Installation

### Monorepo development (recommended)

```bat
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements-dev.txt
```

This installs all three packages in editable mode plus dev dependencies (pytest, etc.).

### Linux equivalent

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

To deactivate:

```bash
deactivate
```

---

## Configuration

All environment variables are loaded from `.env` at the repo root via `python-dotenv`.

**Setup (one-time):**

```bash
cp .env.example .env
```

Then open `.env` and fill in the sections relevant to your workflow:

- **MCCHALLONGE** — Challonge API credentials (required for bracket management)
- **RCE2SHEET** — Google Sheets OAuth or service account (only needed if using rce2sheet)
- **SHARED** — Common settings like build directory

See `.env.example` for detailed comments on each variable.

**Important:**
- Never commit `.env` to version control — it is already in `.gitignore`.
- All three packages (`mcchallonge`, `rce2sheet`, `mcrobotcombatevents`) automatically search for `.env` when run from the repo root.

### Challonge API

Required variables:

```text
challonge_user    your Challonge username
challonge_key     your Challonge API key
```

Get from: https://challonge.com/settings/developer

### Google Sheets (optional, for rce2sheet)

For local development convenience, set:

```text
GOOGLE_OAUTH_CLIENT_SECRETS=path/to/client_secret.json
```

This avoids typing `--oauth-client-secrets` every time. After first authorization, the token
is stored in your OS keyring automatically, so you don't need this set for subsequent runs.

Alternatively, use service account auth by setting `GOOGLE_APPLICATION_CREDENTIALS`.
See `.env.example` for both options.

### Dashboard Appearance (optional, for mcchallonge)

Customize the dashboard logo by setting `MCCHALLONGE_LOGO_URL` in `.env`:

```text
# Absolute URL
MCCHALLONGE_LOGO_URL=https://example.com/logo.png

# Or relative path from static folder
MCCHALLONGE_LOGO_URL=img/logo.png
```

If not set, the dashboard displays without a logo. The logo appears in the header
of the main dashboard page.

---

## Other CLI tools

### Generate a static tournament dashboard HTML

```bash
python -m mcchallonge.cli.generate_dashboard abc123def -o build/index.html
```

Offline mode (no API call):

```bash
python -m mcchallonge.cli.generate_dashboard abc123def \
    --offline \
    --tournament-file build/tournament.json \
    --participants-file build/participants.json \
    --matches-file build/matches.json \
    -o build/index.html
```

### Build a fully static site

```bash
python -m mcchallonge.app build
```

Output goes to the `build/` directory.

---

## Tests

```bash
pytest
```

Integration tests hit the live Challonge API and are deselected by default.
To run them, mark with `-m integration` and ensure credentials are set in `.env`.

### Production Hosting Options

#### Option 1: Reverse proxy with Nginx + Waitress

Run the app behind a production WSGI server:

```bash
python -m mcchallonge.app serve --host 127.0.0.1 --port 8000 --threads 8
```

Nginx and systemd examples are available at:

- `deploy/nginx/mcchallonge.conf`
- `deploy/systemd/mcchallonge.service`

#### Option 2: Serverless static hosting on S3/CloudFront

Terraform and CI/CD scaffolding are included for fixed-filename static data hosting:

- `infra/terraform/envs/prod`
- `.github/workflows/infra.yml`
- `.github/workflows/deploy-site.yml`
- `.github/workflows/deploy-lambda.yml`

Full guide:

- `docs/serverless-s3-terraform-github-actions.md`
- `infra/terraform/README.md`

---

## FAQ & Troubleshooting

### Keyring not available: `RuntimeError: Failed to save token`

**Problem:** rce2sheet is trying to save your Google OAuth token to the OS keyring, but keyring support is not available (e.g., running in WSL, Docker without D-Bus, or SSH session).

**Solution:** Force file-based token storage by setting the env var:

```bash
export RCE2SHEET_TOKEN_BACKEND=file
```

Then run rce2sheet as normal. The token will be saved as plaintext JSON in the default location (`rce2sheet_token.json` or custom path via `--oauth-token`).

**Warning:** File-based tokens are less secure than keyring storage. Only use this when keyring is unavailable.

### Google OAuth: "Use --oauth-client-secrets to authorize for the first time"

**Problem:** You ran rce2sheet or rce2sheet-read without `--oauth-client-secrets` and don't have a stored token.

**Solution:** On your first run, provide the client secrets file (or set `GOOGLE_OAUTH_CLIENT_SECRETS` env var):

```bash
rce2sheet build/event.json --oauth-client-secrets client_secret.json --title "..."
```

A browser window will open for authorization. After login, the token is stored in your keyring.
On subsequent runs (same machine), omit the flag—the stored token is used automatically.

### Challonge API: "KeyError: 'challonge_user' / 'challonge_key'"

**Problem:** `mcchallonge` can't find your Challonge credentials.

**Solution:** Ensure `.env` is in the repo root and contains:

```text
challonge_user=your_username
challonge_key=your_api_key
```

Get your API key from: https://challonge.com/settings/developer

### Flask dashboard won't start: "Address already in use"

**Problem:** Port 5000 is already in use (e.g., another Flask instance is running).

**Solution:** Either stop the other process, or run on a different port:

```bash
FLASK_RUN_PORT=5001 python -m mcchallonge.app
```

Then open http://127.0.0.1:5001
