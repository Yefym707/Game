from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Tuple


@dataclass
class Entity:
    x: int
    y: int
    symbol: str

    def to_dict(self) -> Dict[str, int]:
        return {"x": self.x, "y": self.y, "symbol": self.symbol}

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> "Entity":
        return cls(data["x"], data["y"], data["symbol"])


@dataclass
class Player(Entity):
    id: int = 0
    team: int = 0
    name: str = "Player"
    color: str = "white"
    health: int = 10
    inventory: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        data = super().to_dict()
        data.update(
            {
                "id": self.id,
                "team": self.team,
                "name": self.name,
                "color": self.color,
                "health": self.health,
                "inventory": list(self.inventory),
            }
        )
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "Player":
        return cls(
            data["x"],
            data["y"],
            data.get("symbol", "@"),
            data.get("id", 0),
            data.get("team", 0),
            data.get("name", "Player"),
            data.get("color", "white"),
            data.get("health", 10),
            data.get("inventory", []),
        )


@dataclass
class Zombie(Entity):
    pass


@dataclass
class Item:
    name: str
    symbol: str
