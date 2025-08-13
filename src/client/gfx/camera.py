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
    """Small camera helper with basic panning and zooming.

    ``screen_size`` and ``world_size`` are expressed in pixels.  The camera
    keeps the top left world coordinate in ``x``/``y`` and converts between
    world and screen space via :meth:`world_to_screen` and
    :meth:`screen_to_world`.
    """

    screen_size: tuple[int, int]
    world_size: tuple[int, int]
    zoom: float = 1.0

    def __post_init__(self) -> None:
        self.screen_w, self.screen_h = self.screen_size
        self.world_w, self.world_h = self.world_size
        self.x = 0.0
        self.y = 0.0

    # movement ------------------------------------------------------------
    def clamp_to_bounds(self) -> None:
        """Clamp the view so it stays within the world bounds."""

        max_x = max(0.0, self.world_w - self.screen_w / self.zoom)
        max_y = max(0.0, self.world_h - self.screen_h / self.zoom)
        self.x = max(0.0, min(self.x, max_x))
        self.y = max(0.0, min(self.y, max_y))

    clamp = clamp_to_bounds  # backwards compatibility

    def jump_to(self, cell: tuple[int, int]) -> None:
        """Centre the camera on ``cell`` expressed in world pixels."""

        cx, cy = cell
        self.x = float(cx) - self.screen_w / (2 * self.zoom)
        self.y = float(cy) - self.screen_h / (2 * self.zoom)
        self.clamp_to_bounds()

    # coordinate conversions ---------------------------------------------
    def world_to_screen(self, pos: tuple[float, float]) -> tuple[int, int]:
        """Convert world coordinates to screen pixels."""

        sx = int((pos[0] - self.x) * self.zoom)
        sy = int((pos[1] - self.y) * self.zoom)
        return sx, sy

    def screen_to_world(self, pos: tuple[float, float]) -> tuple[float, float]:
        """Inverse of :meth:`world_to_screen`."""

        wx = pos[0] / self.zoom + self.x
        wy = pos[1] / self.zoom + self.y
        return wx, wy

    # zoom ----------------------------------------------------------------
    def zoom_at(self, amount: float, cursor: tuple[int, int]) -> None:
        """Zoom towards ``cursor`` keeping the world position underneath it."""

        old_zoom = self.zoom
        self.zoom = max(0.25, min(4.0, self.zoom * (1.0 + amount)))
        if self.zoom != old_zoom:
            wx, wy = self.screen_to_world(cursor)
            self.x = wx - cursor[0] / self.zoom
            self.y = wy - cursor[1] / self.zoom
            self.clamp_to_bounds()

    # the real project exposes ``update`` and smooth following.  Tests do not
    # rely on those features so they are intentionally omitted.


__all__ = ["SmoothCamera"]
