from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .models import RCEBot, RCECompetition


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    compact = " ".join(value.split())
    return compact or None


def _competition_id_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    return path.split("/")[-1]


def parse_competition_links(event_id: int, event_html: str, base_url: str) -> list[str]:
    """Extract unique competition page links for the given event ID."""
    soup = BeautifulSoup(event_html, "html.parser")
    pattern = re.compile(rf"/events/{event_id}/competitions/[^/?#\"']+")

    links: list[str] = []
    seen: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        match = pattern.search(href)
        if not match:
            continue

        absolute = urljoin(base_url, match.group(0))
        if absolute in seen:
            continue

        seen.add(absolute)
        links.append(absolute)

    return links


def _find_robot_table(soup: BeautifulSoup):
    candidates = soup.find_all("table")
    expected_headers = {"bot", "team", "status"}

    for table in candidates:
        headers = {
            _clean_text(th.get_text(" ", strip=True)).lower()
            for th in table.find_all("th")
            if _clean_text(th.get_text(" ", strip=True))
        }
        if headers.intersection(expected_headers):
            return table

    return candidates[0] if candidates else None


def _header_index_map(table) -> dict[str, int]:
    header_row = table.find("tr")
    if header_row is None:
        return {}

    mapping: dict[str, int] = {}
    for idx, th in enumerate(header_row.find_all(["th", "td"])):
        text = _clean_text(th.get_text(" ", strip=True))
        if not text:
            continue
        lowered = text.lower()
        if "bot" in lowered or "name" in lowered:
            mapping.setdefault("bot_name", idx)
        if "team" in lowered:
            mapping.setdefault("team_name", idx)
        if "status" in lowered:
            mapping.setdefault("status", idx)
        if "image" in lowered or "photo" in lowered:
            mapping.setdefault("image_url", idx)

    return mapping


def parse_competition_page(competition_url: str, competition_html: str) -> RCECompetition:
    soup = BeautifulSoup(competition_html, "html.parser")

    title_el = soup.select_one("h1.comp-title")
    if title_el:
        direct_text = " ".join(
            text.strip() for text in title_el.find_all(string=True, recursive=False) if text.strip()
        )
        title = _clean_text(direct_text)
    else:
        subtitle_el = soup.select_one(".info-panel-subtitle > p:nth-child(1)")
        title = _clean_text(subtitle_el.get_text(" ", strip=True)) if subtitle_el else None

    competition = RCECompetition(
        competition_id=_competition_id_from_url(competition_url),
        competition_url=competition_url,
        competition_name=title,
    )

    table = _find_robot_table(soup)
    if table is None:
        return competition

    header_map = _header_index_map(table)
    rows = table.find_all("tr")
    if not rows:
        return competition

    body_rows = rows[1:] if rows[0].find_all("th") else rows

    for row in body_rows:
        cells = row.find_all("td")
        if not cells:
            continue

        image_tag = row.find("img")
        image_url = None
        if image_tag and image_tag.get("src"):
            image_url = urljoin(competition_url, image_tag["src"])

        def read_cell(key: str, fallback_idx: int | None = None) -> str | None:
            idx = header_map.get(key, fallback_idx)
            if idx is None or idx >= len(cells):
                return None
            return _clean_text(cells[idx].get_text(" ", strip=True))

        bot_name = read_cell("bot_name", 1 if len(cells) > 1 else 0)
        team_name = read_cell("team_name", 2 if len(cells) > 2 else None)
        status = read_cell("status", len(cells) - 1 if cells else None)

        if not any([image_url, bot_name, team_name, status]):
            continue

        competition.bots.append(
            RCEBot(
                image_url=image_url,
                bot_name=bot_name,
                team_name=team_name,
                status=status,
            )
        )

    return competition
