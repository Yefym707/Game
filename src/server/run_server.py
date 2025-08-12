"""Asyncio based authoritative server using websockets."""
from __future__ import annotations

import asyncio
from typing import Any, Dict

try:  # pragma: no cover - optional during tests
    import websockets
except Exception:  # pragma: no cover
    websockets = None  # type: ignore

from net.protocol import decode_message, encode_message, MessageType
from .lobby import LobbyManager
from .security import check_size


class Server:
    """Accept connections and dispatch messages."""

    def __init__(self) -> None:
        self.lobbies = LobbyManager()
        self.clients: Dict[websockets.WebSocketServerProtocol, str] = {}

    async def handler(self, websocket: "websockets.WebSocketServerProtocol") -> None:
        self.clients[websocket] = ""
        try:
            async for raw in websocket:
                check_size(raw)
                try:
                    msg = decode_message(raw)
                except Exception as exc:
                    await websocket.send(encode_message({"t": MessageType.ERROR.value, "p": str(exc)}))
                    continue
                if msg["t"] == MessageType.PING.value:
                    await websocket.send(encode_message({"t": "PONG"}))
                else:
                    # Server does not yet implement full game logic; placeholder
                    await websocket.send(encode_message({"t": MessageType.ERROR.value, "p": "unsupported"}))
        finally:
            self.clients.pop(websocket, None)


async def run(host: str = "0.0.0.0", port: int = 8765) -> None:
    if websockets is None:
        raise RuntimeError("websockets library not installed")
    server = Server()
    async with websockets.serve(server.handler, host, port):
        await asyncio.Future()  # run forever


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(run())
