from __future__ import annotations

"""Minimal in game scene used for unit tests.

The original project contains a feature rich scene responsible for rendering,
input handling and networking.  Re‑creating that logic is unnecessary for the
unit tests that accompany this kata.  Instead we provide a compact stand‑in
that exposes the few attributes tests interact with: a ``state`` object, a
``camera`` and trivial ``draw``/``handle_event`` hooks.
"""

import pygame

from .gfx.camera import SmoothCamera
from .gfx.tileset import TILE_SIZE
from .ui.widgets import HelpOverlay
from gamecore import board as gboard, rules

hover_hints = []  # tests patch this with translated help strings


class GameScene:
    def __init__(self, app, new_game: bool = True) -> None:
        self.app = app
        self.state = gboard.create_game(players=2)
        rules.start_turn(self.state)
        b = self.state.board
        self.camera = SmoothCamera(
            (app.screen.get_width(), app.screen.get_height()),
            (b.width * TILE_SIZE, b.height * TILE_SIZE),
        )
        self.help = HelpOverlay(app.input_map)

    # the real scene is interactive.  For tests we only need stubs -------------
    def handle_event(self, event: pygame.event.Event) -> None:  # pragma: no cover - trivial
        pass

    def update(self, dt: float) -> None:  # pragma: no cover - trivial
        pass

    def draw(self, surf: pygame.Surface) -> None:  # pragma: no cover - visual
        surf.fill((0, 0, 0))


__all__ = ["GameScene", "hover_hints"]
