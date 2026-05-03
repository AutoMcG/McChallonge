from __future__ import annotations

import json
from dataclasses import dataclass, field

HEADERS = [
    "Image URL",
    "Bot Name",
    "Team Name",
    "Status",
    "Passed Weight",
    "Passed Safety",
    "Paid",
]

DROPDOWN_OPTIONS = ["Yes", "No"]
DROPDOWN_COL_START = 4  # 0-indexed; first of the three dropdown columns
DROPDOWN_COL_END = 7    # exclusive


@dataclass
class SheetBot:
    image_url: str | None = None
    bot_name: str | None = None
    team_name: str | None = None
    status: str | None = None

    def to_row(self) -> list[str]:
        return [
            self.image_url or "",
            self.bot_name or "",
            self.team_name or "",
            self.status or "",
            "",  # Passed Weight
            "",  # Passed Safety
            "",  # Paid
        ]


@dataclass
class SheetCompetition:
    competition_id: str
    competition_name: str | None = None
    bots: list[SheetBot] = field(default_factory=list)

    @property
    def sheet_title(self) -> str:
        return self.competition_name or self.competition_id


@dataclass
class SheetEvent:
    event_id: int
    competitions: list[SheetCompetition] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "SheetEvent":
        competitions = []
        for c in data.get("competitions", []):
            bots = [
                SheetBot(
                    image_url=b.get("image_url"),
                    bot_name=b.get("bot_name"),
                    team_name=b.get("team_name"),
                    status=b.get("status"),
                )
                for b in c.get("bots", [])
            ]
            competitions.append(
                SheetCompetition(
                    competition_id=c["competition_id"],
                    competition_name=c.get("competition_name"),
                    bots=bots,
                )
            )
        return cls(event_id=data["event_id"], competitions=competitions)

    @classmethod
    def from_json_file(cls, path: str) -> "SheetEvent":
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))
