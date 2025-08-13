from __future__ import annotations

"""Very small visual effects used in tests.

The real project ships with a fully fledged animation system.  For the unit
tests we only require two niceties: floating combat text and a stub for screen
shake.  ``FloatText`` simply fades and moves upward over time.  ``screen_shake``
acts as a no-op placeholder so calls do not fail when the function is imported.
"""

import pygame


class FloatText:
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


def screen_shake(camera, intensity: float = 1.0) -> None:  # pragma: no cover - visual
    """Placeholder for a tiny camera shake effect."""
    # In tests the function merely exists so importing modules that call it do
    # not fail; no actual shaking is required.
    return None


__all__ = ["FloatText", "screen_shake"]
