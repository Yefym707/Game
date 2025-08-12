from __future__ import annotations

"""Very small tween/animation helpers.

Only what is required by the simplified game scene is implemented.  These
classes are intentionally tiny; animations are updated manually and report when
complete.
"""

from dataclasses import dataclass


@dataclass
class Tween:
    """Linear interpolation between ``start`` and ``end`` over ``duration``.

    The ``value`` attribute holds the current interpolated value.  Calling
    :meth:`update` advances the tween and returns ``True`` once finished.
    """

    start: float
    end: float
    duration: float
    value: float = 0.0
    time: float = 0.0

    def reset(self) -> None:
        self.value = self.start
        self.time = 0.0

    def update(self, dt: float) -> bool:
        self.time += dt
        t = min(self.time / self.duration, 1.0) if self.duration > 0 else 1.0
        self.value = self.start + (self.end - self.start) * t
        return self.time >= self.duration
