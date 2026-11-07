import hashlib
import json
import logging
import os
import re
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import requests
from mcchallonge import config

logger = logging.getLogger(__name__)

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
_THUMBNAIL_SIZE = 96
_PIL_UNAVAILABLE_LOGGED = False


def get_approved_participants_file_path() -> Path:
    configured = os.environ.get(
        "MCCHALLONGE_APPROVED_PARTICIPANTS_FILE",
        config.DEFAULT_APPROVED_PARTICIPANTS_FILE,
    )
    return Path(configured).expanduser().resolve()


def get_image_cache_dir() -> Path:
    configured = os.environ.get("MCCHALLONGE_IMAGE_CACHE_DIR", config.DEFAULT_IMAGE_CACHE_DIR)
    return Path(configured).expanduser().resolve()


def _normalise_name(value: str | None) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _slugify_name(value: str | None) -> str:
    normalised = _normalise_name(value)
    slug = re.sub(r"[^a-z0-9]+", "-", normalised).strip("-")
    return slug or "participant"


def _get_ext_for_url(image_url: str, content_type: str | None = None) -> str:
    parsed = urlparse(image_url)
    ext = Path(parsed.path).suffix.lower()
    if ext in _IMAGE_EXTENSIONS:
        return ext

    if content_type:
        lowered = content_type.lower()
        if "image/jpeg" in lowered:
            return ".jpg"
        if "image/png" in lowered:
            return ".png"
        if "image/gif" in lowered:
            return ".gif"
        if "image/webp" in lowered:
            return ".webp"

    return ".jpg"


def _iter_approved_participants(payload: dict) -> list[tuple[str, str, str]]:
    entries: list[tuple[str, str, str]] = []
    competitions = payload.get("competitions") or []
    for comp in competitions:
        competition_name = (
            comp.get("competition_name")
            or comp.get("sheet_title")
            or comp.get("name")
            or ""
        )
        participants = comp.get("approved_participants") or comp.get("bots") or []
        for p in participants:
            bot_name = p.get("bot_name") or p.get("name") or ""
            image_url = p.get("image_url") or p.get("img") or p.get("image") or ""
            if bot_name and image_url:
                entries.append((competition_name, bot_name, image_url))
    return entries


def _thumbnail_name(prefix: str) -> str:
    return f"{prefix}-thumb.jpg"


def _load_pillow_image(payload: bytes):
    global _PIL_UNAVAILABLE_LOGGED

    try:
        from PIL import Image
    except ModuleNotFoundError:
        if not _PIL_UNAVAILABLE_LOGGED:
            logger.warning("Pillow is not installed; using full-size cached participant images without thumbnails")
            _PIL_UNAVAILABLE_LOGGED = True
        return None

    with Image.open(BytesIO(payload)) as image:
        # Normalize mode so JPEG output is always supported.
        return image.convert("RGB")


def _write_thumbnail_from_bytes(payload: bytes, output_file: Path) -> bool:
    try:
        image = _load_pillow_image(payload)
        if image is None:
            return False
        image.thumbnail((_THUMBNAIL_SIZE, _THUMBNAIL_SIZE))
        image.save(output_file, format="JPEG", quality=82, optimize=True)
        return True
    except Exception:
        logger.exception("Failed to generate participant thumbnail at %s", output_file)
        return False


def _write_thumbnail_from_file(source_file: Path, output_file: Path) -> bool:
    try:
        payload = source_file.read_bytes()
    except Exception:
        logger.exception("Failed to read source participant image for thumbnail: %s", source_file)
        return False
    return _write_thumbnail_from_bytes(payload, output_file)


def load_approved_participants_index() -> dict | None:
    source_file = get_approved_participants_file_path()
    if not source_file.exists():
        logger.info("Approved participants JSON not found at %s; bot images disabled", source_file)
        return None

    try:
        with source_file.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception:
        logger.exception("Failed to load approved participants JSON: %s", source_file)
        return None

    by_competition: dict[tuple[str, str], str] = {}
    by_name: dict[str, str] = {}

    for competition_name, bot_name, image_url in _iter_approved_participants(payload):
        comp_key = _normalise_name(competition_name)
        bot_key = _normalise_name(bot_name)
        by_competition[(comp_key, bot_key)] = image_url
        by_name.setdefault(bot_key, image_url)

    if not by_name:
        logger.info("Approved participants JSON loaded from %s but no image URLs were found", source_file)
        return None

    return {
        "by_competition": by_competition,
        "by_name": by_name,
    }


def cache_image(image_url: str, participant_name: str | None = None) -> str | None:
    if not image_url:
        return None

    cache_dir = get_image_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)

    url_hash = hashlib.sha1(image_url.encode("utf-8")).hexdigest()[:12]
    filename_stem = _slugify_name(participant_name)

    prefix = f"{filename_stem}-{url_hash}"
    thumb_file = cache_dir / _thumbnail_name(prefix)

    if thumb_file.exists():
        return f"/img/{thumb_file.name}"

    # Reuse an existing original and generate the thumbnail if needed.
    for existing in cache_dir.glob(f"{prefix}.*"):
        if existing.name == thumb_file.name:
            continue
        if _write_thumbnail_from_file(existing, thumb_file):
            return f"/img/{thumb_file.name}"

    headers = {
        "User-Agent": "McChallonger",
        "Accept": "image/*,*/*;q=0.8",
    }

    try:
        response = requests.get(image_url, headers=headers, timeout=20)
        response.raise_for_status()
    except Exception:
        logger.exception("Failed to download participant image from %s", image_url)
        return None

    ext = _get_ext_for_url(image_url, response.headers.get("Content-Type"))
    output_file = cache_dir / f"{prefix}{ext}"

    try:
        output_file.write_bytes(response.content)
    except Exception:
        logger.exception("Failed to write participant image cache file: %s", output_file)
        return None

    if _write_thumbnail_from_bytes(response.content, thumb_file):
        return f"/img/{thumb_file.name}"

    # Fallback to original image if thumbnail creation fails.
    return f"/img/{output_file.name}"


def resolve_cached_image_path(image_url: str, participant_name: str | None = None) -> str | None:
    """Return a cached image URL if present on disk; never performs a network call."""
    if not image_url:
        return None

    cache_dir = get_image_cache_dir()
    url_hash = hashlib.sha1(image_url.encode("utf-8")).hexdigest()[:12]
    filename_stem = _slugify_name(participant_name)
    prefix = f"{filename_stem}-{url_hash}"
    thumb_file = cache_dir / _thumbnail_name(prefix)

    if thumb_file.exists():
        return f"/img/{thumb_file.name}"

    for existing in cache_dir.glob(f"{prefix}.*"):
        if existing.name == thumb_file.name:
            continue
        return f"/img/{existing.name}"

    return None


def prewarm_approved_participant_images(approved_index: dict | None = None) -> int:
    """Download/cache all approved participant images once at server startup."""
    index = approved_index if approved_index is not None else load_approved_participants_index()
    if not index:
        return 0

    by_name = index.get("by_name", {})
    warmed = 0
    for bot_key, image_url in by_name.items():
        if cache_image(image_url, bot_key):
            warmed += 1
    return warmed


def enrich_participants_with_cached_images(
    participants: list,
    tournament_name: str,
    approved_index: dict | None = None,
    allow_download: bool = True,
) -> None:
    if not participants:
        return

    index = approved_index if approved_index is not None else load_approved_participants_index()
    if not index:
        return

    comp_key = _normalise_name(tournament_name)
    by_competition = index.get("by_competition", {})
    by_name = index.get("by_name", {})

    for participant in participants:
        bot_key = _normalise_name(getattr(participant, "name", ""))
        if not bot_key:
            continue

        image_url = by_competition.get((comp_key, bot_key)) or by_name.get(bot_key)
        if not image_url:
            continue

        if allow_download:
            cached_path = cache_image(image_url, getattr(participant, "name", None))
        else:
            cached_path = resolve_cached_image_path(image_url, getattr(participant, "name", None))
        if cached_path:
            participant.img = cached_path
