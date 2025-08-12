"""Async websocket client used by the pygame front-end."""
from __future__ import annotations

import asyncio
from typing import Any, Dict

try:  # pragma: no cover - optional dependency during tests
    import websockets
except Exception:  # pragma: no cover
    websockets = None  # type: ignore

from net.protocol import decode_message, encode_message


class NetClient:
    """Thin wrapper around ``websockets`` with queues."""

    def __init__(self) -> None:
        self.ws: "websockets.WebSocketClientProtocol | None" = None
        self.incoming: "asyncio.Queue[Dict[str, Any]]" = asyncio.Queue()
        self.outgoing: "asyncio.Queue[Dict[str, Any]]" = asyncio.Queue()

    async def connect(self, uri: str) -> None:
        if websockets is None:
            raise RuntimeError("websockets library not installed")
        self.ws = await websockets.connect(uri)
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
        await self.outgoing.put(msg)

    async def recv(self) -> Dict[str, Any]:
        return await self.incoming.get()
