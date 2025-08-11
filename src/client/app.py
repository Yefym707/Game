"""Main pygame application and scene manager."""
from __future__ import annotations

import pygame
from typing import Optional

from gamecore.i18n import gettext as _
from gamecore import config as gconfig


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
        cfg = gconfig.load_config()
        flags = pygame.FULLSCREEN if cfg.get("fullscreen") else 0
        w, h = cfg.get("window_size", [width, height])
        pygame.display.set_caption(_("window_title"))
        self.screen = pygame.display.set_mode((w, h), flags)
        try:
            pygame.mixer.music.set_volume(cfg.get("volume", 1.0))
        except Exception:  # pragma: no cover - mixer may not be init
            pass
        self.clock = pygame.time.Clock()
        from .scene_menu import MenuScene

        self.scene: Scene = MenuScene(self)

    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                self.scene.handle_event(event)
            self.scene.update(dt)
            self.scene.draw(self.screen)
            pygame.display.flip()
            if self.scene.next_scene:
                self.scene = self.scene.next_scene
        pygame.quit()


def main() -> None:
    """Entry point used by scripts.run_gui."""

    App().run()


if __name__ == "__main__":  # pragma: no cover
    main()
