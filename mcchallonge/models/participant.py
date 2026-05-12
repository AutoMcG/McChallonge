from dataclasses import dataclass
from typing import Optional
import json

@dataclass
class Participant:
    id: Optional[int] = None
    name: Optional[str] = None
    wins: int = 0
    losses: int = 0
    img: Optional[str] = None

    def __init__(self, id=None, name=None, wins=0, losses=0, img=None, **kwargs):
        self.id = id
        self.name = name
        self.wins = wins
        self.losses = losses
        self.img = img
        # kwargs are ignored

    @staticmethod
    def from_json(j: str):
        data = json.loads(j) if isinstance(j, str) else j
        data = dict(data)
        # Coerce missing numeric fields to 0 rather than leaving them as None
        for k in ["wins", "losses"]:
            if data.get(k) is None:
                data[k] = 0
        return Participant(**data)

    def __str__(self):
        return json.dumps(self.__dict__, indent=2)