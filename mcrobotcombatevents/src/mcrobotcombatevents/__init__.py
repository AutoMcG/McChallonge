"""McRobot Combat Events scraper package."""

from .models import RCEBot, RCECompetition, RCEEvent
from .workflow import event_to_json, scrape_event, scrape_event_to_file

__all__ = [
    "RCEBot",
    "RCECompetition",
    "RCEEvent",
    "scrape_event",
    "scrape_event_to_file",
    "event_to_json",
]
