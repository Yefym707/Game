"""Minimal UI helpers for tests."""

from __future__ import annotations

import pygame

from gamecore.i18n import gettext as _

_font_cache: pygame.font.Font | None = None


def _font() -> pygame.font.Font:
    global _font_cache
    if _font_cache is None:
        if not pygame.font.get_init():
            pygame.font.init()
        _font_cache = pygame.font.SysFont(None, 24)
    return _font_cache


class ModalError:
    """Very small blocking error dialog."""

    def __init__(self, title: str, message: str) -> None:
        self.title = title
        self.message = message

    def run(self, surface: pygame.Surface) -> None:  # pragma: no cover - manual use
        surface.fill((0, 0, 0))
        f = _font()
        img = f.render(self.title, True, (255, 0, 0))
        surface.blit(img, (20, 20))
        msg = f.render(self.message, True, (255, 255, 255))
        surface.blit(msg, (20, 60))
        pygame.display.flip()
        waiting = True
        while waiting:
            for e in pygame.event.get():
                if e.type in (pygame.KEYDOWN, pygame.QUIT, pygame.MOUSEBUTTONDOWN):
                    waiting = False


class ModalConfirm:
    """Simplified confirmation dialog used in tests."""

    def __init__(self, message: str, on_yes) -> None:
        self.message = message
        self._on_yes = on_yes

    def on_yes(self) -> None:
        self._on_yes()

    # The following methods are placeholders for a real UI -----------------
    def handle_event(self, event: pygame.event.Event) -> None:  # pragma: no cover
        pass

    def update(self, dt: float) -> None:  # pragma: no cover
        pass

    def draw(self, surface: pygame.Surface) -> None:  # pragma: no cover
        f = _font()
        img = f.render(self.message, True, (255, 255, 255))
        rect = img.get_rect(center=surface.get_rect().center)
        pygame.draw.rect(surface, (0, 0, 0), rect.inflate(20, 20))
        surface.blit(img, rect)


class Toast:  # pragma: no cover - placeholder
    def __init__(self, text: str) -> None:
        self.text = text


class Tooltip:  # pragma: no cover - placeholder
    def __init__(self, text: str) -> None:
        self.text = text


class HelpOverlay:
    """Draw a static help overlay describing controls."""

    def __init__(self, input_map) -> None:
        self.visible = False
        self.input_map = input_map

    def toggle(self) -> None:
        self.visible = not self.visible

    def draw(self, surface: pygame.Surface) -> None:  # pragma: no cover
        if not self.visible:
            return
        f = _font()
        lines = [
            _("help_select"),
            _("help_move"),
            _("help_end_turn"),
            _("help_pause"),
            _("help_help"),
        ]
        y = 20
        for line in lines:
            img = f.render(line, True, (255, 255, 255))
            surface.blit(img, (20, y))
            y += 30


__all__ = [
    "ModalConfirm",
    "ModalError",
    "Toast",
    "Tooltip",
    "HelpOverlay",
]

