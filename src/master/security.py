"""Simple security helpers for the master server."""
from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from typing import Deque, Dict

MAX_MESSAGE_SIZE = 65536
RATE_LIMIT = 30  # max requests per IP per minute
TOKEN_ENV = "MASTER_TOKEN"


def check_size(text: str) -> None:
    if len(text) > MAX_MESSAGE_SIZE:
        raise ValueError("message too large")


class RateLimiter:
    """Naive sliding window rate limiter keyed by IP."""

    def __init__(self, limit: int = RATE_LIMIT, window: float = 60.0) -> None:
        self.limit = limit
        self.window = window
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def check(self, ip: str) -> bool:
        now = time.time()
        q = self._hits[ip]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True


def verify_token(token: str | None) -> bool:
    expected = os.getenv(TOKEN_ENV)
    if expected is None:
        return True
    return token == expected


__all__ = ["check_size", "RateLimiter", "verify_token"]
