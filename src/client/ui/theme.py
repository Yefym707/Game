"""Runtime switchable UI themes."""
from __future__ import annotations

from dataclasses import dataclass, field
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
    """Collection of UI colors and sizing constants.

    ``apply_scale`` recomputes all size related attributes allowing the
    interface to be scaled globally (``1.0`` – ``2.0``).  The ``*_base``
    attributes store the unscaled defaults.
    """

    colors: Dict[str, tuple[int, int, int]]
    palette: Dict[str, UIPalette]
    base_padding: int = 4
    base_radius_sm: int = 2
    base_radius_md: int = 4
    base_radius_lg: int = 8
    base_border_xs: int = 1
    base_border_sm: int = 2
    base_border_md: int = 4
    scale: float = 1.0
    padding: int = field(init=False)
    radius_sm: int = field(init=False)
    radius_md: int = field(init=False)
    radius_lg: int = field(init=False)
    border_xs: int = field(init=False)
    border_sm: int = field(init=False)
    border_md: int = field(init=False)

    def __post_init__(self) -> None:
        self.apply_scale(self.scale)

    def apply_scale(self, scale: float) -> None:
        self.scale = max(1.0, min(scale, 2.0))
        self.padding = int(self.base_padding * self.scale)
        self.radius_sm = int(self.base_radius_sm * self.scale)
        self.radius_md = int(self.base_radius_md * self.scale)
        self.radius_lg = int(self.base_radius_lg * self.scale)
        self.border_xs = max(1, int(self.base_border_xs * self.scale))
        self.border_sm = max(1, int(self.base_border_sm * self.scale))
        self.border_md = max(1, int(self.base_border_md * self.scale))

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
        base_padding=6,
        base_radius_md=6,
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
        base_padding=6,
        base_radius_md=6,
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
        base_padding=6,
        base_radius_md=6,
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
        base_padding=8,
        base_radius_md=4,
        base_border_md=4,
    ),
}

_current: Theme = THEMES["dark"]
_ui_scale = 1.0


def set_theme(name: str) -> None:
    """Select ``name`` as the active theme."""

    global _current
    _current = THEMES.get(name, _current)
    _current.apply_scale(_ui_scale)


def set_ui_scale(scale: float) -> None:
    """Update global UI scale and apply it to the current theme."""

    global _ui_scale
    _ui_scale = max(1.0, min(scale, 2.0))
    _current.apply_scale(_ui_scale)


def get_theme() -> Theme:
    """Return the currently active theme."""

    return _current
