from typing import Optional
import json

from dataclasses import asdict, dataclass, fields
import json
from typing import Any, Optional


@dataclass(slots=True)
class Participant:
    id: Optional[int] = None
    name: Optional[str] = None
    wins: int = 0
    losses: int = 0
    img: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        allowed = {f.name for f in fields(cls)}
        filtered = {key: value for key, value in dict(data).items() if key in allowed}
        if filtered.get("wins") is None:
            filtered["wins"] = 0
        if filtered.get("losses") is None:
            filtered["losses"] = 0
        return cls(**filtered)

    @staticmethod
    def from_json(j: str):
        data = json.loads(j) if isinstance(j, str) else j
        return Participant.from_dict(data)

    def to_cache_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}

    def __str__(self):
        return json.dumps(self.to_cache_dict(), indent=2)