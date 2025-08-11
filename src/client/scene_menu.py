"""Main menu scene."""
from __future__ import annotations

import pygame

from gamecore.i18n import gettext as _
from .app import Scene
from .ui.widgets import Button


class MenuScene(Scene):
    """Simple menu with several actions."""

    def __init__(self, app):
        super().__init__(app)
        width, height = app.screen.get_size()
        cx = width // 2 - 100
        y = 150
        self.buttons = []

        def add(text: str, cb) -> None:
            nonlocal y
            rect = pygame.Rect(cx, y, 200, 40)
            self.buttons.append(Button(text, rect, cb))
            y += 60

        add(_("menu_new_game"), self.start_new)
        add(_("menu_continue"), self.continue_game)
        add(_("menu_settings"), self.settings)
        add(_("menu_quit"), self.quit)

    # button callbacks -------------------------------------------------
    def start_new(self) -> None:
        from .scene_game import GameScene

        self.next_scene = GameScene(self.app, new_game=True)

    def continue_game(self) -> None:
        from .scene_game import GameScene

        self.next_scene = GameScene(self.app, new_game=False)

    def settings(self) -> None:  # pragma: no cover - placeholder
        """Settings placeholder."""

    def quit(self) -> None:
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    # scene API --------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        for btn in self.buttons:
            btn.handle_event(event)

    def update(self, dt: float) -> None:  # pragma: no cover - nothing to update
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((20, 20, 20))
        for btn in self.buttons:
            btn.draw(surface)
