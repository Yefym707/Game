"""Menu scene for creating/joining online games."""
from __future__ import annotations

import asyncio

import pygame

from gamecore.i18n import gettext as _
from .app import Scene
from .net_client import NetClient


class OnlineScene(Scene):
    """Very small placeholder lobby UI.

    A real implementation would provide proper widgets.  For the purposes of
    automated tests we only expose a minimal textual interface via the log.
    """

    def __init__(self, app) -> None:
        super().__init__(app)
        self.client = NetClient()
        self.address = "ws://localhost:8765"
        self.name = "player"
        self.status = ""
        self.connected = False

    def handle_event(self, event: pygame.event.Event) -> None:  # pragma: no cover - UI stub
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and not self.connected:
            asyncio.create_task(self.client.connect(self.address))
            self.status = _("Connecting...")
            self.connected = True

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 24)
        txt = font.render(self.status or _("Online"), True, (255, 255, 255))
        surface.blit(txt, (10, 10))
