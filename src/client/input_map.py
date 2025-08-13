"""Centralised input mapping."""

from __future__ import annotations

import pygame


class InputMap:
    """Translate pygame events into high level action strings."""

    def __init__(self) -> None:
        self._map: dict[tuple[str, int], str] = {
            ("mouse", 1): "select",
            ("mouse", 3): "move",
            ("key", pygame.K_SPACE): "end_turn",
            ("key", pygame.K_ESCAPE): "pause",
            ("key", pygame.K_F1): "help",
        }

    def map_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            return self._map.get(("mouse", event.button))
        if event.type == pygame.KEYDOWN:
            return self._map.get(("key", event.key))
        return None


__all__ = ["InputMap"]

