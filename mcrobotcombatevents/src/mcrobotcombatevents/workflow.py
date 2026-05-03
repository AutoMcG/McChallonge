from __future__ import annotations

import json
import os

from .client import RCEHttpClient
from .models import RCEEvent
from .parser import parse_competition_links, parse_competition_page


def scrape_event(event_id: int, client: RCEHttpClient | None = None) -> RCEEvent:
    client = client or RCEHttpClient()
    event_url = client.event_url(event_id)

    event_html = client.get_event_html(event_id)
    competition_urls = parse_competition_links(event_id, event_html, client.BASE_URL)

    event = RCEEvent(event_id=event_id, event_url=event_url)

    for competition_url in competition_urls:
        competition_html = client.get_competition_html(competition_url)
        competition = parse_competition_page(competition_url, competition_html)
        event.competitions.append(competition)

    return event


def event_to_json(event: RCEEvent, indent: int = 2) -> str:
    return json.dumps(event.to_dict(), indent=indent)


def scrape_event_to_file(
    event_id: int,
    output_path: str,
    client: RCEHttpClient | None = None,
    indent: int = 2,
) -> RCEEvent:
    event = scrape_event(event_id=event_id, client=client)
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(event_to_json(event, indent=indent))

    return event
