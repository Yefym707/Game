"""Game room executing authoritative game logic."""
from __future__ import annotations

from typing import Any, Dict, List

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

    def snapshot(self) -> str:
        """Return the full state snapshot."""

        return serialize_state(self.state)
