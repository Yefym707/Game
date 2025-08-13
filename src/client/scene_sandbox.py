"""Simple sandbox scene with a basic map editor."""
from __future__ import annotations

import pygame

from .scene_base import Scene
from .ui.widgets import Button, TilePalette, Toolbar
from .gfx.tileset import TILE_SIZE
from gamecore import board as gboard, saveio
from gamecore.i18n import gettext as _


class SandboxScene(Scene):
    """Very small tile based editor used for modding maps."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self.board = gboard.Board.generate(10, 10)
        self.palette = TilePalette([".", "#"], pygame.Rect(10, 10, 64, 32))
        self.toolbar = Toolbar(
            [
                Button(_("save_map"), pygame.Rect(10, 50, 110, 30), self._save),
                Button(_("load_map"), pygame.Rect(130, 50, 110, 30), self._load),
                Button(_("test_map"), pygame.Rect(250, 50, 110, 30), self._test),
            ]
        )
        self.offset_y = 100

    # button callbacks -------------------------------------------------
    def _save(self) -> None:
        saveio.export_map(self.board, "sandbox")

    def _load(self) -> None:
        try:
            self.board = saveio.import_map("sandbox")
        except FileNotFoundError:
            pass

    def _test(self) -> None:
        from .scene_game import GameScene

        self.next_scene = GameScene(self.app)

    # event handling ---------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        self.palette.handle_event(event)
        self.toolbar.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
            x = event.pos[0] // TILE_SIZE
            y = (event.pos[1] - self.offset_y) // TILE_SIZE
            if self.board.in_bounds(x, y):
                if event.button == 1:
                    self.board.tiles[y][x] = self.palette.selected
                else:
                    self.board.tiles[y][x] = "."

    def update(self, dt: float) -> None:
        pass

    # drawing ----------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        for y, row in enumerate(self.board.tiles):
            for x, tile in enumerate(row):
                color = (60, 60, 60) if tile == "." else (100, 100, 100)
                r = pygame.Rect(x * TILE_SIZE, self.offset_y + y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(surface, color, r)
                pygame.draw.rect(surface, (20, 20, 20), r, 1)
        self.palette.draw(surface)
        self.toolbar.draw(surface)
