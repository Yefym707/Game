from __future__ import annotations

"""Extremely small camera with jump/zoom used by tests.

The class is purposely tiny yet mimics the API of the real project where a
camera exposes ``x``/``y`` coordinates and a ``jump_to`` method that centres the
view on a given world cell.  ``SmoothCamera`` also exposes ``world_w`` and
``world_h`` attributes which the minimap widget relies on.
"""

from dataclasses import dataclass


@dataclass
class SmoothCamera:
    screen_size: tuple[int, int]
    world_size: tuple[int, int]
    zoom: float = 1.0

    def __post_init__(self) -> None:
        self.screen_w, self.screen_h = self.screen_size
        self.world_w, self.world_h = self.world_size
        self.x = 0.0
        self.y = 0.0

    # movement ------------------------------------------------------------
    def clamp(self) -> None:
        max_x = max(0.0, self.world_w - self.screen_w / self.zoom)
        max_y = max(0.0, self.world_h - self.screen_h / self.zoom)
        self.x = max(0.0, min(self.x, max_x))
        self.y = max(0.0, min(self.y, max_y))

    def jump_to(self, cell: tuple[int, int]) -> None:
        cx, cy = cell
        self.x = float(cx) - self.screen_w / (2 * self.zoom)
        self.y = float(cy) - self.screen_h / (2 * self.zoom)
        self.clamp()

    # the real project exposes ``update`` and smooth following.  Tests do not
    # rely on those features so they are intentionally omitted.


__all__ = ["SmoothCamera"]
