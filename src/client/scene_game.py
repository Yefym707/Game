from __future__ import annotations

"""Minimal in game scene used for unit tests.

The original project contains a feature rich scene responsible for rendering,
input handling and networking.  Re‑creating that logic is unnecessary for the
unit tests that accompany this kata.  Instead we provide a compact stand‑in
that exposes the few attributes tests interact with: a ``state`` object, a
``camera`` and trivial ``draw``/``handle_event`` hooks.
"""

import pygame
from collections import deque
from typing import Deque, Tuple

from .gfx.camera import SmoothCamera
from .gfx.tileset import TILE_SIZE
from .ui.widgets import HelpOverlay, Toast
from gamecore import board as gboard, rules, validate

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
        self.selected = self.state.current
        self.toasts: list[Toast] = []
        self.queue: Deque[Tuple[str, tuple[int, int]]] = deque()

    # helpers -----------------------------------------------------------
    def cell_from_screen(self, pos: tuple[int, int]) -> tuple[int, int] | None:
        wx, wy = self.camera.screen_to_world(pos)
        cell = int(wx // TILE_SIZE), int(wy // TILE_SIZE)
        b = self.state.board
        if 0 <= cell[0] < b.width and 0 <= cell[1] < b.height:
            return cell
        return None

    def toast(self, text: str) -> None:
        self.toasts.append(Toast(text))

    # input --------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        action = self.app.input_map.map_event(event)
        if action == "help":
            self.help.toggle()
            return
        if action == "pause":  # pragma: no cover - minimal
            return
        if action == "end_turn":
            rules.end_turn(self.state)
            self.selected = self.state.current
            return
        if action == "select" and hasattr(event, "pos"):
            cell = self.cell_from_screen(event.pos)
            if cell:
                for p in self.state.players:
                    if (p.x, p.y) == cell:
                        self.selected = p
                        break
            return
        if action == "action" and hasattr(event, "pos"):
            cell = self.cell_from_screen(event.pos)
            if cell:
                self.queue.append(("action", cell))

    # processing ---------------------------------------------------------
    def update(self, dt: float) -> None:
        if self.queue:
            act, cell = self.queue.popleft()
            if act == "action" and self.selected is self.state.current:
                target = next((p for p in self.state.players if (p.x, p.y) == cell and p is not self.selected), None)
                if target:
                    ok, reason = rules.attack(self.state, target)
                else:
                    ok, reason = rules.move(self.state, cell)
                if not ok and reason:
                    self.toast(reason)

    def draw(self, surf: pygame.Surface) -> None:  # pragma: no cover - visual
        surf.fill((0, 0, 0))
        # draw toasts
        y = 10
        for t in self.toasts:
            t.draw(surf, y)
            y += 20


__all__ = ["GameScene", "hover_hints"]
