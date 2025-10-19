from dataclasses import dataclass, field
from typing import Optional
import json

@dataclass
class Participant:
    id: Optional[int] = None
    name: Optional[str] = None
    wins: int = 0
    losses: int = 0

    def __init__(self, id=None, name=None, wins=0, losses=0, **kwargs):
        self.id = id
        self.name = name
        self.wins = wins
        self.losses = losses
        # kwargs are ignored

    @staticmethod
    def from_json(j: str):
        data = json.loads(j) if isinstance(j, str) else j
        # Replace None with "empty" if needed
        for k, v in data.items():
            if v is None and k in ["id", "name", "wins", "losses"]:
                data[k] = "empty"
        return Participant(**data)

    def __str__(self):
        return json.dumps(self.__dict__, indent=2)