from __future__ import annotations

"""Utilities for hashing and signing data."""

import hashlib
import hmac
import time
from pathlib import Path
from typing import Dict


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hmac_sign(data: bytes, key: bytes) -> str:
    return hmac.new(key, data, hashlib.sha256).hexdigest()


def hmac_file(path: str | Path, key: bytes) -> str:
    with open(path, "rb") as fh:
        return hmac_sign(fh.read(), key)


def _invite_payload_str(payload: Dict[str, object]) -> bytes:
    host = str(payload.get("host", ""))
    port = int(payload.get("port", 0))
    room = str(payload.get("room", ""))
    exp = int(payload.get("exp", 0))
    code = str(payload.get("code", ""))
    text = f"{host}|{port}|{room}|{exp}|{code}"
    return text.encode("utf-8")


def sign_invite(payload: Dict[str, object], secret: bytes) -> str:
    """Return HMAC signature for an invite payload."""

    return hmac_sign(_invite_payload_str(payload), secret)


def verify_invite(payload: Dict[str, object], sig: str, secret: bytes) -> bool:
    """Validate invite HMAC and expiration.

    Raises :class:`ValueError` on failure.
    """

    expected = sign_invite(payload, secret)
    if not hmac.compare_digest(expected, sig):
        raise ValueError("invalid signature")
    exp = int(payload.get("exp", 0))
    if exp and exp < int(time.time()):
        raise ValueError("invite expired")
    return True

__all__ = [
    "sha256",
    "hmac_sign",
    "hmac_file",
    "sign_invite",
    "verify_invite",
]
