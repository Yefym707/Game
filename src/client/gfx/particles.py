from __future__ import annotations

"""Tiny particle helpers used by weather effects.

The real project would likely ship a more elaborate system but for the
purposes of the kata the implementation below keeps things intentionally
minimal.  Particles are stored inside a fixed size pool to avoid frequent
allocations.  Emitters create new particles at a configurable rate while the
``ParticlePool`` applies very small physics updates such as gravity and wind.
"""

from dataclasses import dataclass
from typing import Callable, Iterable, Iterator, List, Tuple


@dataclass
class Particle:
    """Simple particle with position, velocity and remaining life time."""

    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    life: float = 0.0
    color: Tuple[int, int, int] = (255, 255, 255)
    size: float = 1.0


class ParticlePool:
    """Container managing a fixed amount of particles.

    Particles are reused once their ``life`` drops below zero.  External code
    may iterate over the pool to draw active particles.
    """

    def __init__(self, capacity: int) -> None:
        self._items: List[Particle] = [Particle() for _ in range(capacity)]
        self._active: List[bool] = [False] * capacity

    def spawn(self) -> Particle | None:
        """Return an inactive particle from the pool or ``None`` if full."""

        for i, flag in enumerate(self._active):
            if not flag:
                self._active[i] = True
                p = self._items[i]
                p.life = 0.0
                p.vx = p.vy = 0.0
                return p
        return None

    # iteration ---------------------------------------------------------
    def __iter__(self) -> Iterator[Particle]:  # pragma: no cover - trivial
        for active, item in zip(self._active, self._items):
            if active:
                yield item

    # update ------------------------------------------------------------
    def update(self, dt: float, gravity: float = 0.0, wind: Tuple[float, float] = (0.0, 0.0)) -> None:
        """Advance all active particles by ``dt`` seconds."""

        gx, gy = wind
        gy += gravity
        for i, p in enumerate(self._items):
            if not self._active[i]:
                continue
            p.vx += gx * dt
            p.vy += gy * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.life -= dt
            if p.life <= 0.0:
                self._active[i] = False


class ParticleEmitter:
    """Continuously emit particles using a callback."""

    def __init__(self, pool: ParticlePool, rate: float, spawn: Callable[[Particle], None]) -> None:
        self.pool = pool
        self.rate = rate  # particles per second
        self._spawn_cb = spawn
        self._acc = 0.0

    def update(self, dt: float) -> None:
        self._acc += dt * self.rate
        while self._acc >= 1.0:
            self._acc -= 1.0
            p = self.pool.spawn()
            if p is None:
                return
            self._spawn_cb(p)
