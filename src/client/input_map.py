"""Centralised input mapping and key binding management."""

from __future__ import annotations

import pygame


class InputMap:
    """Translate pygame events into high level action strings."""

    def __init__(self) -> None:
        """Create the input map and disable key repeat."""

        pygame.key.set_repeat()  # disable key repeat – actions fire once
        self._map: dict[tuple[str, int], str] = {
            ("mouse", 1): "select",  # left mouse button
            ("mouse", 3): "action",  # right mouse button – move/attack
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


class InputManager:
    """Store and manage action → key bindings."""

    def __init__(self, keybinds: dict[str, int] | None = None) -> None:
        self._binds = keybinds or self.default_keybinds()

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @staticmethod
    def default_keybinds() -> dict[str, int]:
        """Return default bindings using common WASD controls."""

        return {
            "move_up": pygame.K_w,
            "move_down": pygame.K_s,
            "move_left": pygame.K_a,
            "move_right": pygame.K_d,
            "end_turn": pygame.K_SPACE,
            "rest": pygame.K_r,
            "scavenge": pygame.K_g,
            "pause": pygame.K_ESCAPE,
        }

    def get(self, action: str) -> int:
        """Return the key bound to ``action``."""

        return self._binds[action]

    def set(self, action: str, key: int) -> None:
        """Bind ``action`` to ``key``."""

        self._binds[action] = int(key)

    def to_config(self) -> dict[str, int]:
        """Return bindings in a serialisable form."""

        return dict(self._binds)

    @classmethod
    def from_config(cls, cfg: dict[str, int] | None) -> "InputManager":
        """Create manager from ``cfg`` using defaults for missing keys."""

        if not isinstance(cfg, dict):
            return cls(cls.default_keybinds())
        defaults = cls.default_keybinds()
        for action, key in cfg.items():
            if action in defaults and isinstance(key, int):
                defaults[action] = int(key)
        return cls(defaults)


def name_for_key(key: int) -> str:
    """Return human readable name for ``key``."""

    try:
        return pygame.key.name(key)
    except Exception:  # pragma: no cover - defensive
        return str(key)


__all__ = ["InputMap", "InputManager", "name_for_key"]

