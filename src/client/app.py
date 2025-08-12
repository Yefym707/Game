"""Main pygame application and scene manager."""
from __future__ import annotations

import pygame
from typing import Optional

from gamecore.i18n import gettext as _
from gamecore import config as gconfig
from telemetry import init as telemetry_init, shutdown as telemetry_shutdown
from . import input as cinput
from .gfx.anim import FadeTransition
from .sfx import set_volume
from .scene_replay import ReplayScene  # imported for routing; used by menu


class Scene:
    """Base class for scenes."""

    def __init__(self, app: "App") -> None:
        self.app = app
        self.next_scene: Optional[Scene] = None

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle pygame events."""

    def update(self, dt: float) -> None:
        """Update scene state."""

    def draw(self, surface: pygame.Surface) -> None:
        """Draw scene to the surface."""


class App:
    """Pygame application managing scenes."""

    def __init__(self, width: int = 800, height: int = 600) -> None:
        pygame.init()
        # configuration -------------------------------------------------
        self.cfg = gconfig.load_config()
        telemetry_init(self.cfg)
        flags = pygame.FULLSCREEN if self.cfg.get("fullscreen") else 0
        w, h = self.cfg.get("window_size", [width, height])
        pygame.display.set_caption(_("window_title"))
        self.screen = pygame.display.set_mode((w, h), flags)
        set_volume(self.cfg.get("volume", 1.0))
        # unified input layer
        self.input = cinput.InputManager(self.cfg)
        self.clock = pygame.time.Clock()
        from .scene_menu import MenuScene

        self.scene: Scene = MenuScene(self)
        self.transition: FadeTransition | None = None

    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                if not self.transition:
                    self.scene.handle_event(event)
            if self.transition:
                self.transition.update(dt)
            else:
                self.scene.update(dt)
                if self.scene.next_scene:
                    self.transition = FadeTransition(self, self.scene.next_scene)
                    self.scene.next_scene = None
            self.scene.draw(self.screen)
            if self.transition:
                self.transition.draw(self.screen)
                if self.transition.finished:
                    self.transition = None
            pygame.display.flip()
        pygame.quit()
        telemetry_shutdown("quit")


def main(demo: bool = False) -> None:
    """Entry point used by ``scripts.run_gui``.

    Parameters
    ----------
    demo:
        When ``True`` the game runs in limited demo mode and corresponding
        restrictions are enabled.
    """

    if demo:
        from gamecore import rules

        rules.DEMO_MODE = True
    App().run()


if __name__ == "__main__":  # pragma: no cover
    main()
