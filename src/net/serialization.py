"""Helpers for serialising game state for network transfer."""
from __future__ import annotations

import json
from typing import Any


def serialize_state(state: Any) -> str:
    """Serialise a game state object to a compact JSON string.

    The function accepts either a plain mapping or any object providing a
    ``to_dict`` method.  It intentionally performs no compression or binary
    packing to keep the implementation simple and debuggable.
    """

    if hasattr(state, "to_dict"):
        state = state.to_dict()
    return json.dumps(state, separators=(",", ":"))


def deserialize_state(payload: str) -> Any:
    """Inverse operation for :func:`serialize_state`."""

    return json.loads(payload)
