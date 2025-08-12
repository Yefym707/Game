from __future__ import annotations

"""Very small tween/animation helpers.

Only what is required by the simplified game scene is implemented.  These
classes are intentionally tiny; animations are updated manually and report when
complete.
"""

from dataclasses import dataclass
import pygame

# ---------------------------------------------------------------------------
# tween helpers


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


def ease_in_out(t: float) -> float:
    """Smoothstep easing used throughout the UI."""

    return t * t * (3.0 - 2.0 * t)


class FadeTransition:
    """Fade-out old scene and fade-in the new one."""

    def __init__(self, app, new_scene, duration: float = 0.3) -> None:
        self.app = app
        self.new_scene = new_scene
        self.duration = duration
        self.time = 0.0
        self.phase = "out"
        self.finished = False
        self.overlay = pygame.Surface(app.screen.get_size())
        self.overlay.fill((0, 0, 0))

    def update(self, dt: float) -> None:
        self.time += dt
        if self.time >= self.duration:
            if self.phase == "out":
                # switch scenes and start fading back in
                self.app.scene = self.new_scene
                self.phase = "in"
                self.time = 0.0
            else:
                self.finished = True

    def draw(self, surface: pygame.Surface) -> None:
        t = min(self.time / self.duration, 1.0)
        t = ease_in_out(t)
        alpha = int(t * 255) if self.phase == "out" else int((1.0 - t) * 255)
        self.overlay.set_alpha(alpha)
        surface.blit(self.overlay, (0, 0))


class SlideTransition:
    """Slide the new scene over the old one."""

    def __init__(self, app, new_scene, duration: float = 0.3) -> None:
        self.app = app
        self.new_scene = new_scene
        self.duration = duration
        self.time = 0.0
        self.finished = False

        w, h = app.screen.get_size()
        self.old_surf = pygame.Surface((w, h))
        self.new_surf = pygame.Surface((w, h))
        app.scene.draw(self.old_surf)
        new_scene.draw(self.new_surf)

    def update(self, dt: float) -> None:
        self.time += dt
        if self.time >= self.duration:
            self.finished = True
            self.app.scene = self.new_scene

    def draw(self, surface: pygame.Surface) -> None:
        w, _ = surface.get_size()
        t = min(self.time / self.duration, 1.0)
        t = ease_in_out(t)
        offset = int((1.0 - t) * w)
        surface.blit(self.new_surf, (0, 0))
        surface.blit(self.old_surf, (-offset, 0))
