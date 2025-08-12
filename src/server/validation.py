from __future__ import annotations

"""Server side validation for incoming ACTION payloads."""

from typing import Any, Dict

from gamecore import rules

ALLOWED_ACTIONS = {"move", "end_turn"}


def validate_action(state: Dict[str, Any], action: Dict[str, Any], player_index: int) -> None:
    """Validate ``action`` against current ``state``.

    The function performs a tiny subset of checks required for tests.  It
    ensures the action only contains whitelisted keys and that the move
    directions are valid.  Real game logic would perform additional checks
    like turn ownership, resources and game specific rules.
    """

    if not isinstance(action, dict):
        raise ValueError("action must be dict")
    if "seq" not in action:
        raise ValueError("missing seq")
    # ensure there is at least one recognised action
    keys = set(action) - {"seq"}
    if not keys:
        raise ValueError("empty action")
    if not keys <= ALLOWED_ACTIONS:
        raise ValueError("unsupported action type")
    if "move" in action and action["move"] not in rules.DIRECTIONS:
        raise ValueError("invalid move")
    # delegate to gamecore rules (which always returns True for now)
    if not rules.validate_action(state, action, player_index):
        raise ValueError("rejected by rules")

__all__ = ["validate_action", "ALLOWED_ACTIONS"]
