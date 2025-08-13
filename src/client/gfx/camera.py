from __future__ import annotations

import math
import pygame

from .tileset import TILE_SIZE
from . import anim


class SmoothCamera:
    """Camera following a target with smoothing and a deadzone."""

    def __init__(
        self,
        screen_size: tuple[int, int],
        world_size: tuple[int, int],
        follow_speed: float = 5.0,
        zoom_speed: float = 0.25,
        shake_scale: float = 1.0,
        deadzone: tuple[int, int] = (100, 80),
    ) -> None:
        self.screen_w, self.screen_h = screen_size
        self.world_w, self.world_h = world_size
        self.follow_speed = follow_speed
        self.zoom_speed = zoom_speed
        self.shake_scale = shake_scale
        self.deadzone_w, self.deadzone_h = deadzone
        self.x = 0.0
        self.y = 0.0
        # start with target at current position
        self.target_x = self.x
        self.target_y = self.y
        self.zoom = 1.0
        self._shake: anim.Shake | None = None
        self.shake_offset = (0.0, 0.0)

    # positioning -----------------------------------------------------
    def follow(self, pos: tuple[float, float]) -> None:
        """Adjust target so ``pos`` remains inside the deadzone."""

        view_w = self.screen_w / self.zoom
        view_h = self.screen_h / self.zoom
        cx = self.x + view_w / 2
        cy = self.y + view_h / 2
        dzx = self.deadzone_w / self.zoom
        dzy = self.deadzone_h / self.zoom

        tx = self.x
        ty = self.y
        dx = pos[0] - cx
        if dx < -dzx / 2:
            tx += dx + dzx / 2
        elif dx > dzx / 2:
            tx += dx - dzx / 2
        dy = pos[1] - cy
        if dy < -dzy / 2:
            ty += dy + dzy / 2
        elif dy > dzy / 2:
            ty += dy - dzy / 2
        self.target_x, self.target_y = tx, ty

    def update(self, dt: float) -> None:
        t = min(self.follow_speed * dt, 1.0)
        self.x = anim.lerp(self.x, self.target_x, t)
        self.y = anim.lerp(self.y, self.target_y, t)
        self.clamp_to_bounds()
        if self._shake:
            if self._shake.update(dt):
                self._shake = None
                self.shake_offset = (0.0, 0.0)
            else:
                self.shake_offset = self._shake.offset

    def clamp_to_bounds(self) -> None:
        max_x = max(0.0, self.world_w - self.screen_w / self.zoom)
        max_y = max(0.0, self.world_h - self.screen_h / self.zoom)
        self.x = max(0.0, min(self.x, max_x))
        self.y = max(0.0, min(self.y, max_y))

    # coordinate transforms ------------------------------------------
    def world_to_screen(self, pos: tuple[float, float]) -> tuple[float, float]:
        sx = (pos[0] - self.x) * self.zoom + self.shake_offset[0]
        sy = (pos[1] - self.y) * self.zoom + self.shake_offset[1]
        return sx, sy

    def screen_to_world(self, pos: tuple[float, float]) -> tuple[float, float]:
        wx = pos[0] / self.zoom + self.x
        wy = pos[1] / self.zoom + self.y
        return wx, wy

    # zoom & shake ----------------------------------------------------
    def zoom_at(self, step: int, focus: tuple[int, int]) -> None:
        before = self.screen_to_world(focus)
        self.zoom *= 1.0 + step * self.zoom_speed
        self.zoom = max(0.75, min(2.0, self.zoom))
        after = self.screen_to_world(focus)
        self.x += before[0] - after[0]
        self.y += before[1] - after[1]
        self.clamp_to_bounds()

    def shake(self, duration: float, amplitude: float, freq: float) -> None:
        self._shake = anim.Shake(duration, amplitude * self.shake_scale, freq)

    # direct positioning ---------------------------------------------
    def jump_to(self, cell: tuple[int, int]) -> None:
        """Center the camera on ``cell`` immediately."""

        px = cell[0] * TILE_SIZE + TILE_SIZE / 2
        py = cell[1] * TILE_SIZE + TILE_SIZE / 2
        self.x = px - self.screen_w / (2 * self.zoom)
        self.y = py - self.screen_h / (2 * self.zoom)
        self.target_x, self.target_y = self.x, self.y
        self.clamp_to_bounds()
