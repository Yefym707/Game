"""Network protocol definitions and helpers."""
from __future__ import annotations

import json
from enum import Enum
from typing import Any, Dict

PROTOCOL_VERSION = 1


class MessageType(str, Enum):
    """Supported message types."""

    HELLO = "HELLO"
    LOBBY = "LOBBY"
    ACTION = "ACTION"
    STATE = "STATE"
    PING = "PING"
    ERROR = "ERROR"
    INVITE_CREATE = "INVITE_CREATE"
    INVITE_INFO = "INVITE_INFO"
    INVITE_JOIN = "INVITE_JOIN"
    LOBBY_SET_READY = "LOBBY_SET_READY"
    LOBBY_STATUS = "LOBBY_STATUS"
    INVITE_REVOKE = "INVITE_REVOKE"
    INVITE_REFRESH = "INVITE_REFRESH"
    PONG = "PONG"
    RECONNECT = "RECONNECT"


_ALLOWED_TYPES = {t.value for t in MessageType}


def validate_message(data: Dict[str, Any]) -> None:
    """Validate a decoded message in-place.

    The function raises :class:`ValueError` if the message structure is invalid.
    Only a very small set of checks is performed – it is intentionally strict
    but minimal so it can be used on both client and server.
    """

    if "t" not in data:
        raise ValueError("missing 't' field")
    if data["t"] not in _ALLOWED_TYPES:
        raise ValueError(f"unknown message type: {data['t']}")
    if "v" in data and data["v"] != PROTOCOL_VERSION:
        raise ValueError("incompatible protocol version")


def encode_message(data: Dict[str, Any]) -> str:
    """Encode a message to JSON string."""

    payload = dict(data)
    payload.setdefault("v", PROTOCOL_VERSION)
    validate_message(payload)
    return json.dumps(payload, separators=(",", ":"))


def decode_message(text: str) -> Dict[str, Any]:
    """Decode and validate a message from JSON string."""

    if len(text) > 65536:
        raise ValueError("message too large")
    data = json.loads(text)
    validate_message(data)
    return data
