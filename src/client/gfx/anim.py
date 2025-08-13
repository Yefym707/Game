from __future__ import annotations

"""Very small tween/animation helpers.

Only what is required by the simplified game scene is implemented.  These
classes are intentionally tiny; animations are updated manually and report when
complete.
"""

from dataclasses import dataclass
import math
import pygame


_FLOAT_STACKS: dict[tuple[int, int], int] = {}

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


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


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


# lightweight animation primitives used by the game scene -----------------


@dataclass
class Fade:
    """Fade a surface in or out by modifying its alpha channel."""

    surface: pygame.Surface
    duration: float = 0.3
    out: bool = True
    time: float = 0.0

    def update(self, dt: float) -> bool:
        self.time += dt
        t = min(self.time / self.duration, 1.0)
        t = ease_in_out(t)
        alpha = int(t * 255) if self.out else int((1.0 - t) * 255)
        self.surface.set_alpha(alpha)
        return self.time >= self.duration


@dataclass
class Flash:
    """Briefly flash a rectangle to indicate a hit."""

    rect: pygame.Rect
    color: tuple[int, int, int] = (255, 255, 255)
    duration: float = 0.2
    time: float = 0.0

    def update(self, dt: float) -> bool:
        self.time += dt
        return self.time >= self.duration

    def draw(self, surface: pygame.Surface) -> None:
        if int(self.time * 10) % 2 == 0:
            pygame.draw.rect(surface, self.color, self.rect, 2)


@dataclass
class Slide:
    """Slide an image from ``start`` to ``end`` over ``duration``."""

    image: pygame.Surface
    start: tuple[float, float]
    end: tuple[float, float]
    duration: float = 0.2
    time: float = 0.0
    pos: tuple[float, float] | None = None

    def update(self, dt: float) -> bool:
        self.time += dt
        t = min(self.time / self.duration, 1.0)
        t = ease_in_out(t)
        x = self.start[0] + (self.end[0] - self.start[0]) * t
        y = self.start[1] + (self.end[1] - self.start[1]) * t
        self.pos = (x, y)
        return self.time >= self.duration

    def draw(self, surface: pygame.Surface) -> None:
        if self.pos:
            surface.blit(self.image, self.pos)


@dataclass
class FloatText:
    """Small piece of text floating upwards and fading out."""

    text: str
    pos: tuple[float, float]
    color: tuple[int, int, int] = (255, 255, 255)
    duration: float = 0.45
    rise: float = 30.0
    drift: float = 8.0
    time: float = 0.0
    font: pygame.font.Font | None = None
    stack: int = 0

    def __post_init__(self) -> None:
        if self.font is None:
            self.font = pygame.font.SysFont(None, 18)
        key = (int(self.pos[0]), int(self.pos[1]))
        self.stack = _FLOAT_STACKS.get(key, 0)
        _FLOAT_STACKS[key] = self.stack + 1

    def update(self, dt: float) -> bool:
        self.time += dt
        finished = self.time >= self.duration
        if finished:
            key = (int(self.pos[0]), int(self.pos[1]))
            _FLOAT_STACKS[key] = max(0, _FLOAT_STACKS.get(key, 1) - 1)
        return finished

    def draw(self, surface: pygame.Surface) -> None:
        t = min(self.time / self.duration, 1.0)
        alpha = int((1.0 - t) * 255)
        x = self.pos[0] + self.drift * t
        y = self.pos[1] - self.rise * t - self.stack * self.font.get_linesize()
        img = self.font.render(self.text, True, self.color)
        img.set_alpha(alpha)
        w, h = surface.get_size()
        x = max(0.0, min(x, w - img.get_width()))
        y = max(0.0, min(y, h - img.get_height()))
        surface.blit(img, (x, y))


@dataclass
class Shake:
    duration: float
    amplitude: float
    freq: float
    time: float = 0.0
    offset: tuple[float, float] = (0.0, 0.0)

    def update(self, dt: float) -> bool:
        self.time += dt
        decay = 1.0 - min(self.time / self.duration, 1.0)
        ang = self.time * self.freq * 2.0 * math.pi
        self.offset = (
            math.sin(ang) * self.amplitude * decay,
            math.cos(ang) * self.amplitude * decay,
        )
        return self.time >= self.duration
