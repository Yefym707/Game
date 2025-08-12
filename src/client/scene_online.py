"""Menu scene for creating/joining online games."""
from __future__ import annotations

import asyncio

import pygame

from gamecore.config import load_config
from gamecore.i18n import gettext as _
from net.master_api import MasterMessage, encode_master_message, decode_master_message
from net.protocol import MessageType
from .app import Scene
from .net_client import NetClient

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

    def update(self, dt: float) -> None:
        asyncio.create_task(self._poll())

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 24)
        txt = font.render(self.status or _("Online"), True, (255, 255, 255))
        surface.blit(txt, (10, 10))
