"""Lobby management for multiplayer games."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any


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
    ready: Dict[str, bool] = field(default_factory=dict)
    privacy: str = "public"
    rtt: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "mode": self.mode,
            "max_players": self.max_players,
            "cur_players": self.cur_players,
            "region": self.region,
            "players": list(self.players),
            "privacy": self.privacy,
        }

    # ready state management -----------------------------------------
    def add_player(self, name: str) -> bool:
        if self.cur_players >= self.max_players:
            return False
        self.players.append(name)
        self.cur_players += 1
        self.ready[name] = False
        return True

    def remove_player(self, name: str) -> None:
        if name in self.players:
            self.players.remove(name)
            self.cur_players -= 1
        self.ready.pop(name, None)
        self.rtt.pop(name, None)

    def set_ready(self, name: str, is_ready: bool) -> None:
        if name in self.players:
            self.ready[name] = is_ready

    def all_ready(self) -> bool:
        if not self.players:
            return False
        return all(self.ready.get(p, False) for p in self.players)

    def status(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "players": [
                {"name": p, "ready": self.ready.get(p, False), "rtt": self.rtt.get(p, 0.0)}
                for p in self.players
            ],
            "privacy": self.privacy,
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

    def find_joinable(self, lobby_id: str) -> Lobby | None:
        """Return lobby if it exists and has free slots."""

        lobby = self._lobbies.get(lobby_id)
        if lobby and lobby.cur_players < lobby.max_players:
            return lobby
        return None

    def remove(self, lobby_id: str) -> None:
        self._lobbies.pop(lobby_id, None)

    def list_lobbies(self) -> List[Dict[str, object]]:
        return [lobby.to_dict() for lobby in self._lobbies.values()]
