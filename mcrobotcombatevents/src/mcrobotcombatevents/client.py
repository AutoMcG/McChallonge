from __future__ import annotations

import requests


class RCEHttpClient:
    """Small HTTP client wrapper for Robot Combat Events scraping."""

    BASE_URL = "https://www.robotcombatevents.com"

    def __init__(self, session: requests.Session | None = None, timeout: float = 20.0):
        self.session = session or requests.Session()
        self.timeout = timeout
        self.session.headers.update(
            {
                "User-Agent": "mcrobotcombatevents/0.1 (+https://github.com/AutoMcG/McChallonge)",
                "Accept": "text/html,application/xhtml+xml",
            }
        )

    def event_url(self, event_id: int) -> str:
        return f"{self.BASE_URL}/events/{event_id}"

    def get_html(self, url: str) -> str:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def get_event_html(self, event_id: int) -> str:
        return self.get_html(self.event_url(event_id))

    def get_competition_html(self, competition_url: str) -> str:
        return self.get_html(competition_url)
