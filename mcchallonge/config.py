import os
from dotenv import load_dotenv

load_dotenv()

# Challonge API settings
CHALLONGE_USER = os.environ.get('challonge_user')
CHALLONGE_KEY = os.environ.get('challonge_key')

# Support multiple tournament IDs (comma-separated in challonge_tournament_ids,
# falling back to the legacy single-ID key challonge_tt_id).
_raw_ids = os.environ.get('challonge_tournament_ids') or os.environ.get('challonge_tt_id', '')
CHALLONGE_TOURNAMENT_IDS: list[str] = [t.strip() for t in _raw_ids.split(',') if t.strip()]
CHALLONGE_TOURNAMENT_ID: str | None = CHALLONGE_TOURNAMENT_IDS[0] if CHALLONGE_TOURNAMENT_IDS else None

# Output settings
BUILD_DIR = os.environ.get('BUILD_DIR', 'build')

# Optional logo for dashboard header. Supports absolute URL or path under static/.
# Examples:
# - MCCHALLONGE_LOGO_URL=https://example.com/logo.png
# - MCCHALLONGE_LOGO_URL=img/logo.png
MCCHALLONGE_LOGO_URL = os.environ.get('MCCHALLONGE_LOGO_URL')

# Client-side data-loading mode for rendered pages.
# - api: read from Flask API endpoints (/api/cache...)
# - fixed: read fixed static files from MCCHALLONGE_CLIENT_DATA_ROOT
MCCHALLONGE_CLIENT_DATA_MODE = os.environ.get('MCCHALLONGE_CLIENT_DATA_MODE', 'api').strip().lower()
MCCHALLONGE_CLIENT_DATA_ROOT = os.environ.get('MCCHALLONGE_CLIENT_DATA_ROOT', '/data').strip() or '/data'