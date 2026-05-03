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
cp mcchallonge/.env.example .env
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

## Run a production WSGI server (for Nginx reverse proxy)

```bash
python -m mcchallonge.app serve --host 127.0.0.1 --port 8000
```

Optional flags:

```text
--threads 8
```

Use this mode when you want Nginx to proxy requests to the app process.

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

# Nginx Hosting Option

This repository includes sample deployment config files:

- `deploy/nginx/mcchallonge.conf`
- `deploy/systemd/mcchallonge.service`

Typical Linux deployment flow:

1. Copy `deploy/systemd/mcchallonge.service` to `/etc/systemd/system/mcchallonge.service`.
2. Edit the `WorkingDirectory`, `EnvironmentFile`, and Python path values.
3. Start and enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mcchallonge
sudo systemctl status mcchallonge
```

4. Copy `deploy/nginx/mcchallonge.conf` to `/etc/nginx/sites-available/mcchallonge` and adjust `server_name`.
5. Enable the site and reload Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/mcchallonge /etc/nginx/sites-enabled/mcchallonge
sudo nginx -t
sudo systemctl reload nginx
```

# Serverless Hosting (S3 + Lambda + Terraform + GitHub Actions)

A full serverless deployment path is now included.

## What was added

- Terraform infrastructure under `infra/terraform/envs/prod`
- Lambda data updater at `mcchallonge/lambda_handlers/update_data.py`
- GitHub Actions workflows under `.github/workflows`
- Full deployment documentation in `docs/serverless-s3-terraform-github-actions.md`

## Frontend data mode

The dashboard supports two client data modes:

- `api` (default): reads from Flask API endpoints (`/api/cache...`)
- `fixed`: reads fixed JSON files from `MCCHALLONGE_CLIENT_DATA_ROOT` (default `/data`)

Fixed mode expects:

```text
/data/tournament.json
/data/participants.json
/data/matches.json
/data/manifest.json
```

When running static build (`python -m mcchallonge.app build`), fixed mode is automatically enabled for generated pages.

## CI/CD workflows

- `infra.yml`: Terraform validate/plan/apply
- `deploy-site.yml`: build and publish static site to S3
- `deploy-lambda.yml`: package and deploy updater Lambda

## Next step

Read and follow:

- `docs/serverless-s3-terraform-github-actions.md`
- `infra/terraform/README.md`