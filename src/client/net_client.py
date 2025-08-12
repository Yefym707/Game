"""Async websocket client used by the pygame front-end."""
from __future__ import annotations

import asyncio
import time
from typing import Any, Dict

try:  # pragma: no cover - optional dependency during tests
    import websockets
except Exception:  # pragma: no cover
    websockets = None  # type: ignore

from net.protocol import decode_message, encode_message, MessageType
from server.security import RateLimiter


class NetClient:
    """Thin wrapper around ``websockets`` with queues."""

    def __init__(self) -> None:
        self.ws: "websockets.WebSocketClientProtocol | None" = None
        self.incoming: "asyncio.Queue[Dict[str, Any]]" = asyncio.Queue()
        self.outgoing: "asyncio.Queue[Dict[str, Any]]" = asyncio.Queue(maxsize=32)
        self._action_rl = RateLimiter(5, 1.0)

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
        asyncio.create_task(self._reader())
        asyncio.create_task(self._writer())

    async def _reader(self) -> None:
        assert self.ws is not None
        async for raw in self.ws:
            try:
                msg = decode_message(raw)
            except Exception:
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

    async def ping(self, uri: str, timeout: float = 5.0) -> float:
        """Return round-trip latency to ``uri`` in seconds."""

        if websockets is None:
            raise RuntimeError("websockets library not installed")
        start = time.perf_counter()
        async with websockets.connect(uri) as ws:
            await ws.send(encode_message({"t": MessageType.PING.value}))
            await asyncio.wait_for(ws.recv(), timeout=timeout)
        return time.perf_counter() - start
