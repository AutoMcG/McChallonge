from dataclasses import dataclass
from typing import Optional
import json

@dataclass
class Tournament:
    id: Optional[int] = None
    name: Optional[str] = None
    state: Optional[str] = None
    url: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def __init__(self, id=None, name=None, state=None, url=None, started_at=None, completed_at=None, **kwargs):
        self.id = id
        self.name = name
        self.state = state
        self.url = url
        self.started_at = started_at
        self.completed_at = completed_at
        # kwargs are ignored

    @staticmethod
    def from_json(j: str):
        data = json.loads(j) if isinstance(j, str) else j
        return Tournament(**data)

    def __str__(self):
        return json.dumps(self.__dict__, indent=2)