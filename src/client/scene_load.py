"""Save slot selection scene."""

from __future__ import annotations

from typing import List

import pygame

from gamecore import saveio
from gamecore.i18n import gettext as _
from client.util_paths import user_data_dir

from .scene_base import Scene
from .ui.widgets import ModalConfirm


class LoadScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._font = pygame.font.SysFont(None, 24)
        self.slots: List[dict] = saveio.list_saves()
        self.index = 0
        self._rects: List[pygame.Rect] = []
        self.confirm: ModalConfirm | None = None

    # internal helpers --------------------------------------------------
    def _start_game(self, slot: int) -> None:
        try:
            saveio.load(slot)
        except Exception:
            return
        from .scene_game import GameScene

        self.next_scene = GameScene(self.app)

    def _delete(self, slot: int) -> None:
        path = user_data_dir() / "saves" / f"{slot}.json"
        try:
            path.unlink()
        except FileNotFoundError:  # pragma: no cover - defensive
            pass
        self.slots = saveio.list_saves()
        self.index = min(self.index, max(0, len(self.slots) - 1))

    # scene interface ---------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:  # pragma: no cover - simple
        if self.confirm:
            self.confirm.handle_event(event)
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.index = (self.index - 1) % max(1, len(self.slots))
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.index = (self.index + 1) % max(1, len(self.slots))
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.slots:
                    self._start_game(self.slots[self.index]["slot"])
            elif event.key == pygame.K_DELETE and self.slots:
                slot = self.slots[self.index]["slot"]

                def _cb() -> None:
                    self.confirm = None
                    self._delete(slot)

                self.confirm = ModalConfirm(_("load_delete_confirm"), _cb)
            elif event.key == pygame.K_ESCAPE:
                from .scene_menu import MenuScene

                self.next_scene = MenuScene(self.app)
        elif event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self._rects):
                if rect.collidepoint(event.pos):
                    self.index = i
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self._rects):
                if rect.collidepoint(event.pos) and self.slots:
                    self.index = i
                    self._start_game(self.slots[i]["slot"])
                    break

    def update(self, dt: float) -> None:  # pragma: no cover - nothing to update
        pass

    def draw(self, surface: pygame.Surface) -> None:  # pragma: no cover - visual
        surface.fill((0, 0, 0))
        if self.confirm:
            self.confirm.draw(surface)
            return
        self._rects.clear()
        w = surface.get_width()
        start_y = 100
        if not self.slots:
            text = _( "load_empty" )
            img = self._font.render(text, True, (200, 200, 200))
            rect = img.get_rect(center=(w // 2, start_y))
            surface.blit(img, rect)
            return
        for i, data in enumerate(self.slots):
            meta = data.get("meta", {})
            text = f"#{data['slot']} T{meta.get('turn', '?')} {meta.get('difficulty', '')} {meta.get('seed', '')}"
            color = (255, 255, 0) if i == self.index else (255, 255, 255)
            img = self._font.render(text, True, color)
            rect = img.get_rect(center=(w // 2, start_y + i * 30))
            self._rects.append(rect)
            surface.blit(img, rect)


__all__ = ["LoadScene"]

