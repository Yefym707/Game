"""Main menu scene."""

from __future__ import annotations

import pygame

from gamecore import saveio
from gamecore.i18n import gettext as _

from .ui.widgets import ModalConfirm


class MenuScene:
    """Tiny menu used in tests.

    Only the logic for *Continue* is implemented.  The graphical representation
    is intentionally omitted to keep the module lightweight.
    """

    def __init__(self, app) -> None:
        self.app = app
        self.next_scene = None
        self.error_modal: ModalConfirm | None = None

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

    def update(self, dt: float) -> None:  # pragma: no cover - nothing to update
        pass

    def draw(self, surface: pygame.Surface) -> None:  # pragma: no cover
        surface.fill((0, 0, 0))


__all__ = ["MenuScene"]

