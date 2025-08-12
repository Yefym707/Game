"""Tiny helpers for limiting abusive clients and validating master payloads."""
from __future__ import annotations

from typing import Dict, Any

MAX_MESSAGE_SIZE = 65536


def check_size(text: str) -> None:
    """Ensure the raw websocket message is not excessively large."""

    if len(text) > MAX_MESSAGE_SIZE:
        raise ValueError("message too large")


def validate_master_payload(data: Dict[str, Any]) -> None:
    """Basic sanity checks for data sent to the master server."""

    if len(data.get("name", "")) > 64:
        raise ValueError("name too long")
    if len(data.get("mode", "")) > 32:
        raise ValueError("mode too long")
    if len(data.get("region", "")) > 32:
        raise ValueError("region too long")
    # ensure numeric fields are non-negative
    for key in ("max_players", "cur_players", "port", "protocol"):
        if int(data.get(key, 0)) < 0:
            raise ValueError(f"invalid {key}")


__all__ = ["check_size", "validate_master_payload"]
