import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from . import challonging, think

logger = logging.getLogger(__name__)


def get_cache_file_path() -> Path:
    """Resolve the local cache file path for tournament data."""
    configured_path = os.environ.get("MCCHALLONGE_CACHE_FILE", "build/tournament_cache.json")
    return Path(configured_path).expanduser().resolve()


def load_cached_tournament_data() -> dict[str, Any] | None:
    """Load cached tournament data from disk, if it exists."""
    cache_path = get_cache_file_path()
    if not cache_path.exists():
        return None

    with cache_path.open("r", encoding="utf-8") as cache_file:
        return json.load(cache_file)


def refresh_cached_tournament_data(tournament_id: str) -> dict[str, Any]:
    """Fetch latest data from Challonge and persist a local JSON cache."""
    session = challonging.prepare_session_from_env()

    tournament = challonging.get_tournament_data(session, tournament_id)
    participants = challonging.get_participants_data(session, tournament_id)
    matches = challonging.get_match_data(session, tournament_id)
    updated_participants = think.count_outcomes(matches, participants)

    payload = {
        "tournament": tournament.__dict__,
        "participants": [participant.__dict__ for participant in updated_participants],
        "matches": [match.__dict__ for match in matches],
        "meta": {
            "cached_at": time.strftime("%Y-%m-%d %H:%M"),
            "tournament_id": tournament_id,
            "cache_file": str(get_cache_file_path()),
        },
    }

    cache_path = get_cache_file_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    with cache_path.open("w", encoding="utf-8") as cache_file:
        json.dump(payload, cache_file, indent=2)

    logger.info("Local cache updated at %s", cache_path)
    return payload
