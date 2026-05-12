import json
import os
import re
import time
from pathlib import Path
from typing import Any


def get_underway_dir() -> Path:
    configured_path = os.environ.get("MCCHALLONGE_UNDERWAY_DIR", "build/underway")
    return Path(configured_path).expanduser().resolve()


def get_underway_manifest_path() -> Path:
    return get_underway_dir() / "manifest.json"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", str(value or "").strip().lower())
    return slug.strip("-") or "unknown"


def _collect_underway_entries(cache_data: dict[str, Any]) -> list[dict[str, Any]]:
    tournaments = cache_data.get("tournaments") or {}
    entries: list[dict[str, Any]] = []

    for tournament_key, tournament_entry in tournaments.items():
        tournament_name = (
            (tournament_entry.get("tournament") or {}).get("name")
            or str(tournament_key)
        )

        participants = tournament_entry.get("participants") or []
        participants_by_id = {
            p.get("id"): p.get("name")
            for p in participants
            if p.get("id") is not None
        }

        for match in tournament_entry.get("matches") or []:
            underway_at = match.get("underway_at")
            completed_at = match.get("completed_at")
            if not underway_at or completed_at:
                continue

            p1 = participants_by_id.get(match.get("player1_id")) or "TBD"
            p2 = participants_by_id.get(match.get("player2_id")) or "TBD"
            suggested_order = match.get("suggested_play_order")
            try:
                sort_order = int(suggested_order)
            except (TypeError, ValueError):
                sort_order = 10**9

            entries.append(
                {
                    "tournament_key": str(tournament_key),
                    "tournament_name": tournament_name,
                    "match_id": match.get("id"),
                    "player_1": p1,
                    "player_2": p2,
                    "underway_at": underway_at,
                    "suggested_play_order": suggested_order,
                    "sort_order": sort_order,
                }
            )

    entries.sort(
        key=lambda item: (
            item["tournament_name"].lower(),
            item["sort_order"],
            int(item["match_id"] or 0),
        )
    )
    return entries


def _draw_banner(output_file: Path, title_text: str, subtitle_text: str) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise RuntimeError(
            "Pillow is required to generate underway banners. Install with: pip install pillow"
        ) from exc

    width = 1400
    height = 200

    # Fully transparent canvas — shapes float as a broadcast overlay.
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    player_1, sep, player_2 = title_text.partition(" vs ")
    if not sep:
        player_1 = title_text
        player_2 = ""

    # All shapes share y=0 as their top edge — butts against the top of the frame.
    # Drawing order: competitors → VS center → name plate (so plate sits on top).
    left_poly = [(0, 0), (627, 0), (650, 190), (0, 190)]
    right_poly = [(773, 0), (1400, 0), (1400, 190), (750, 190)]
    center_poly = [(620, 0), (780, 0), (745, 190), (655, 190)]
    subtitle_poly = [(50, 0), (1350, 0), (1300, 34), (100, 34)]

    # Base fills — competitor panels slightly translucent, plate and center fully opaque.
    draw.polygon(left_poly, fill=(29, 78, 216, 218))
    draw.polygon(right_poly, fill=(185, 28, 28, 218))
    draw.polygon(center_poly, fill=(8, 14, 36, 235))

    # Gloss strip across the BOTTOM ~35 % of each side panel.
    def _bottom_gloss(poly: list, gloss_rgba: tuple) -> None:
        ys = [p[1] for p in poly]
        bottom_y = max(ys)
        cut_y = bottom_y - (bottom_y - min(ys)) * 0.35
        clipped = []
        for i, pt in enumerate(poly):
            nxt = poly[(i + 1) % len(poly)]
            if pt[1] >= cut_y:
                clipped.append(pt)
            if (pt[1] >= cut_y) != (nxt[1] >= cut_y):
                if nxt[1] == pt[1]:
                    continue
                t = (cut_y - pt[1]) / (nxt[1] - pt[1])
                clipped.append((pt[0] + t * (nxt[0] - pt[0]), cut_y))
        if len(clipped) >= 3:
            draw.polygon(clipped, fill=gloss_rgba)

    _bottom_gloss(left_poly, (160, 200, 255, 55))
    _bottom_gloss(right_poly, (255, 140, 140, 55))
    _bottom_gloss(center_poly, (80, 110, 200, 45))

    # Glow borders: wide soft outer ring then bright inner line.
    def _glow_border(poly: list, bright: tuple, glow: tuple) -> None:
        pts = poly + [poly[0]]
        draw.line(pts, fill=glow, width=7)
        draw.line(pts, fill=bright, width=2)

    _glow_border(left_poly, (147, 197, 253, 255), (37, 99, 235, 100))
    _glow_border(right_poly, (252, 165, 165, 255), (220, 38, 38, 100))
    _glow_border(center_poly, (203, 213, 225, 255), (80, 110, 180, 110))

    # Draw the tournament name plate last so it fully covers everything beneath it.
    draw.polygon(subtitle_poly, fill=(8, 14, 36, 255))
    _glow_border(subtitle_poly, (96, 130, 220, 220), (37, 99, 235, 70))

    try:
        name_font = ImageFont.truetype("arialbd.ttf", 38)
        vs_font = ImageFont.truetype("arialbd.ttf", 48)
        subtitle_font = ImageFont.truetype("arial.ttf", 22)
    except OSError:
        name_font = ImageFont.load_default()
        vs_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()

    def _centered_text(
        text: str,
        box: tuple[int, int, int, int],
        font,
        fill: tuple,
        shadow: tuple = (0, 0, 0, 200),
    ) -> None:
        if not text:
            return
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x1, y1, x2, y2 = box
        x = x1 + (x2 - x1 - tw) / 2
        y = y1 + (y2 - y1 - th) / 2
        # Multi-direction shadow produces a broadcast-style drop glow.
        for ox, oy in ((-2, 2), (2, 2), (-2, -2), (2, -2), (0, 3), (0, -3), (3, 0), (-3, 0)):
            draw.text((x + ox, y + oy), text, font=font, fill=shadow)
        draw.text((x, y), text, font=font, fill=fill)

    # Text regions sit below the subtitle plate (y≥38) so they don't clash.
    _centered_text(player_1, (10, 38, 610, 175), name_font, (255, 255, 255, 255))
    _centered_text(player_2, (790, 38, 1390, 175), name_font, (255, 255, 255, 255))
    _centered_text("VS", (640, 38, 760, 175), vs_font, (248, 250, 252, 255))
    _centered_text(
        subtitle_text,
        (110, 3, 1290, 31),
        subtitle_font,
        (191, 219, 254, 255),
        shadow=(0, 0, 30, 190),
    )

    image.save(output_file, format="PNG")


def generate_underway_banners(cache_data: dict[str, Any]) -> dict[str, Any]:
    underway_dir = get_underway_dir()
    underway_dir.mkdir(parents=True, exist_ok=True)

    for png_file in underway_dir.glob("*.png"):
        png_file.unlink()

    entries = _collect_underway_entries(cache_data)
    banners: list[dict[str, Any]] = []

    for index, entry in enumerate(entries, start=1):
        tournament_slug = _slugify(entry["tournament_name"])
        match_id = entry["match_id"] if entry["match_id"] is not None else index
        filename = f"{tournament_slug}-match-{match_id}.png"
        output_file = underway_dir / filename

        title_text = f"{entry['player_1']} vs {entry['player_2']}"
        subtitle_text = f"{entry['tournament_name']}"
        _draw_banner(output_file, title_text, subtitle_text)

        banners.append(
            {
                "filename": filename,
                "title": title_text,
                "subtitle": subtitle_text,
                "tournament_name": entry["tournament_name"],
                "match_id": entry["match_id"],
                "underway_at": entry["underway_at"],
                "suggested_play_order": entry["suggested_play_order"],
                "url": f"/underway/banner/{filename}",
            }
        )

    manifest = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(banners),
        "banners": banners,
    }

    with get_underway_manifest_path().open("w", encoding="utf-8") as manifest_file:
        json.dump(manifest, manifest_file, indent=2)

    return manifest


def load_underway_manifest() -> dict[str, Any] | None:
    manifest_path = get_underway_manifest_path()
    if not manifest_path.exists():
        return None

    with manifest_path.open("r", encoding="utf-8") as manifest_file:
        return json.load(manifest_file)
