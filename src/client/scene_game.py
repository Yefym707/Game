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
from typing import Deque, Tuple, Optional, List

from .gfx.camera import SmoothCamera
from .gfx.tileset import TILE_SIZE
from .gfx.anim import float_text, screen_shake
from .ui.widgets import HelpOverlay, Toast, MinimapWidget
from .ui.theme import get_theme
from gamecore import board as gboard, rules, validate
from gamecore.i18n import safe_get

hover_hints = []  # tests patch this with translated help strings


class GameScene:
    def __init__(self, app, new_game: bool = True, level_data: Optional[List[str]] = None) -> None:
        self.app = app
        self.level_data = level_data
        self.help = HelpOverlay(app.input_map)
        self.toasts: list[Toast] = []
        self.floaties: list = []
        self.queue: Deque[Tuple[str, tuple[int, int]]] = deque()
        self.preview_path: list[tuple[int, int]] = []
        self.font = pygame.font.SysFont(None, 16)
        self._init_world()

    def _init_world(self) -> None:
        if self.level_data:
            height = len(self.level_data)
            width = len(self.level_data[0]) if height else 0
            self.state = gboard.create_game(width=width, height=height, players=2)
            self.state.board.tiles = [list(row) for row in self.level_data]
        else:
            self.state = gboard.create_game(width=10, height=10, players=2)
        self.state.active = 0
        rules.start_turn(self.state)
        b = self.state.board
        self.camera = SmoothCamera(
            (self.app.screen.get_width(), self.app.screen.get_height()),
            (b.width * TILE_SIZE, b.height * TILE_SIZE),
        )
        self.camera.jump_to((b.width * TILE_SIZE // 2, b.height * TILE_SIZE // 2))
        b.players = self.state.players  # type: ignore[attr-defined]
        self.selected = self.state.current
        self.board_surf = pygame.Surface((b.width * TILE_SIZE, b.height * TILE_SIZE))
        light = (180, 180, 180)
        dark = (50, 50, 50)
        grid = (80, 80, 80)
        for y, row in enumerate(b.tiles):
            for x, ch in enumerate(row):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                self.board_surf.fill(dark if ch == "#" else light, rect)
                pygame.draw.rect(self.board_surf, grid, rect, 1)
        mm_rect = pygame.Rect(self.app.screen.get_width() - 90, 10, 80, 80)
        self.minimap = MinimapWidget(mm_rect, b, self.camera)
        self.queue.clear()
        self.preview_path = []
        self.toasts.clear()
        self.floaties.clear()

    def enter(self) -> None:
        self._init_world()

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
        self.minimap.handle_event(event)
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
                self.preview_path = self.state.board.find_path((self.selected.x, self.selected.y), cell)
                self.queue.append(("action", cell))

    # processing ---------------------------------------------------------
    def update(self, dt: float) -> None:
        if self.queue:
            act, cell = self.queue.popleft()
            if act == "action" and self.selected is self.state.current:
                target = next(
                    (p for p in self.state.players if (p.x, p.y) == cell and p is not self.selected),
                    None,
                )
                if target:
                    ok, reason = rules.attack(self.state, target)
                    if ok:
                        sx, sy = self.camera.world_to_screen(
                            (target.x * TILE_SIZE, target.y * TILE_SIZE)
                        )
                        self.floaties.append(float_text("-3", (sx, sy)))
                        screen_shake(self.camera, 1.0, 0.2)
                else:
                    ok, reason = rules.move(self.state, cell)
                if not ok and reason:
                    self.toast(reason)
                self.preview_path = []
        for ft in list(self.floaties):
            ft.update(dt)
            if ft.alpha <= 0:
                self.floaties.remove(ft)

    def draw(self, surf: pygame.Surface) -> None:  # pragma: no cover - visual
        theme = get_theme()
        surf.fill(theme.colors["bg"])
        # board
        view = pygame.Rect(int(self.camera.x), int(self.camera.y), self.camera.screen_w, self.camera.screen_h)
        surf.blit(self.board_surf, (0, 0), view)
        # units
        for p in self.state.players:
            cx, cy = self.camera.world_to_screen((p.x * TILE_SIZE + TILE_SIZE // 2, p.y * TILE_SIZE + TILE_SIZE // 2))
            pygame.draw.circle(surf, theme.palette["ui"].accent, (cx, cy), TILE_SIZE // 4)
            if p is self.selected:
                rect = pygame.Rect(
                    self.camera.world_to_screen((p.x * TILE_SIZE, p.y * TILE_SIZE)),
                    (TILE_SIZE, TILE_SIZE),
                )
                pygame.draw.rect(surf, theme.palette["ui"].neutral, rect, theme.border_xs)
                pygame.draw.rect(surf, theme.palette["ui"].accent, rect.inflate(-4, -4), theme.border_xs)
        # path preview
        if len(self.preview_path) > 1:
            pts = [
                self.camera.world_to_screen(
                    (x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2)
                )
                for x, y in self.preview_path
            ]
            pygame.draw.lines(surf, theme.palette["ui"].info, False, pts, theme.border_xs)
            lx, ly = pts[-1]
            pygame.draw.polygon(
                surf,
                theme.palette["ui"].info,
                [(lx, ly - 5), (lx - 4, ly + 4), (lx + 4, ly + 4)],
            )
        # float texts
        for ft in self.floaties:
            ft.draw(surf)
        # HUD stats
        hp_txt = f"{safe_get('hp')}: {self.selected.health}"
        ap = getattr(self.selected, 'ap', 0)
        ap_txt = f"{safe_get('ap')}: {ap}"
        img = self.font.render(hp_txt, True, theme.colors["text"])
        surf.blit(img, (10, surf.get_height() - 40))
        img = self.font.render(ap_txt, True, theme.colors["text"])
        surf.blit(img, (10, surf.get_height() - 20))
        # event log panel
        log_x = surf.get_width() - 150
        log_rect = pygame.Rect(log_x - 10, 10, 140, 100)
        pygame.draw.rect(surf, theme.colors["panel"], log_rect)
        pygame.draw.rect(surf, theme.colors["border"], log_rect, theme.border_xs)
        y = log_rect.y + theme.padding
        for ev in self.state.log[-5:]:
            key = f"log_{ev.lower().replace(' ', '_')}"
            text = safe_get(key)
            img = self.font.render(text, True, theme.colors["text"])
            surf.blit(img, (log_rect.x + theme.padding, y))
            y += img.get_height() + 2
        # minimap & help
        self.minimap.draw(surf)
        self.help.draw(surf)
        # toasts
        y = 10
        for t in self.toasts:
            t.draw(surf, y)
            y += 20


__all__ = ["GameScene", "hover_hints"]
