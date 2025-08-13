"""Main menu scene with basic navigation."""
from __future__ import annotations

import pygame

from gamecore import saveio
from gamecore.i18n import gettext as _
from .scene_base import Scene
from .ui.widgets import Button, ModalConfirm


class MenuScene(Scene):
    """Display entry points into the game."""

    def __init__(self, app) -> None:
        super().__init__(app)
        w, h = app.screen.get_size()
        bw, bh = 200, 40
        cx = w // 2 - bw // 2
        cy = h // 2 - 100
        self.new_btn = Button(_("menu_new_game"), pygame.Rect(cx, cy, bw, bh), self._new_game)
        self.cont_btn = Button(_("menu_continue"), pygame.Rect(cx, cy + 50, bw, bh), self._continue)
        self.load_btn = Button(_("menu_load"), pygame.Rect(cx, cy + 100, bw, bh), self._load)
        self.settings_btn = Button(_("menu_settings"), pygame.Rect(cx, cy + 150, bw, bh), self._settings)
        self.quit_btn = Button(_("menu_quit"), pygame.Rect(cx, cy + 200, bw, bh), self._quit)
        self.focusables = [
            self.new_btn,
            self.cont_btn,
            self.load_btn,
            self.settings_btn,
            self.quit_btn,
        ]
        self.focus_idx = 0
        self.focusables[0].focus = True
        self.error_modal: ModalConfirm | None = None

    # button callbacks -------------------------------------------------
    def _new_game(self) -> None:
        from .scene_newgame import NewGameScene

        self.next_scene = NewGameScene(self.app)

    def _load(self) -> None:
        from .scene_load import LoadScene

        self.next_scene = LoadScene(self.app)

    def _settings(self) -> None:
        from .scene_settings import SettingsScene

        self.next_scene = SettingsScene(self.app)

    def _quit(self) -> None:
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _continue(self) -> None:
        slot = saveio.last_slot()
        if slot is None:
            self._no_save()
            return
        try:
            saveio.load(slot)
        except Exception:
            self._no_save()
            return
        from .scene_game import GameScene

        self.next_scene = GameScene(self.app, new_game=False)

    def _no_save(self) -> None:
        w, h = self.app.screen.get_size()
        rect = pygame.Rect(w // 2 - 150, h // 2 - 75, 300, 150)

        def _cb() -> None:
            self.error_modal = None
            from .scene_newgame import NewGameScene

            self.next_scene = NewGameScene(self.app)

        self.error_modal = ModalConfirm(rect, _("no_save_found"), _cb)

    # event handling ---------------------------------------------------
    def _move_focus(self, step: int) -> None:
        self.focusables[self.focus_idx].focus = False
        self.focus_idx = (self.focus_idx + step) % len(self.focusables)
        self.focusables[self.focus_idx].focus = True

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.error_modal:
            self.error_modal.handle_event(event)
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_TAB):
                self._move_focus(1)
            elif event.key == pygame.K_UP:
                self._move_focus(-1)
        for b in self.focusables:
            b.handle_event(event)

    # update / draw ----------------------------------------------------
    def update(self, dt: float) -> None:
        if self.error_modal:
            self.error_modal.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        for b in self.focusables:
            b.draw(surface)
        if self.error_modal:
            self.error_modal.draw(surface)

