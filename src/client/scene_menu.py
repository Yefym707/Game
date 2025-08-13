"""Main menu scene."""

from __future__ import annotations

import pygame

from gamecore import saveio
from gamecore.i18n import gettext as _

from .scene_base import Scene
from .ui.widgets import ModalConfirm


class MenuScene(Scene):
    """Simple keyboard/mouse driven main menu."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self.error_modal: ModalConfirm | None = None
        self._font = pygame.font.SysFont(None, 28)
        self.items: list[tuple[str, callable]] = [
            ("menu_new_game", self._new_game),
            ("menu_continue", self._continue),
            ("menu_load", self._load_scene),
            ("menu_settings", self._settings),
            ("menu_quit", self._quit),
        ]
        self.index = 0
        self._item_rects: list[pygame.Rect] = []

    # actions -----------------------------------------------------------
    def _new_game(self) -> None:
        from .scene_newgame import NewGameScene

        self.next_scene = NewGameScene(self.app)

    def _continue(self) -> None:
        slot = saveio.find_last_save()
        if slot is None or not saveio.validate(slot):
            self._no_save()
            return
        try:
            saveio.load(slot)
        except Exception:  # pragma: no cover - load errors treated uniformly
            self._no_save()
            return
        from .scene_game import GameScene

        self.next_scene = GameScene(self.app)

    def _load_scene(self) -> None:
        from .scene_load import LoadScene

        self.next_scene = LoadScene(self.app)

    def _settings(self) -> None:  # pragma: no cover - placeholder
        from .scene_settings import SettingsScene

        self.next_scene = SettingsScene(self.app)

    def _quit(self) -> None:
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _no_save(self) -> None:
        def _cb() -> None:
            self.error_modal = None
            self._new_game()

        self.error_modal = ModalConfirm(_("no_valid_save"), _cb)

    # scene interface ---------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if self.error_modal:
            self.error_modal.handle_event(event)
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.index = (self.index - 1) % len(self.items)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.index = (self.index + 1) % len(self.items)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.items[self.index][1]()
            elif event.key == pygame.K_ESCAPE:
                self._quit()
        elif event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self._item_rects):
                if rect.collidepoint(event.pos):
                    self.index = i
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self._item_rects):
                if rect.collidepoint(event.pos):
                    self.index = i
                    self.items[i][1]()
                    break

    def update(self, dt: float) -> None:  # pragma: no cover - nothing dynamic
        pass

    def draw(self, surface: pygame.Surface) -> None:  # pragma: no cover - visual
        surface.fill((0, 0, 0))
        if self.error_modal:
            self.error_modal.draw(surface)
            return
        w = surface.get_width()
        h = surface.get_height()
        self._item_rects.clear()
        start_y = h // 2 - len(self.items) * 20 // 2
        for i, (key, _cb) in enumerate(self.items):
            text = _(key)
            color = (255, 255, 0) if i == self.index else (255, 255, 255)
            img = self._font.render(text, True, color)
            rect = img.get_rect(center=(w // 2, start_y + i * 30))
            self._item_rects.append(rect)
            surface.blit(img, rect)
        hint = self._font.render(_("menu_hint"), True, (200, 200, 200))
        surface.blit(hint, (10, h - 40))


__all__ = ["MenuScene"]

