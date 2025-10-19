from dataclasses import dataclass, field
from typing import Optional
import json

@dataclass
class Match:
    id: Optional[int] = None
    state: Optional[str] = None
    player1_id: Optional[int] = None
    player2_id: Optional[int] = None
    winner_id: Optional[int] = None
    loser_id: Optional[int] = None
    scheduled_time: Optional[str] = None
    location: Optional[str] = None
    underway_at: Optional[str] = None
    completed_at: Optional[str] = None

    def __init__(self, id=None, state=None, player1_id=None, player2_id=None, winner_id=None, loser_id=None,
                 scheduled_time=None, location=None, underway_at=None, completed_at=None, **kwargs):
        self.id = id
        self.state = state
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.winner_id = winner_id
        self.loser_id = loser_id
        self.scheduled_time = scheduled_time
        self.location = location
        self.underway_at = underway_at
        self.completed_at = completed_at
        # kwargs are ignored

    @staticmethod
    def from_json(j: str):
        data = json.loads(j) if isinstance(j, str) else j
        return Match(**data)

    def __str__(self):
        return json.dumps(self.__dict__, indent=2)