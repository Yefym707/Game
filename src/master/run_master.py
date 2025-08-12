"""Asyncio based master server."""
from __future__ import annotations

import asyncio
import json
import urllib.parse

try:  # pragma: no cover - optional dependency during tests
    import websockets
except Exception:  # pragma: no cover
    websockets = None  # type: ignore

from net.master_api import MasterMessage, decode_master_message, encode_master_message
from .registry import LobbyInfo, MasterRegistry
from .security import RateLimiter, check_size, verify_token


async def run_master(host: str = "0.0.0.0", port: int = 8080) -> None:
    """Run the master server indefinitely."""

    if websockets is None:
        raise RuntimeError("websockets library not installed")

    registry = MasterRegistry()
    limiter = RateLimiter()

    async def handler(ws: "websockets.WebSocketServerProtocol", path: str) -> None:
        ip = ws.remote_address[0] if ws.remote_address else "?"
        async for raw in ws:
            if not limiter.check(ip):
                await ws.close()
                break
            try:
                check_size(raw)
                msg = decode_master_message(raw)
            except Exception as exc:
                await ws.send(encode_master_message({"t": MasterMessage.ERROR.value, "p": str(exc)}))
                continue
            t = msg["t"]
            if t == MasterMessage.REGISTER.value:
                token = msg.get("token")
                if not verify_token(token):
                    await ws.send(encode_master_message({"t": MasterMessage.ERROR.value, "p": "unauthorised"}))
                    continue
                info = LobbyInfo(
                    host=msg["host"],
                    port=int(msg["port"]),
                    name=msg.get("name", ""),
                    mode=msg.get("mode", ""),
                    max_players=int(msg.get("max_players", 0)),
                    cur_players=int(msg.get("cur_players", 0)),
                    region=msg.get("region", ""),
                    build=msg.get("build", ""),
                    protocol=int(msg.get("protocol", 0)),
                )
                sid = registry.register(info)
                await ws.send(encode_master_message({"t": t, "server_id": sid}))
            elif t == MasterMessage.HEARTBEAT.value:
                sid = msg.get("server_id", "")
                try:
                    registry.heartbeat(sid, int(msg.get("cur_players", 0)))
                except KeyError:
                    await ws.send(encode_master_message({"t": MasterMessage.ERROR.value, "p": "unknown"}))
                else:
                    await ws.send(encode_master_message({"t": t}))
            elif t == MasterMessage.UNREGISTER.value:
                sid = msg.get("server_id", "")
                registry.unregister(sid)
                await ws.send(encode_master_message({"t": t}))
            elif t == MasterMessage.LIST.value:
                data = registry.list(
                    mode=msg.get("mode"),
                    region=msg.get("region"),
                    build=msg.get("build"),
                    limit=msg.get("limit"),
                )
                await ws.send(encode_master_message({"t": t, "servers": data}))
            elif t == MasterMessage.PING.value:
                await ws.send(encode_master_message({"t": "PONG"}))
            else:  # pragma: no cover - future types
                await ws.send(encode_master_message({"t": MasterMessage.ERROR.value, "p": "unsupported"}))

    async def process_request(path: str, request_headers):  # type: ignore[override]
        parsed = urllib.parse.urlparse(path)
        if parsed.path != "/list":
            return None
        params = urllib.parse.parse_qs(parsed.query)
        data = registry.list(
            mode=params.get("mode", [None])[0],
            region=params.get("region", [None])[0],
            build=params.get("build", [None])[0],
            limit=int(params.get("limit", ["0"])[0]) or None,
        )
        payload = json.dumps(data).encode("utf-8")
        headers = [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(payload))),
        ]
        return (200, headers, payload)

    async with websockets.serve(handler, host, port, process_request=process_request):
        await asyncio.Future()


__all__ = ["run_master"]
