from __future__ import annotations

"""Utilities for hashing and signing data."""

import hashlib
import hmac
from pathlib import Path
from typing import Any


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hmac_sign(data: bytes, key: bytes) -> str:
    return hmac.new(key, data, hashlib.sha256).hexdigest()


def hmac_file(path: str | Path, key: bytes) -> str:
    with open(path, "rb") as fh:
        return hmac_sign(fh.read(), key)

__all__ = ["sha256", "hmac_sign", "hmac_file"]
