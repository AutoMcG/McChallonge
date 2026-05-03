from dataclasses import asdict, dataclass, field


@dataclass
class RCEBot:
    image_url: str | None = None
    bot_name: str | None = None
    team_name: str | None = None
    status: str | None = None


@dataclass
class RCECompetition:
    competition_id: str
    competition_url: str
    competition_name: str | None = None
    bots: list[RCEBot] = field(default_factory=list)


@dataclass
class RCEEvent:
    event_id: int
    event_url: str
    competitions: list[RCECompetition] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
