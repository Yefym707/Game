"""Load game scene placeholder."""

from __future__ import annotations

import pygame


class LoadScene:
    """Minimal stub used for menu navigation tests."""

    def __init__(self, app) -> None:
        self.app = app
        self.next_scene = None

    def handle_event(self, event: pygame.event.Event) -> None:  # pragma: no cover
        pass

    def update(self, dt: float) -> None:  # pragma: no cover
        pass

    def draw(self, surface: pygame.Surface) -> None:  # pragma: no cover
        surface.fill((0, 0, 0))


__all__ = ["LoadScene"]

