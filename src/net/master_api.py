"""Message protocol for the master server.

The master server exchanges small JSON messages over websockets.  Each
message contains a ``t`` field with the message type.  The following types are
currently recognised:

``REGISTER``
    Sent by game servers to announce themselves.  Includes lobby metadata.
``UNREGISTER``
    Sent by game servers when shutting down.
``HEARTBEAT``
    Periodic keep-alive from game servers updating ``cur_players``.
``LIST``
    Request a list of registered servers.  Can include optional filters.
``PING``
    Round trip latency check.

The functions below mirror :mod:`net.protocol` but are intentionally self
contained so the master service can operate independently from the main game
protocol.
"""
from __future__ import annotations

import json
from enum import Enum
from typing import Any, Dict

PROTOCOL_VERSION = 1


class MasterMessage(str, Enum):
    """Supported master server message types."""

    REGISTER = "REGISTER"
    UNREGISTER = "UNREGISTER"
    HEARTBEAT = "HEARTBEAT"
    LIST = "LIST"
    PING = "PING"
    ERROR = "ERROR"


_ALLOWED_TYPES = {t.value for t in MasterMessage}
MAX_MASTER_MESSAGE_SIZE = 65536


def _validate(msg: Dict[str, Any]) -> None:
    if "t" not in msg:
        raise ValueError("missing 't' field")
    if msg["t"] not in _ALLOWED_TYPES:
        raise ValueError(f"unknown message type: {msg['t']}")
    if "v" in msg and msg["v"] != PROTOCOL_VERSION:
        raise ValueError("incompatible protocol version")


def encode_master_message(data: Dict[str, Any]) -> str:
    """Encode *data* as JSON string suitable for transmission."""

    payload = dict(data)
    payload.setdefault("v", PROTOCOL_VERSION)
    _validate(payload)
    return json.dumps(payload, separators=(",", ":"))


def decode_master_message(text: str) -> Dict[str, Any]:
    """Decode and validate JSON message from master connection."""

    if len(text) > MAX_MASTER_MESSAGE_SIZE:
        raise ValueError("message too large")
    data = json.loads(text)
    _validate(data)
    return data


__all__ = [
    "PROTOCOL_VERSION",
    "MasterMessage",
    "encode_master_message",
    "decode_master_message",
]
