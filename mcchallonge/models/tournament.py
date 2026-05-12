from typing import Optional
import json

from dataclasses import asdict, dataclass, fields
import json
from typing import Any, Optional


@dataclass(slots=True)
class Tournament:
    id: Optional[int] = None
    name: Optional[str] = None
    state: Optional[str] = None
    url: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        allowed = {f.name for f in fields(cls)}
        return cls(**{key: value for key, value in dict(data).items() if key in allowed})

    @staticmethod
    def from_json(j: str):
        data = json.loads(j) if isinstance(j, str) else j
        return Tournament.from_dict(data)

    def to_cache_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}

    def __str__(self):
        return json.dumps(self.to_cache_dict(), indent=2)