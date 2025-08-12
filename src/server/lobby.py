"""Lobby management for multiplayer games."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Lobby:
    id: str
    name: str
    mode: str = "default"
    max_players: int = 4
    cur_players: int = 0
    region: str = "global"
    seed: int = 0
    players: List[str] = field(default_factory=list)
    ready: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "mode": self.mode,
            "max_players": self.max_players,
            "cur_players": self.cur_players,
            "region": self.region,
            "players": list(self.players),
        }


class LobbyManager:
    """Create and track lobbies."""

    def __init__(self) -> None:
        self._lobbies: Dict[str, Lobby] = {}
        self._next_id = 1

    def create(self, name: str, mode: str = "default", max_players: int = 4, seed: int = 0,
               region: str = "global") -> Lobby:
        lobby_id = str(self._next_id)
        self._next_id += 1
        lobby = Lobby(lobby_id, name, mode=mode, max_players=max_players, seed=seed, region=region)
        self._lobbies[lobby_id] = lobby
        return lobby

    def get(self, lobby_id: str) -> Lobby | None:
        return self._lobbies.get(lobby_id)

    def remove(self, lobby_id: str) -> None:
        self._lobbies.pop(lobby_id, None)

    def list_lobbies(self) -> List[Dict[str, object]]:
        return [lobby.to_dict() for lobby in self._lobbies.values()]
