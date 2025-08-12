from __future__ import annotations

"""Simple weather effects built on top of the particle helpers."""

from dataclasses import dataclass
import math
from gamecore import rules
import pygame
from typing import Tuple

from .particles import Particle, ParticleEmitter, ParticlePool


@dataclass
class Wind:
    x: float = 0.0
    y: float = 0.0


class _BaseWeather:
    """Shared functionality for all weather effects."""

    def __init__(self, size: tuple[int, int], intensity: float = 1.0, wind: Tuple[float, float] = (0.0, 0.0)) -> None:
        self.size = size
        self.intensity = intensity
        self.wind = wind

    def set_wind(self, wind: Tuple[float, float]) -> None:
        self.wind = wind

    def set_intensity(self, value: float) -> None:
        self.intensity = value

    def update(self, dt: float) -> None:  # pragma: no cover - interface
        pass

    def draw(self, surface: pygame.Surface, camera: Tuple[float, float]) -> None:  # pragma: no cover - interface
        pass


class Rain(_BaseWeather):
    """Diagonal rain streaks affected by wind."""

    def __init__(self, size: tuple[int, int], intensity: float = 1.0, wind: Tuple[float, float] = (0.0, 0.0)) -> None:
        super().__init__(size, intensity, wind)
        cap = max(16, int(400 * intensity))
        self.pool = ParticlePool(cap)
        self.emitter = ParticleEmitter(self.pool, 200 * intensity, self._spawn)

    def _spawn(self, p: Particle) -> None:
        w, h = self.size
        p.x = rules.RNG.uniform(0, w)
        p.y = rules.RNG.uniform(-h, 0)
        p.vx = self.wind[0] - 50.0
        p.vy = 300.0 + self.wind[1]
        p.life = h / p.vy
        p.color = (150, 150, 255)
        p.size = rules.RNG.uniform(8, 15)

    def update(self, dt: float) -> None:
        self.emitter.rate = 200 * self.intensity
        self.emitter.update(dt)
        self.pool.update(dt, wind=self.wind)

    def draw(self, surface: pygame.Surface, camera: Tuple[float, float]) -> None:
        cx, cy = camera
        for p in self.pool:
            start = (p.x - cx * 0.5, p.y - cy * 0.5)
            end = (start[0] + p.vx * 0.05, start[1] + p.vy * 0.05)
            pygame.draw.line(surface, p.color, start, end)


class Snow(_BaseWeather):
    """Gentle snow flakes with slight drifting."""

    def __init__(self, size: tuple[int, int], intensity: float = 1.0, wind: Tuple[float, float] = (0.0, 0.0)) -> None:
        super().__init__(size, intensity, wind)
        cap = max(16, int(300 * intensity))
        self.pool = ParticlePool(cap)
        self.emitter = ParticleEmitter(self.pool, 150 * intensity, self._spawn)

    def _spawn(self, p: Particle) -> None:
        w, h = self.size
        p.x = rules.RNG.uniform(0, w)
        p.y = rules.RNG.uniform(-h, 0)
        p.vx = self.wind[0]
        p.vy = 40.0 + self.wind[1]
        p.life = h / p.vy + rules.RNG.uniform(1.0, 2.0)
        p.color = (255, 255, 255)
        p.size = rules.RNG.uniform(2, 4)
        p.phase = rules.RNG.uniform(0.0, math.tau)  # type: ignore[attr-defined]

    def update(self, dt: float) -> None:
        self.emitter.rate = 150 * self.intensity
        self.emitter.update(dt)
        self.pool.update(dt, wind=self.wind)
        for p in self.pool:
            p.phase += dt  # type: ignore[attr-defined]
            p.x += math.sin(p.phase) * 10.0 * dt

    def draw(self, surface: pygame.Surface, camera: Tuple[float, float]) -> None:
        cx, cy = camera
        for p in self.pool:
            pos = (p.x - cx * 0.3, p.y - cy * 0.3)
            pygame.draw.circle(surface, p.color, (int(pos[0]), int(pos[1])), int(p.size))


class Fog(_BaseWeather):
    """Semi-transparent pulsating fog overlay."""

    def __init__(self, size: tuple[int, int], intensity: float = 1.0, wind: Tuple[float, float] = (0.0, 0.0)) -> None:
        super().__init__(size, intensity, wind)
        self.surface = pygame.Surface(size, pygame.SRCALPHA)
        base = pygame.Surface((64, 64))
        for x in range(64):
            for y in range(64):
                v = rules.RNG.randint(200, 255)
                base.set_at((x, y), (v, v, v))
        self.noise = pygame.transform.smoothscale(base, size)
        self.time = 0.0

    def update(self, dt: float) -> None:
        self.time += dt
        alpha = int(80 * self.intensity + 40 * math.sin(self.time * 0.5))
        self.surface.fill((100, 100, 100, alpha))
        self.surface.blit(self.noise, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

    def draw(self, surface: pygame.Surface, camera: Tuple[float, float]) -> None:  # noqa: ARG002 - camera unused
        surface.blit(self.surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
