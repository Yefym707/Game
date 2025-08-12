from __future__ import annotations

"""Invite token generation and validation."""

import os
import time
from typing import Dict

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
    return {"code": code, "url": url, "exp": exp, "sig": sig}


def validate_invite(data: Dict[str, object], secret: bytes) -> bool:
    """Validate invite payload with signature and expiration."""

    payload = {k: data.get(k) for k in ("host", "port", "room", "exp", "code")}
    sig = str(data.get("sig", ""))
    return verify_invite(payload, sig, secret)


__all__ = ["create_invite", "validate_invite"]
