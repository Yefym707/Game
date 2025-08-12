"""Asyncio based authoritative server using websockets."""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict

try:  # pragma: no cover - optional during tests
    import websockets
except Exception:  # pragma: no cover
    websockets = None  # type: ignore

from net.protocol import decode_message, encode_message, MessageType
from net.serialization import parse_invite_url
from .invite import (
    create_invite,
    validate_invite,
    revoke_invite,
    refresh_invite,
)
from net.master_api import MasterMessage, encode_master_message, decode_master_message
from .lobby import LobbyManager
from .security import check_size, validate_master_payload, SessionGuard
from .banlist import BanList

log = logging.getLogger(__name__)


class Server:
    """Accept connections and dispatch messages."""

    def __init__(self, limits: Dict[str, int] | None = None) -> None:
        self.lobbies = LobbyManager()
        self.clients: Dict[websockets.WebSocketServerProtocol, str] = {}
        self.guards: Dict[websockets.WebSocketServerProtocol, SessionGuard] = {}
        self.limits = limits or {"actions_per_sec": 10, "bytes_per_min": 65536}
        self.bans = BanList()

    async def handler(self, websocket: "websockets.WebSocketServerProtocol") -> None:
        ip = getattr(websocket, "remote_address", ("", 0))[0]
        if self.bans.is_banned(str(ip)):
            await websocket.close()
            return
        self.clients[websocket] = ""
        self.guards[websocket] = SessionGuard(**self.limits)
        try:
            async for raw in websocket:
                check_size(raw)
                try:
                    self.guards[websocket].check(len(raw))
                except Exception as exc:
                    log.warning("rate limit: %s", exc)
                    await websocket.send(encode_message({"t": MessageType.ERROR.value, "p": str(exc)}))
                    continue
                try:
                    msg = decode_message(raw)
                except Exception as exc:
                    await websocket.send(encode_message({"t": MessageType.ERROR.value, "p": str(exc)}))
                    continue
                if msg["t"] == MessageType.PING.value:
                    await websocket.send(
                        encode_message({"t": MessageType.PONG.value, "p": msg.get("p")})
                    )
                elif msg["t"] == MessageType.INVITE_CREATE.value:
                    secret = os.environ.get("INVITE_SECRET")
                    if not secret:
                        await websocket.send(
                            encode_message({"t": MessageType.ERROR.value, "p": "invites disabled"})
                        )
                        continue
                    ttl = int(os.environ.get("INVITE_TTL", "1800"))
                    data = create_invite(self.host, self.port, msg.get("room", ""), secret.encode(), ttl)
                    await websocket.send(
                        encode_message({"t": MessageType.INVITE_INFO.value, **data})
                    )
                elif msg["t"] == MessageType.INVITE_JOIN.value:
                    secret = os.environ.get("INVITE_SECRET")
                    if not secret:
                        await websocket.send(
                            encode_message({"t": MessageType.ERROR.value, "p": "invites disabled"})
                        )
                        continue
                    data = msg.get("p", {})
                    if "url" in data:
                        data.update(parse_invite_url(data["url"]))
                    try:
                        validate_invite(data, secret.encode())
                        await websocket.send(
                            encode_message({"t": MessageType.STATE.value, "p": "joined"})
                        )
                    except Exception as exc:  # pragma: no cover - error paths
                        await websocket.send(
                            encode_message({"t": MessageType.ERROR.value, "p": str(exc)})
                        )
                elif msg["t"] == MessageType.INVITE_REVOKE.value:
                    code = str(msg.get("code", ""))
                    revoke_invite(code)
                    await websocket.send(
                        encode_message({"t": MessageType.INVITE_INFO.value, "p": "revoked"})
                    )
                elif msg["t"] == MessageType.INVITE_REFRESH.value:
                    secret = os.environ.get("INVITE_SECRET")
                    if not secret:
                        await websocket.send(
                            encode_message({"t": MessageType.ERROR.value, "p": "invites disabled"})
                        )
                        continue
                    ttl = int(os.environ.get("INVITE_TTL", "1800"))
                    data = refresh_invite(msg.get("p", {}), secret.encode(), ttl)
                    await websocket.send(
                        encode_message({"t": MessageType.INVITE_INFO.value, **data})
                    )
                else:
                    await websocket.send(encode_message({"t": MessageType.ERROR.value, "p": "unsupported"}))
        finally:
            self.clients.pop(websocket, None)
            self.guards.pop(websocket, None)

    # metadata used for master registration
    def lobby_payload(self) -> Dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "name": "Game Server",
            "mode": "default",
            "max_players": 4,
            "cur_players": len(self.clients),
            "region": "global",
            "build": "dev",
            "protocol": 1,
        }


async def _master_loop(server: Server, url: str) -> None:
    payload = server.lobby_payload()
    validate_master_payload(payload)
    async with websockets.connect(url) as ws:
        await ws.send(encode_master_message({"t": MasterMessage.REGISTER.value, **payload}))
        resp = decode_master_message(await ws.recv())
        server_id = resp.get("server_id")
        try:
            while True:
                await asyncio.sleep(15)
                hb = {"t": MasterMessage.HEARTBEAT.value, "server_id": server_id, "cur_players": len(server.clients)}
                await ws.send(encode_master_message(hb))
                await ws.recv()
        finally:
            try:
                await ws.send(encode_master_message({"t": MasterMessage.UNREGISTER.value, "server_id": server_id}))
            except Exception:
                pass


async def run(host: str = "0.0.0.0", port: int = 8765, master: str | None = None, limits: Dict[str, int] | None = None) -> None:
    if websockets is None:
        raise RuntimeError("websockets library not installed")
    server = Server(limits)
    server.host = host  # type: ignore[attr-defined]
    server.port = port  # type: ignore[attr-defined]
    tasks = []
    if master:
        tasks.append(asyncio.create_task(_master_loop(server, master)))
    async with websockets.serve(server.handler, host, port):
        await asyncio.Future()  # run forever
    for t in tasks:
        t.cancel()


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
