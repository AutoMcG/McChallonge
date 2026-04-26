# McChallonge
Tools for interacting with the Challonge API and generating a tournament dashboard (Flask app or static HTML).

# Setup
## Linux
At project root:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Windows
At project root:

```bat
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

To deactivate:

```bash
deactivate
```

# Configuration
Environment variables are loaded from `.env` (via `python-dotenv`).

Copy and fill in the sample file:

```bash
cp mcchallonge/sample-env .env
```

Required for API access:

```text
challonge_user
challonge_key
challonge_tt_id
```

Optional for OAuth helper:

```text
CHALLONGE_CLIENT_ID
CHALLONGE_CLIENT_SECRET
CHALLONGE_REDIRECT_URI
```

# Usage
## Run the Flask dashboard (dev server)

```bash
python -m mcchallonge.app
```

The dashboard now loads tournament data from a local JSON cache file (default: `build/tournament_cache.json`).
It does not fetch Challonge data automatically on page load.
Use the **Update Local Cache** button in the UI to refresh local cached data.

Optional cache file override:

```text
MCCHALLONGE_CACHE_FILE
```

Then open:
- http://127.0.0.1:5000/
- http://127.0.0.1:5000/participants
- http://127.0.0.1:5000/matches

## Build a static site (Flask-Freezer)

```bash
python -m mcchallonge.app build
```

Static output is generated in the `build` directory.

## Generate a static HTML file via CLI

```bash
python -m mcchallonge.cli.generate_dashboard <tournament_id_or_url> -o build/index.html
```

When run against the live API, this command now also writes these normalized JSON files next to the HTML output:

```text
tournament.json
participants.json
matches.json
```

It also generates section pages in the same output tree:

```text
participants
matches
```

Offline mode with local JSON files:

```bash
python -m mcchallonge.cli.generate_dashboard <tournament_id_or_url> \
	--offline \
	--tournament-file tournament.json \
	--participants-file participants.json \
	--matches-file matches.json \
	-o build/index.html
```

If you install the package, you can use the console scripts:

```bash
mcchallonge-dashboard <tournament_id_or_url> -o build/index.html
```

## OAuth helper CLI

```bash
python -m mcchallonge.cli.challonge_oauth_cli
```

Or, if installed:

```bash
mcchallonge-oauth
```

# Tests

```bash
pytest
```

Integration tests hit the real API and require `challonge_user` and `challonge_key` to be set.