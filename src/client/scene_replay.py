"""Placeholder replay scene used to play recorded matches."""
from __future__ import annotations

import pygame
from pathlib import Path

from .app import Scene
from gamecore.i18n import gettext as _
from replay import player as replay_player


class ReplayScene(Scene):
    """Very small stub for replay playback."""

    def __init__(self, app, path: str | Path) -> None:
        super().__init__(app)
        self.player = replay_player.Player.load(path)
        self.playing = False
        self.rate = 1.0

    def handle_event(self, event: pygame.event.Event) -> None:
        pass  # CONTINUE

    def update(self, dt: float) -> None:
        pass  # CONTINUE

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        # CONTINUE
