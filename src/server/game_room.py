"""Game room executing authoritative game logic."""
from __future__ import annotations

from typing import Any, Dict, List
import secrets

from .lobby import Lobby

from net.serialization import serialize_state
from .validation import validate_action


class GameRoom:
    """Maintain game state and apply actions."""

    def __init__(self, lobby_id: str, seed: int = 0) -> None:
        self.lobby_id = lobby_id
        self.seed = seed
        self.state: Dict[str, Any] = {"players": [], "tick": 0}
        self.actions: List[Dict[str, Any]] = []
        self._next_seq = 1
        self.started = False
        self.rejoin_tokens: Dict[str, str] = {}
        self.slots: Dict[str, int] = {}
        self.spectators: List[str] = []

    def apply_action(self, action: Dict[str, Any], player_index: int = 0) -> Dict[str, Any]:
        """Validate and apply an action returning state delta.

        The function raises :class:`ValueError` if the action fails validation or
        arrives out of order.  On success ``state['tick']`` is incremented and a
        minimal delta is returned.
        """

        validate_action(self.state, action, player_index)
        if action.get("seq") != self._next_seq:
            raise ValueError("bad seq")
        self.actions.append(action)
        self.state["tick"] += 1
        self._next_seq += 1
        return {"tick": self.state["tick"]}

    # player slot management -------------------------------------------
    def add_player(self, player_id: str, token: str | None = None) -> str:
        """Add a player slot and return rejoin token."""

        tok = token or secrets.token_hex(8)
        self.rejoin_tokens[player_id] = tok
        if player_id not in self.slots:
            self.slots[player_id] = len(self.slots)
        if player_id not in self.state["players"]:
            self.state["players"].append(player_id)
        return tok

    def drop_player(self, player_id: str) -> None:
        """Remove player from active list but keep slot/token."""

        if player_id in self.state["players"]:
            self.state["players"].remove(player_id)

    def rejoin_player(self, player_id: str, token: str) -> str:
        """Validate rejoin token and return state snapshot."""

        if self.rejoin_tokens.get(player_id) != token:
            raise ValueError("bad token")
        if player_id not in self.state["players"]:
            self.state["players"].append(player_id)
        return self.snapshot()

    def add_spectator(self, name: str) -> None:
        """Track spectator connections."""

        if name not in self.spectators:
            self.spectators.append(name)

    def can_start(self, lobby: "Lobby") -> bool:
        """Return ``True`` if the game can start based on lobby state."""

        return lobby.all_ready()

    def start(self, lobby: "Lobby") -> bool:
        """Mark the room as started when all players are ready."""

        if self.can_start(lobby):
            self.started = True
            return True
        return False

    def snapshot(self) -> str:
        """Return the full state snapshot."""

        return serialize_state(self.state)
