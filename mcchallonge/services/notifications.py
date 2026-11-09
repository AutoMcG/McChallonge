import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

from mcchallonge import config
from .participant_images import get_approved_participants_file_path

NOTIFICATION_TYPE_QUEUE_CALL = "queue_call"
NOTIFICATION_TYPE_EO_SUMMON = "eo_summon"
ALLOWED_NOTIFICATION_TYPES = {NOTIFICATION_TYPE_QUEUE_CALL, NOTIFICATION_TYPE_EO_SUMMON}


def _normalise_name(value: str | None) -> str:
    return " ".join(str(value or "").strip().lower().split())


def build_robot_key(tournament_key: str, bot_name: str) -> str:
    return f"{str(tournament_key).strip()}::{_normalise_name(bot_name)}"


def get_notifications_file_path() -> Path:
    configured = os.environ.get(
        "MCCHALLONGE_NOTIFICATIONS_FILE",
        f"{config.BUILD_DIR}/notifications.json",
    )
    return Path(configured).expanduser().resolve()


def _load_notifications_payload() -> dict[str, Any]:
    path = get_notifications_file_path()
    if not path.exists():
        return {"notifications": []}
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    notifications = payload.get("notifications")
    if not isinstance(notifications, list):
        return {"notifications": []}
    return {"notifications": notifications}


def _save_notifications_payload(payload: dict[str, Any]) -> None:
    path = get_notifications_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _sorted_notifications(notifications: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(notifications, key=lambda n: str(n.get("created_at") or ""), reverse=True)


def list_all_notifications() -> list[dict[str, Any]]:
    payload = _load_notifications_payload()
    return _sorted_notifications(payload.get("notifications", []))


def list_notifications_for_robot_keys(robot_keys: set[str]) -> list[dict[str, Any]]:
    if not robot_keys:
        return []
    selected = [
        notification
        for notification in list_all_notifications()
        if str(notification.get("robot_key") or "") in robot_keys
    ]
    return selected


def create_notification(
    *,
    notification_type: str,
    robot_key: str,
    tournament_key: str,
    competition_name: str,
    bot_name: str,
    team_name: str | None,
    participant_id: int | None,
    message: str | None,
) -> dict[str, Any]:
    if notification_type not in ALLOWED_NOTIFICATION_TYPES:
        raise ValueError("Unsupported notification type.")

    notification = {
        "id": str(uuid.uuid4()),
        "type": notification_type,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "robot_key": robot_key,
        "tournament_key": str(tournament_key),
        "competition_name": str(competition_name or ""),
        "bot_name": str(bot_name or ""),
        "team_name": str(team_name or ""),
        "participant_id": participant_id,
        "message": str(message or ""),
        "created_by": "loopback_admin",
    }

    payload = _load_notifications_payload()
    payload["notifications"] = payload.get("notifications", [])
    payload["notifications"].append(notification)
    _save_notifications_payload(payload)
    return notification


def _load_approved_participants_lookup() -> tuple[dict[tuple[str, str], str], dict[str, str]]:
    source = get_approved_participants_file_path()
    if not source.exists():
        return {}, {}

    with source.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    by_competition: dict[tuple[str, str], str] = {}
    by_name: dict[str, str] = {}
    for competition in payload.get("competitions") or []:
        comp_name = (
            competition.get("competition_name")
            or competition.get("sheet_title")
            or competition.get("name")
            or ""
        )
        comp_key = _normalise_name(comp_name)
        participants = competition.get("approved_participants") or competition.get("bots") or []
        for participant in participants:
            bot_name = participant.get("bot_name") or participant.get("name") or ""
            if not bot_name:
                continue
            bot_key = _normalise_name(bot_name)
            team_name = participant.get("team_name") or ""
            by_competition[(comp_key, bot_key)] = team_name
            if bot_key not in by_name:
                by_name[bot_key] = team_name
    return by_competition, by_name


def build_robot_directory(cache_data: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not cache_data:
        return []

    by_competition, by_name = _load_approved_participants_lookup()
    robots: list[dict[str, Any]] = []

    for tournament_key, entry in (cache_data.get("tournaments") or {}).items():
        tournament = entry.get("tournament") or {}
        competition_name = str(tournament.get("name") or tournament_key)
        comp_key = _normalise_name(competition_name)

        for participant in (entry.get("participants") or []):
            bot_name = str(participant.get("name") or "").strip()
            if not bot_name:
                continue
            bot_key = _normalise_name(bot_name)
            team_name = (
                by_competition.get((comp_key, bot_key))
                or by_name.get(bot_key)
                or ""
            )
            participant_id_raw = participant.get("id")
            participant_id = participant_id_raw if isinstance(participant_id_raw, int) else None
            robot_key = build_robot_key(str(tournament_key), bot_name)
            robots.append({
                "robot_key": robot_key,
                "tournament_key": str(tournament_key),
                "competition_name": competition_name,
                "bot_name": bot_name,
                "team_name": team_name,
                "participant_id": participant_id,
            })

    robots.sort(key=lambda row: (row["competition_name"].lower(), row["bot_name"].lower()))
    return robots
