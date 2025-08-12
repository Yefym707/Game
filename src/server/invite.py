from __future__ import annotations

"""Invite token generation and validation."""

import os
import time
from typing import Dict, Set

from net.attestation import sign_invite, verify_invite
from net.serialization import generate_invite_code, build_invite_url


def create_invite(host: str, port: int, room: str, secret: bytes, ttl: int) -> Dict[str, object]:
    """Create invite payload and signature.

    Parameters
    ----------
    host, port, room:
        Identify the server lobby.
    secret:
        HMAC secret used for signing.
    ttl:
        Time-to-live in seconds.
    """

    code = generate_invite_code()
    exp = int(time.time()) + ttl
    payload = {"host": host, "port": port, "room": room, "exp": exp, "code": code}
    sig = sign_invite(payload, secret)
    url = build_invite_url(payload, sig)
    _ACTIVE_SIGS[code] = sig
    return {"host": host, "port": port, "room": room, "code": code, "url": url, "exp": exp, "sig": sig}


_REVOKED: Set[str] = set()
_ACTIVE_SIGS: Dict[str, str] = {}


def revoke_invite(code: str) -> None:
    """Mark ``code`` as revoked."""

    _REVOKED.add(code)
    _ACTIVE_SIGS.pop(code, None)


def refresh_invite(invite: Dict[str, object], secret: bytes, ttl: int) -> Dict[str, object]:
    """Return new expiration/signature for existing ``invite``."""

    code = str(invite.get("code"))
    host = str(invite.get("host"))
    port = int(invite.get("port", 0))
    room = str(invite.get("room"))
    exp = int(time.time()) + ttl
    payload = {"host": host, "port": port, "room": room, "exp": exp, "code": code}
    sig = sign_invite(payload, secret)
    url = build_invite_url(payload, sig)
    invite.update({"exp": exp, "sig": sig, "url": url})
    _ACTIVE_SIGS[code] = sig
    return invite


def validate_invite(data: Dict[str, object], secret: bytes) -> bool:
    """Validate invite payload with signature and expiration."""

    code = str(data.get("code", ""))
    sig = str(data.get("sig", ""))
    if code in _REVOKED:
        return False
    current = _ACTIVE_SIGS.get(code)
    if current is not None and sig != current:
        return False
    payload = {k: data.get(k) for k in ("host", "port", "room", "exp", "code")}
    return verify_invite(payload, sig, secret)


__all__ = [
    "create_invite",
    "validate_invite",
    "revoke_invite",
    "refresh_invite",
]
