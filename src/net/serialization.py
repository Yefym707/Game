"""Helpers for serialising game state and invite tokens."""
from __future__ import annotations

import json
import secrets
from urllib.parse import urlencode, urlparse, parse_qs
from typing import Any, Dict


INVITE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ234567890"


def generate_invite_code(length: int = 8) -> str:
    """Return random invite code formatted as ``XXXX-YYYY``."""

    raw = "".join(secrets.choice(INVITE_ALPHABET) for _ in range(length))
    return f"{raw[:4]}-{raw[4:]}"


def build_invite_url(payload: Dict[str, object], sig: str) -> str:
    """Construct invite URL from payload and signature."""

    params = dict(payload)
    params["sig"] = sig
    return "oko://join?" + urlencode(params)


def parse_invite_url(text: str) -> Dict[str, object]:
    """Parse ``oko://`` invite URL into a payload dictionary."""

    if not text.startswith("oko://"):
        raise ValueError("invalid invite url")
    parts = urlparse(text)
    qs = parse_qs(parts.query)
    payload: Dict[str, object] = {
        "host": qs.get("host", [parts.hostname or ""])[0],
        "port": int(qs.get("port", [parts.port or 0])[0]),
        "room": qs.get("room", [""])[0],
        "code": qs.get("code", [""])[0],
        "exp": int(qs.get("exp", [0])[0]),
        "sig": qs.get("sig", [""])[0],
    }
    return payload


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


__all__ = [
    "serialize_state",
    "deserialize_state",
    "generate_invite_code",
    "build_invite_url",
    "parse_invite_url",
    "INVITE_ALPHABET",
]
