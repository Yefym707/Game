"""Runtime switchable UI themes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class UIPalette:
    """Subset of theme colors used for highlights and UI states."""

    neutral: tuple[int, int, int]
    accent: tuple[int, int, int]
    danger: tuple[int, int, int]
    warn: tuple[int, int, int]
    info: tuple[int, int, int]


@dataclass
class Theme:
    colors: Dict[str, tuple[int, int, int]]
    palette: Dict[str, UIPalette]
    padding: int = 4
    radius_sm: int = 2
    radius_md: int = 4
    radius_lg: int = 8
    border_xs: int = 1
    border_sm: int = 2
    border_md: int = 4

    @property
    def radius(self) -> int:
        return self.radius_md

    @property
    def border_width(self) -> int:
        return self.border_sm


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
        palette={
            "ui": UIPalette(
                neutral=(120, 120, 120),
                accent=(0, 120, 215),
                danger=(200, 40, 40),
                warn=(240, 170, 0),
                info=(30, 144, 255),
            )
        },
        padding=6,
        radius_md=6,
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
        palette={
            "ui": UIPalette(
                neutral=(180, 180, 180),
                accent=(0, 170, 255),
                danger=(220, 80, 80),
                warn=(240, 170, 0),
                info=(80, 160, 255),
            )
        },
        padding=6,
        radius_md=6,
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
        palette={
            "ui": UIPalette(
                neutral=(170, 130, 120),
                accent=(200, 110, 60),
                danger=(200, 60, 60),
                warn=(220, 160, 70),
                info=(120, 180, 200),
            )
        },
        padding=6,
        radius_md=6,
    ),
    "high_contrast": Theme(
        colors={
            "bg": (11, 11, 11),  # #0B0B0B
            "panel": (18, 18, 18),  # #121212
            "panel_hover": (32, 32, 32),
            "text": (255, 255, 255),
            "border": (255, 255, 255),
            "tooltip": (18, 18, 18),
            "toast": (11, 11, 11),
            "shadow1": (0, 0, 0, 150),
            "shadow2": (0, 0, 0, 80),
        },
        palette={
            "ui": UIPalette(
                neutral=(220, 220, 220),
                accent=(255, 191, 0),  # amber
                danger=(255, 80, 80),
                warn=(240, 170, 0),
                info=(0, 170, 255),
            )
        },
        padding=8,
        radius_md=4,
        border_md=4,
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
