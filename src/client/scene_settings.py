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
from . import sfx
from .ui.widgets import Button, Dropdown, RebindButton, Slider, Toggle


class InputField:
    """Very small text input used for telemetry endpoint."""

    def __init__(self, rect: pygame.Rect, text: str, callback) -> None:
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.active = False
        self.font = pygame.font.SysFont(None, 24)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.callback(self.text)
                self.active = False
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (60, 60, 60), self.rect)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 1)
        img = self.font.render(self.text, True, (255, 255, 255))
        surface.blit(img, (self.rect.x + 4, self.rect.y + 4))


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

        # volume sliders -------------------------------------------------
        vol_y = 80
        for key in ["master", "step", "hit", "ui"]:
            val = self.cfg.get(f"volume_{key}", self.cfg.get("volume", 1.0))
            self.widgets.append(
                Slider(pygame.Rect(360, vol_y, 200, 20), 0, 100, val * 100, lambda v, k=key: self._on_volume(k, v))
            )
            vol_y += 40

        # UI scale slider ------------------------------------------------
        self.widgets.append(
            Slider(
                pygame.Rect(360, vol_y, 200, 20),
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

        # telemetry toggle ----------------------------------------------
        self.widgets.append(
            Toggle(
                _("telemetry_opt_in"),
                pygame.Rect(40, y, 260, 32),
                self.cfg.get("telemetry_opt_in", False),
                self._on_tel_opt,
            )
        )
        y += 40
        # endpoint input -------------------------------------------------
        self.endpoint_input = InputField(
            pygame.Rect(40, y, 260, 32),
            self.cfg.get("telemetry_endpoint", ""),
            self._on_endpoint,
        )
        self.widgets.append(self.endpoint_input)
        y += 40
        # send test event ------------------------------------------------
        self.widgets.append(
            Button(
                _("send_test_event"),
                pygame.Rect(40, y, 260, 32),
                self._send_test_event,
            )
        )

        # back/apply button ---------------------------------------------
        self.widgets.append(Button(_("apply"), pygame.Rect(w // 2 - 60, h - 80, 120, 40), self._apply))

    # callbacks ----------------------------------------------------------
    def _on_volume(self, channel: str, value: float) -> None:
        vol = round(value / 100.0, 2)
        self.cfg[f"volume_{channel}"] = vol
        if channel == "master":
            # legacy key used by menu scene
            self.cfg["volume"] = vol
        sfx.set_volume(vol, channel)

    def _on_scale(self, value: float) -> None:
        self.cfg["ui_scale"] = round(value / 100.0, 2)

    def _on_lang(self, value: str) -> None:
        self.cfg["lang"] = value
        i18n.set_language(value)

    def _on_tel_opt(self, value: bool) -> None:
        self.cfg["telemetry_opt_in"] = value

    def _on_endpoint(self, value: str) -> None:
        self.cfg["telemetry_endpoint"] = value

    def _send_test_event(self) -> None:
        from telemetry import send, events

        send(events.perf_tick(0, 0, 0, self.app.screen.get_size()))

    def _apply(self) -> None:
        self.input.save(self.cfg)
        gconfig.save_config(self.cfg)
        from telemetry import init as telemetry_init, send, events

        telemetry_init(self.cfg)
        send(events.settings_changed({"telemetry_opt_in": self.cfg.get("telemetry_opt_in", False)}))
        from .scene_menu import MenuScene

        self.next_scene = MenuScene(self.app)

    # scene API ---------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from .scene_menu import MenuScene

            self.next_scene = MenuScene(self.app)
            return
        for w in self.widgets:
            w.handle_event(event)

    def update(self, dt: float) -> None:  # pragma: no cover - nothing dynamic
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((30, 30, 30))
        for w in self.widgets:
            w.draw(surface)
