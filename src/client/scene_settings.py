from __future__ import annotations

"""Settings scene providing basic configuration options.

The implementation is intentionally lightweight yet covers the requirements of
key rebinding, audio volume control, UI scale and language selection.  Real
GUI layout/graphics are minimal; the goal is to offer a functional example
that can be interacted with during manual testing and from unit tests through
the underlying configuration objects.
"""

import pygame

from gamecore import config as gconfig
from gamecore import i18n
from gamecore.i18n import gettext as _
from .app import Scene
from .input import InputManager
from .sfx import set_volume
from .ui.widgets import Button, Dropdown, RebindButton, Slider


class SettingsScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.cfg = app.cfg
        self.input: InputManager = app.input
        self.widgets: list = []
        w, h = app.screen.get_size()
        y = 80

        # key bindings ---------------------------------------------------
        for action in ["end_turn", "rest", "scavenge", "pause"]:
            rect = pygame.Rect(40, y, 260, 32)
            self.widgets.append(RebindButton(rect, action, self.input))
            y += 40

        # volume slider --------------------------------------------------
        self.widgets.append(
            Slider(pygame.Rect(360, 80, 200, 20), 0, 100, self.cfg.get("volume", 1.0) * 100, self._on_volume)
        )

        # UI scale slider ------------------------------------------------
        self.widgets.append(
            Slider(
                pygame.Rect(360, 120, 200, 20),
                75,
                200,
                self.cfg.get("ui_scale", 1.0) * 100,
                self._on_scale,
            )
        )

        # language dropdown ---------------------------------------------
        self.widgets.append(
            Dropdown(pygame.Rect(360, 160, 200, 32), ["en", "ru"], self.cfg.get("lang", "en"), self._on_lang)
        )

        # back/apply button ---------------------------------------------
        self.widgets.append(Button(_("apply"), pygame.Rect(w // 2 - 60, h - 80, 120, 40), self._apply))

    # callbacks ----------------------------------------------------------
    def _on_volume(self, value: float) -> None:
        self.cfg["volume"] = round(value / 100.0, 2)
        set_volume(self.cfg["volume"])

    def _on_scale(self, value: float) -> None:
        self.cfg["ui_scale"] = round(value / 100.0, 2)

    def _on_lang(self, value: str) -> None:
        self.cfg["lang"] = value
        i18n.set_language(value)

    def _apply(self) -> None:
        self.input.save(self.cfg)
        gconfig.save_config(self.cfg)
        from .scene_menu import MenuScene

        self.next_scene = MenuScene(self.app)

    # scene API ---------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        for w in self.widgets:
            w.handle_event(event)

    def update(self, dt: float) -> None:  # pragma: no cover - nothing dynamic
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((30, 30, 30))
        for w in self.widgets:
            w.draw(surface)
