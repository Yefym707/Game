"""Helpers for limiting abusive clients and validating master payloads."""
from __future__ import annotations

import collections
import time
from typing import Any, Dict, Deque, Tuple

MAX_MESSAGE_SIZE = 65536


class RateLimiter:
    """Simple sliding window rate limiter."""

    def __init__(self, limit: int, interval: float) -> None:
        self.limit = limit
        self.interval = interval
        self.events: Deque[Tuple[float, int]] = collections.deque()

    def hit(self, weight: int = 1) -> bool:
        now = time.time()
        while self.events and self.events[0][0] <= now - self.interval:
            self.events.popleft()
        total = sum(v for _, v in self.events)
        if total + weight > self.limit:
            return False
        self.events.append((now, weight))
        return True


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


class SessionGuard:
    """Per session/IP flood protection."""

    def __init__(self, *, actions_per_sec: int = 10, bytes_per_min: int = 65536, pings_per_sec: int = 5) -> None:
        self.action_rl = RateLimiter(actions_per_sec, 1.0)
        self.byte_rl = RateLimiter(bytes_per_min, 60.0)
        self.ping_rl = RateLimiter(pings_per_sec, 1.0)

    def check(self, size: int = 0) -> None:
        if not self.action_rl.hit():
            raise ValueError("rate limit exceeded")
        if size and not self.byte_rl.hit(size):
            raise ValueError("traffic limit exceeded")

    def check_ping(self) -> None:
        """Guard against excessive ping messages."""

        if not self.ping_rl.hit():
            raise ValueError("ping limit exceeded")


class InviteLimiter:
    """Track invite creation per IP."""

    def __init__(self, limit: int = 5, interval: float = 60.0) -> None:
        self.limit = limit
        self.interval = interval
        self._by_ip: Dict[str, RateLimiter] = {}

    def hit(self, ip: str) -> bool:
        rl = self._by_ip.setdefault(ip, RateLimiter(self.limit, self.interval))
        return rl.hit()


__all__ = [
    "check_size",
    "validate_master_payload",
    "RateLimiter",
    "SessionGuard",
    "InviteLimiter",
]
