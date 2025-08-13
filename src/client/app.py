"""Minimal pygame application wrapper.

This module bootstraps pygame, shows a system cursor and provides a tiny event
loop.  Scenes follow a very small interface: ``handle_event``, ``update`` and
``draw``.  Global exceptions are caught and rendered via ``ModalError`` so
tests can inspect the message rather than crashing outright.
"""

from __future__ import annotations

import logging
import traceback

import pygame

from gamecore.i18n import gettext as _

from .input_map import InputMap
from .scene_menu import MenuScene
from .ui.widgets import HelpOverlay, ModalError


class App:
    """Small pygame application managing a single scene."""

    def __init__(self, safe_mode: bool = False) -> None:
        pygame.init()
        pygame.font.init()
        pygame.mouse.set_visible(True)
        self.safe_mode = safe_mode
        self.screen = pygame.display.set_mode((640, 480))
        self.input_map = InputMap()
        self.scene = MenuScene(self)
        self.help = HelpOverlay(self.input_map)
        self.running = True

    # main loop ---------------------------------------------------------
    def run(self) -> None:
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                self.handle_event(event)
            self.scene.update(0.0)
            self.screen.fill((0, 0, 0))
            self.scene.draw(self.screen)
            if self.help.visible:
                self.help.draw(self.screen)
            pygame.display.flip()
            clock.tick(60)

    # event dispatch ----------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        action = self.input_map.map_event(event)
        if action == "help":
            self.help.toggle()
            return
        if action == "pause":
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return
        self.scene.handle_event(event)


def main(safe_mode: bool = False) -> None:
    """Entry point used by ``scripts.run_gui``."""

    try:
        App(safe_mode=safe_mode).run()
    except Exception:  # pragma: no cover - error handling
        logging.exception("app crash")
        pygame.init()
        pygame.font.init()
        screen = pygame.display.set_mode((640, 480))
        dialog = ModalError(_("error"), traceback.format_exc())
        dialog.run(screen)


__all__ = ["App", "main"]

