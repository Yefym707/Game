"""Very small camera helper."""

from __future__ import annotations


class Camera:
    """Track a view rectangle inside world bounds."""

    def __init__(self, view_w: int, view_h: int, world_w: int, world_h: int) -> None:
        self.view_w = view_w
        self.view_h = view_h
        self.world_w = world_w
        self.world_h = world_h
        self.x = 0
        self.y = 0

    def clamp(self) -> None:
        max_x = max(0, self.world_w - self.view_w)
        max_y = max(0, self.world_h - self.view_h)
        self.x = max(0, min(self.x, max_x))
        self.y = max(0, min(self.y, max_y))

    def jump_to(self, cell: tuple[int, int]) -> None:
        cx, cy = cell
        self.x = cx - self.view_w // 2
        self.y = cy - self.view_h // 2
        self.clamp()


__all__ = ["Camera"]

