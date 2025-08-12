"""Tiny helpers for limiting abusive clients."""
from __future__ import annotations

MAX_MESSAGE_SIZE = 65536


def check_size(text: str) -> None:
    """Ensure the raw websocket message is not excessively large."""

    if len(text) > MAX_MESSAGE_SIZE:
        raise ValueError("message too large")
