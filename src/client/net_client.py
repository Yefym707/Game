"""Async websocket client used by the pygame front-end."""
from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Iterable

try:  # pragma: no cover - optional dependency during tests
    import websockets
except Exception:  # pragma: no cover
    websockets = None  # type: ignore

from net.protocol import decode_message, encode_message, MessageType
from server.security import RateLimiter
from net.serialization import parse_invite_url as _parse_invite_url


class NetClient:
    """Thin wrapper around ``websockets`` with queues."""

    def __init__(self, reconnect_backoff: Iterable[int] | None = None) -> None:
        self.ws: "websockets.WebSocketClientProtocol | None" = None
        self.incoming: "asyncio.Queue[Dict[str, Any]]" = asyncio.Queue()
        self.outgoing: "asyncio.Queue[Dict[str, Any]]" = asyncio.Queue(maxsize=32)
        self._action_rl = RateLimiter(5, 1.0)
        self._ping_interval = 5.0
        self.rtt: float | None = None
        self._reconnect_backoff = list(reconnect_backoff or [1, 2, 5, 10])
        self._reconnect_attempt = 0
        self.last_invite: str = ""
        self.rejoin_token: str | None = None
        self.spectator = False

    async def connect(self, uri: str) -> None:
        if websockets is None:
            raise RuntimeError("websockets library not installed")
        delay = 1.0
        while True:
            try:
                self.ws = await websockets.connect(uri)
                break
            except Exception:
                await asyncio.sleep(delay)
                delay = min(delay * 2, 30)
        if self.rejoin_token:
            await self.ws.send(
                encode_message({"t": MessageType.REJOIN_REQ.value, "token": self.rejoin_token})
            )
        asyncio.create_task(self._reader())
        asyncio.create_task(self._writer())

    async def _reader(self) -> None:
        assert self.ws is not None
        async for raw in self.ws:
            try:
                msg = decode_message(raw)
            except Exception:
                continue
            if msg.get("t") == MessageType.PONG.value:
                sent = float(msg.get("p", 0.0))
                self.record_rtt(max(0.0, time.perf_counter() - sent))
                continue
            if msg.get("t") == MessageType.REJOIN_ACK.value:
                self.rejoin_token = msg.get("token", self.rejoin_token)
                continue
            await self.incoming.put(msg)

    async def _writer(self) -> None:
        assert self.ws is not None
        while True:
            msg = await self.outgoing.get()
            await self.ws.send(encode_message(msg))

    async def send(self, msg: Dict[str, Any]) -> None:
        if msg.get("t") == MessageType.ACTION.value:
            if not self._action_rl.hit():
                return  # drop spammy action
        try:
            self.outgoing.put_nowait(msg)
        except asyncio.QueueFull:
            # dropping messages prevents unbounded growth
            pass

    async def recv(self) -> Dict[str, Any]:
        return await self.incoming.get()

    # ping helpers -----------------------------------------------------
    async def ping_loop(self) -> None:
        """Send periodic ping messages to measure latency."""

        while True:
            await asyncio.sleep(self._ping_interval)
            if not self.ws:
                continue
            await self.send({"t": MessageType.PING.value, "p": time.perf_counter()})

    def record_rtt(self, rtt: float) -> float:
        """Record a round-trip time using simple smoothing."""

        if self.rtt is None:
            self.rtt = rtt
        else:
            self.rtt = (self.rtt + rtt) / 2.0
        return self.rtt

    # reconnect helpers -----------------------------------------------
    def next_backoff(self) -> int:
        """Return delay for the next reconnect attempt."""

        delay = self._reconnect_backoff[min(self._reconnect_attempt, len(self._reconnect_backoff) - 1)]
        self._reconnect_attempt += 1
        return delay

    def reset_backoff(self) -> None:
        """Reset reconnect attempt counter."""

        self._reconnect_attempt = 0

    def set_rejoin_token(self, token: str) -> None:
        self.rejoin_token = token

    def set_spectator(self, value: bool) -> None:
        self.spectator = value


def parse_invite_url(url: str) -> Dict[str, object]:
    """Parse invite URL into a payload dictionary."""

    return _parse_invite_url(url)


async def ping(uri: str, timeout: float = 5.0) -> float:
    """Return round-trip latency to ``uri`` in seconds."""

    if websockets is None:
        raise RuntimeError("websockets library not installed")
    start = time.perf_counter()
    async with websockets.connect(uri) as ws:
        await ws.send(encode_message({"t": MessageType.PING.value}))
        await asyncio.wait_for(ws.recv(), timeout=timeout)
    return time.perf_counter() - start
