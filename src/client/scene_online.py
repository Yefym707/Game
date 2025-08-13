"""Menu scene for creating/joining online games."""
from __future__ import annotations

import asyncio
import time
from typing import Dict

import pygame

from gamecore.config import load_config
from gamecore.i18n import gettext as _
from net.master_api import MasterMessage, encode_master_message, decode_master_message
from net.protocol import MessageType
from .app import Scene
from .net_client import NetClient, parse_invite_url
from . import clipboard

try:  # pragma: no cover - optional dependency
    import websockets
except Exception:  # pragma: no cover
    websockets = None  # type: ignore


class OnlineScene(Scene):
    """Very small placeholder lobby UI with a simple server browser."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self.client = NetClient()
        cfg = load_config()
        self.address = cfg.get("server_address", "ws://localhost:8765")
        self.master_url = cfg.get("master_url", "ws://localhost:8080")
        self.name = "player"
        self.status = ""
        self.connected = False
        self.servers = []
        self.invite: str | None = None
        self.ready = False
        self.rtts: Dict[str, float] = {}
        self.allow_drop_in = False
        self.allow_spectators = False
        self.spectate = False

    async def _refresh(self) -> None:
        if websockets is None:
            self.status = "websockets missing"
            return
        try:
            async with websockets.connect(self.master_url) as ws:
                await ws.send(encode_master_message({"t": MasterMessage.LIST.value}))
                msg = decode_master_message(await ws.recv())
                self.servers = msg.get("servers", [])
                self.status = _("BROWSE")
        except Exception:
            self.status = _("DISCONNECTED")
            self.servers = []

    def handle_event(self, event: pygame.event.Event) -> None:  # pragma: no cover - UI stub
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                asyncio.create_task(self._refresh())
            if event.key == pygame.K_RETURN and not self.connected:
                asyncio.create_task(self.client.connect(self.address))
                self.status = _("CONNECT")
                self.connected = True
            if event.key == pygame.K_SPACE:
                self.ready = not self.ready
            if event.key == pygame.K_d:
                self.allow_drop_in = not self.allow_drop_in
            if event.key == pygame.K_s:
                self.allow_spectators = not self.allow_spectators
            if event.key == pygame.K_p and not self.connected:
                self.client.set_spectator(True)
                asyncio.create_task(self.client.connect(self.address))
                self.status = _("CONNECT")
                self.connected = True
                self.spectate = True

    async def _poll(self) -> None:
        if not self.connected:
            return
        try:
            msg = self.client.incoming.get_nowait()
        except asyncio.QueueEmpty:
            return
        if msg.get("t") == MessageType.ERROR.value:
            self.status = msg.get("p", "error")
        elif msg.get("t") == "KICK":
            self.status = _("DISCONNECTED")
            self.connected = False
        elif msg.get("t") == MessageType.PONG.value:
            self.client.record_rtt(max(0.0, time.perf_counter() - float(msg.get("p", 0))))

    def update(self, dt: float) -> None:
        asyncio.create_task(self._poll())

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 24)
        txt = font.render(self.status or _("Online"), True, (255, 255, 255))
        surface.blit(txt, (10, 10))

    # invite helpers ----------------------------------------------------
    async def create_invite(self) -> None:
        if not self.connected:
            return
        await self.client.send({"t": MessageType.INVITE_CREATE.value, "room": "1"})
        resp = await self.client.recv()
        if resp.get("t") == MessageType.INVITE_INFO.value:
            self.invite = resp.get("url")

    def copy_invite_link(self) -> None:
        if self.invite:
            clipboard.copy(self.invite)

    def join_from_invite(self, text: str) -> None:
        try:
            data = parse_invite_url(text)
        except Exception:
            return
        self.address = f"ws://{data['host']}:{data['port']}"
        asyncio.create_task(self.client.connect(self.address))
        self.connected = True
