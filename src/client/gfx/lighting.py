"""Simple tile based light map with blur and blending helpers."""
from __future__ import annotations

import pygame
from typing import List


class LightMap:
    """Maintain per-tile light intensity and render to a surface."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.map: List[List[float]] = [ [0.0]*width for _ in range(height) ]
        self.surface = pygame.Surface((width, height))

    def clear(self, value: float) -> None:
        for y in range(self.height):
            row = self.map[y]
            for x in range(self.width):
                row[x] = value

    def add_light(self, cx: int, cy: int, radius: int, intensity: float) -> None:
        r2 = radius * radius
        for y in range(cy - radius, cy + radius + 1):
            if not (0 <= y < self.height):
                continue
            row = self.map[y]
            for x in range(cx - radius, cx + radius + 1):
                if not (0 <= x < self.width):
                    continue
                dx = x - cx
                dy = y - cy
                if dx * dx + dy * dy > r2:
                    continue
                dist = (dx * dx + dy * dy) ** 0.5
                val = intensity * max(0.0, 1.0 - dist / radius)
                row[x] = min(1.0, row[x] + val)

    def blur(self) -> None:
        kernel = [0.27901, 0.44198, 0.27901]
        tmp = [row[:] for row in self.map]
        # horizontal
        for y in range(self.height):
            for x in range(self.width):
                acc = 0.0
                for k, w in enumerate(kernel):
                    xx = x + k - 1
                    if 0 <= xx < self.width:
                        acc += self.map[y][xx] * w
                tmp[y][x] = acc
        # vertical
        out = [row[:] for row in tmp]
        for y in range(self.height):
            for x in range(self.width):
                acc = 0.0
                for k, w in enumerate(kernel):
                    yy = y + k - 1
                    if 0 <= yy < self.height:
                        acc += tmp[yy][x] * w
                out[y][x] = acc
        self.map = out

    def to_surface(self, tile_size: int) -> pygame.Surface:
        w = self.width * tile_size
        h = self.height * tile_size
        surf = pygame.Surface((w, h))
        for y in range(self.height):
            for x in range(self.width):
                v = int(max(0.0, min(1.0, self.map[y][x])) * 255)
                color = (v, v, v)
                rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                surf.fill(color, rect)
        return surf
