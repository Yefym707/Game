"""Runtime switchable UI themes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class Theme:
    colors: Dict[str, tuple[int, int, int]]
    padding: int = 4
    radius: int = 4


THEMES: Dict[str, Theme] = {
    "light": Theme(
        colors={
            "bg": (240, 240, 240),
            "panel": (220, 220, 220),
            "panel_hover": (200, 200, 200),
            "text": (0, 0, 0),
            "border": (40, 40, 40),
            "tooltip": (250, 250, 210),
            "toast": (0, 0, 0),
        },
        padding=6,
        radius=6,
    ),
    "dark": Theme(
        colors={
            "bg": (30, 30, 30),
            "panel": (60, 60, 60),
            "panel_hover": (80, 80, 80),
            "text": (255, 255, 255),
            "border": (200, 200, 200),
            "tooltip": (50, 50, 50),
            "toast": (20, 20, 20),
        },
        padding=6,
        radius=6,
    ),
    "apocalypse": Theme(
        colors={
            "bg": (40, 40, 40),
            "panel": (80, 60, 60),
            "panel_hover": (100, 80, 80),
            "text": (230, 220, 200),
            "border": (150, 80, 80),
            "tooltip": (60, 50, 50),
            "toast": (30, 20, 20),
        },
        padding=6,
        radius=6,
    ),
}

_current: Theme = THEMES["dark"]


def set_theme(name: str) -> None:
    """Select ``name`` as the active theme."""

    global _current
    _current = THEMES.get(name, _current)


def get_theme() -> Theme:
    """Return the currently active theme."""

    return _current
