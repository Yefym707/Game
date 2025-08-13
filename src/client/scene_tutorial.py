from __future__ import annotations

"""Minimal first-run tutorial scene.

The tutorial is intentionally tiny: it simply cycles through a few messages and
once finished starts a new game.  Its main purpose in this project is to flip
the ``first_run`` flag in the configuration so that subsequent launches skip
it.
"""

import pygame

from gamecore import config as gconfig
from gamecore.i18n import gettext as _
from .scene_base import Scene


class TutorialScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.cfg = app.cfg
        self.font = pygame.font.SysFont(None, 28)
        self.step = 0
        self.messages = [_("tut_step1"), _("tut_step2"), _("tut_step3")]

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self.step += 1
            if self.step >= len(self.messages):
                self.cfg["first_run"] = False
                gconfig.save_config(self.cfg)
                from .scene_game import GameScene

                self.next_scene = GameScene(self.app, new_game=True)

    def update(self, dt: float) -> None:  # pragma: no cover
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        msg = self.messages[min(self.step, len(self.messages) - 1)]
        img = self.font.render(msg, True, (255, 255, 255))
        surface.blit(img, (40, 40))
