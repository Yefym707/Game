"""Game room executing authoritative game logic."""
from __future__ import annotations

from typing import Any, Dict, List

from net.serialization import serialize_state


class GameRoom:
    """Maintain game state and apply actions."""

    def __init__(self, lobby_id: str, seed: int = 0) -> None:
        self.lobby_id = lobby_id
        self.seed = seed
        self.state: Dict[str, Any] = {"players": [], "tick": 0}
        self.actions: List[Dict[str, Any]] = []

    def apply_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and apply an action returning state delta."""

        self.actions.append(action)
        self.state["tick"] += 1
        return {"tick": self.state["tick"]}

    def snapshot(self) -> str:
        """Return the full state snapshot."""

        return serialize_state(self.state)
