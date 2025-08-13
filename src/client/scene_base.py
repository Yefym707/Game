"""Base scene class used by all game scenes."""
from __future__ import annotations

import pygame
from typing import Optional


class Scene:
    """Common base class for all scenes.

    Provides no functionality by default but defines the interface expected
    by :class:`App` and other scenes.
    """

    def __init__(self, app) -> None:
        """Store reference to the application instance."""
        self.app = app
        self.next_scene: Optional[Scene] = None

    def enter(self) -> None:  # pragma: no cover - interface stub
        """Called when the scene becomes active."""

    def exit(self) -> None:  # pragma: no cover - interface stub
        """Called when the scene is deactivated."""

    def handle_event(self, event: pygame.event.Event) -> None:  # pragma: no cover - interface stub
        """Handle a pygame event."""

    def update(self, dt: float) -> None:  # pragma: no cover - interface stub
        """Update scene logic."""

    def draw(self, screen: pygame.Surface) -> None:  # pragma: no cover - interface stub
        """Draw scene contents to ``screen``."""
