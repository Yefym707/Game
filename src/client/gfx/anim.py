from __future__ import annotations

"""Very small visual effects used in tests.

The real project ships with a fully fledged animation system.  For the unit
tests we only require two niceties: floating combat text and a stub for screen
shake.  ``FloatText`` simply fades and moves upward over time.  ``screen_shake``
acts as a no-op placeholder so calls do not fail when the function is imported.
"""

import pygame


class FloatText:
    """Simple piece of combat text that rises and fades."""

    def __init__(self, text: str, pos: tuple[int, int]) -> None:
        self.text = text
        self.x, self.y = pos
        self.alpha = 255
        self.font = pygame.font.SysFont(None, 16)

    def update(self, dt: float) -> None:
        self.y -= 20 * dt
        self.alpha = max(0, self.alpha - int(255 * dt))

    def draw(self, surface: pygame.Surface) -> None:  # pragma: no cover - visual
        img = self.font.render(self.text, True, (255, 255, 255))
        img.set_alpha(self.alpha)
        surface.blit(img, (self.x, self.y))


def float_text(text: str, pos: tuple[int, int]) -> FloatText:
    """Convenience factory returning a :class:`FloatText` instance."""

    return FloatText(text, pos)


def screen_shake(camera, amplitude: float = 1.0, duration: float = 0.2) -> None:  # pragma: no cover - visual
    """Tiny placeholder for a camera shake effect.

    The implementation is intentionally light weight – the tests only need the
    function to exist so modules can call it after an attack.  No actual shaking
    is required.
    """

    _ = (camera, amplitude, duration)  # unused but keeps signature stable
    return None


__all__ = ["FloatText", "float_text", "screen_shake"]
