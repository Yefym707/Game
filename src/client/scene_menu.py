"""Main menu scene."""

from __future__ import annotations

import pygame

from gamecore import saveio
from gamecore.i18n import gettext as _

from .scene_base import Scene
from .ui.widgets import ModalConfirm


class MenuScene(Scene):
    """Very small interactive main menu.

    The original project provided a blank scene that only exposed a ``_continue``
    helper for tests.  This implementation adds a minimal user facing menu so
    manual runs are not greeted by an empty window.
    """

    def __init__(self, app) -> None:
        super().__init__(app)
        self.error_modal: ModalConfirm | None = None
        self._font = pygame.font.SysFont(None, 28)

    # actions -----------------------------------------------------------
    def _new_game(self) -> None:
        from .scene_newgame import NewGameScene

        self.next_scene = NewGameScene(self.app)

    def _continue(self) -> None:
        slot = saveio.find_last_save()
        if slot is None:
            self._no_save()
            return
        try:
            saveio.load(slot)
        except Exception:  # pragma: no cover - load errors are handled the same
            self._no_save()
            return
        from .scene_game import GameScene

        self.next_scene = GameScene(self.app)

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
            if event.key == pygame.K_n:
                self._new_game()
            elif event.key == pygame.K_c:
                self._continue()
            elif event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update(self, dt: float) -> None:  # pragma: no cover - nothing to update
        pass

    def draw(self, surface: pygame.Surface) -> None:  # pragma: no cover - visual
        surface.fill((0, 0, 0))
        if self.error_modal:
            self.error_modal.draw(surface)
            return
        lines = [
            _("Press N to start a new game"),
            _("Press C to continue"),
            _("Press ESC to quit"),
        ]
        w = surface.get_width()
        h = surface.get_height()
        start_y = h // 2 - len(lines) * 20 // 2
        for i, text in enumerate(lines):
            img = self._font.render(text, True, (255, 255, 255))
            rect = img.get_rect(center=(w // 2, start_y + i * 30))
            surface.blit(img, rect)


__all__ = ["MenuScene"]

