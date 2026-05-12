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

# Shared artifact path defaults
DEFAULT_CACHE_FILE = os.environ.get('MCCHALLONGE_CACHE_FILE', f'{BUILD_DIR}/tournament_cache.json')
DEFAULT_UNDERWAY_DIR = os.environ.get('MCCHALLONGE_UNDERWAY_DIR', f'{BUILD_DIR}/underway')
DEFAULT_APPROVED_PARTICIPANTS_FILE = os.environ.get(
	'MCCHALLONGE_APPROVED_PARTICIPANTS_FILE',
	f'{BUILD_DIR}/approved_participants.json',
)
DEFAULT_IMAGE_CACHE_DIR = os.environ.get('MCCHALLONGE_IMAGE_CACHE_DIR', f'{BUILD_DIR}/img')

# Shared timestamp formatting defaults
CACHE_METADATA_TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M'
UNDERWAY_TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%S'
UNDERWAY_MANIFEST_TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'

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