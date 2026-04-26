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


def _migrate_legacy(data: dict[str, Any]) -> dict[str, Any]:
    """Upgrade a legacy single-tournament cache payload to the multi-tournament format."""
    if "tournament" in data and "tournaments" not in data:
        tournament_id = str(data.get("meta", {}).get("tournament_id", "unknown"))
        return {"tournaments": {tournament_id: data}}
    return data


def load_cached_tournament_data() -> dict[str, Any] | None:
    """Load cached tournament data from disk, if it exists."""
    cache_path = get_cache_file_path()
    if not cache_path.exists():
        return None

    with cache_path.open("r", encoding="utf-8") as cache_file:
        data = json.load(cache_file)

    return _migrate_legacy(data)


def refresh_cached_tournament_data(tournament_id: str) -> dict[str, Any]:
    """Fetch latest data for one tournament and update the shared cache file."""
    session = challonging.prepare_session_from_env()

    tournament = challonging.get_tournament_data(session, tournament_id)
    participants = challonging.get_participants_data(session, tournament_id)
    matches = challonging.get_match_data(session, tournament_id)
    updated_participants = think.count_outcomes(matches, participants)

    entry: dict[str, Any] = {
        "tournament": tournament.__dict__,
        "participants": [p.__dict__ for p in updated_participants],
        "matches": [m.__dict__ for m in matches],
        "meta": {
            "cached_at": time.strftime("%Y-%m-%d %H:%M"),
            "tournament_id": tournament_id,
            "cache_file": str(get_cache_file_path()),
        },
    }

    # Load existing cache and merge (preserving other tournaments).
    cache_path = get_cache_file_path()
    existing: dict[str, Any] = {}
    if cache_path.exists():
        with cache_path.open("r", encoding="utf-8") as cache_file:
            existing = json.load(cache_file)
        existing = _migrate_legacy(existing)

    if "tournaments" not in existing:
        existing["tournaments"] = {}

    existing["tournaments"][str(tournament_id)] = entry

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("w", encoding="utf-8") as cache_file:
        json.dump(existing, cache_file, indent=2)

    logger.info("Cache updated for tournament %s at %s", tournament_id, cache_path)
    return existing


def refresh_all_cached_tournaments(tournament_ids: list[str]) -> dict[str, Any]:
    """Refresh cache for all given tournament IDs and return the full cache."""
    result: dict[str, Any] = {}
    for tournament_id in tournament_ids:
        result = refresh_cached_tournament_data(tournament_id)
    return result

