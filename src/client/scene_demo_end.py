"""End of demo screen offering to buy the full version."""
from __future__ import annotations

import pygame

from gamecore.i18n import gettext as _
from .app import Scene
from .ui.widgets import Button

try:  # pragma: no cover - optional dependency
    import steamworks  # type: ignore
except Exception:  # pragma: no cover - library not available
    steamworks = None


class DemoEndScene(Scene):
    """Simple scene shown when the demo limitations are reached."""

    def __init__(self, app) -> None:
        super().__init__(app)
        w, h = app.screen.get_size()
        self.font = pygame.font.SysFont(None, 36)
        self.message = _("DEMO_COMPLETE")
        self.button = Button(
            _("BUY_FULL"), pygame.Rect(w // 2 - 100, h // 2, 200, 40), self._buy
        )

    def _buy(self) -> None:
        """Attempt to open the Steam overlay or warn if unavailable."""

        if steamworks and hasattr(steamworks, "open_overlay"):
            try:
                steamworks.open_overlay("store")
            except Exception:  # pragma: no cover - fallback
                print(_("steam_sdk_missing"))
        else:  # pragma: no cover - fallback
            print(_("steam_sdk_missing"))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from .scene_menu import MenuScene

            self.next_scene = MenuScene(self.app)
            return
        self.button.handle_event(event)

    def update(self, dt: float) -> None:  # pragma: no cover - nothing dynamic
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        img = self.font.render(self.message, True, (255, 255, 255))
        surface.blit(img, img.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2 - 40)))
        self.button.draw(surface)
