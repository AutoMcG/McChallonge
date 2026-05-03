import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import boto3

from mcchallonge.services import challonging, think

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _tournament_ids_from_env() -> list[str]:
    raw = os.environ.get("CHALLONGE_TOURNAMENT_IDS") or os.environ.get("challonge_tournament_ids") or os.environ.get("challonge_tt_id", "")
    ids = [part.strip() for part in raw.split(",") if part.strip()]
    if not ids:
        raise ValueError("At least one tournament ID is required in CHALLONGE_TOURNAMENT_IDS or challonge_tt_id")
    return ids


def _data_keys(prefix: str) -> dict[str, str]:
    clean_prefix = prefix.strip("/")
    base = f"{clean_prefix}/" if clean_prefix else ""
    return {
        "tournament": f"{base}tournament.json",
        "participants": f"{base}participants.json",
        "matches": f"{base}matches.json",
        "manifest": f"{base}manifest.json",
    }


def _fetch_tournament_payload(tournament_ids: list[str]) -> dict[str, Any]:
    session = challonging.prepare_session_from_env()

    tournaments: dict[str, dict[str, Any]] = {}
    participants: dict[str, list[dict[str, Any]]] = {}
    matches: dict[str, list[dict[str, Any]]] = {}
    manifest: dict[str, dict[str, Any]] = {}

    generated_at = _utc_now_iso()

    for tournament_id in tournament_ids:
        tournament = challonging.get_tournament_data(session, tournament_id)
        participant_items = challonging.get_participants_data(session, tournament_id)
        match_items = challonging.get_match_data(session, tournament_id)
        enriched_participants = think.count_outcomes(match_items, participant_items)

        tournaments[str(tournament_id)] = tournament.__dict__
        participants[str(tournament_id)] = [item.__dict__ for item in enriched_participants]
        matches[str(tournament_id)] = [item.__dict__ for item in match_items]
        manifest[str(tournament_id)] = {
            "schema_version": "1.0.0",
            "generated_at": generated_at,
            "source_tournament_id": str(tournament_id),
            "participants_count": len(enriched_participants),
            "matches_count": len(match_items),
            "publish_status": "complete",
        }

    return {
        "tournaments": tournaments,
        "participants": participants,
        "matches": matches,
        "manifest": manifest,
    }


def _put_json(s3_client: Any, bucket: str, key: str, payload: dict[str, Any]) -> None:
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(payload, indent=2).encode("utf-8"),
        ContentType="application/json",
        CacheControl="no-cache, must-revalidate",
    )


def publish_to_s3() -> dict[str, Any]:
    bucket = _require_env("MCCHALLONGE_DATA_BUCKET")
    prefix = os.environ.get("MCCHALLONGE_DATA_PREFIX", "data")
    tournament_ids = _tournament_ids_from_env()
    keys = _data_keys(prefix)

    payload = _fetch_tournament_payload(tournament_ids)

    s3_client = boto3.client("s3")

    # Publish manifest last so clients see complete refreshes.
    _put_json(s3_client, bucket, keys["tournament"], {"tournaments": payload["tournaments"]})
    _put_json(s3_client, bucket, keys["participants"], {"tournaments": payload["participants"]})
    _put_json(s3_client, bucket, keys["matches"], {"tournaments": payload["matches"]})
    _put_json(s3_client, bucket, keys["manifest"], {"tournaments": payload["manifest"]})

    result = {
        "bucket": bucket,
        "keys": keys,
        "tournament_ids": tournament_ids,
        "generated_at": _utc_now_iso(),
    }
    logger.info("Published tournament data: %s", result)
    return result


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    del event, context
    details = publish_to_s3()
    return {"ok": True, **details}


def main() -> None:
    result = publish_to_s3()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
