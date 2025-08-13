"""New game wizard placeholder."""

from __future__ import annotations

import pygame

from .scene_base import Scene


class NewGameScene(Scene):
    """Minimal stub used in tests.

    A full implementation with player setup lives in the complete project; the
    tests only verify that the menu can switch to this scene. The class extends
    :class:`Scene` so the application can safely call ``enter`` and ``exit``
    without raising ``AttributeError`` during manual runs.
    """

    def __init__(self, app) -> None:
        super().__init__(app)

    def handle_event(self, event: pygame.event.Event) -> None:  # pragma: no cover
        pass

    def update(self, dt: float) -> None:  # pragma: no cover
        pass

    def draw(self, surface: pygame.Surface) -> None:  # pragma: no cover
        surface.fill((0, 0, 0))


__all__ = ["NewGameScene"]

