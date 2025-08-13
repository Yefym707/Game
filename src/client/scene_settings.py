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
from .ui.widgets import (
    Button,
    Dropdown,
    RebindButton,
    Slider,
    Toggle,
    LargeTextToggle,
    hover_hints,
)
from .ui.theme import set_theme


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
        self.general_widgets: list = []
        self.access_widgets: list = []
        self.widgets: list = self.general_widgets
        w, h = app.screen.get_size()
        set_theme(self.cfg.get("theme", "dark"))

        self.btn_general = Button(_("SETTINGS"), pygame.Rect(40, 20, 120, 32), lambda: self._set_tab("general"))
        self.btn_access = Button(_("accessibility"), pygame.Rect(180, 20, 160, 32), lambda: self._set_tab("access"))

        # general tab ----------------------------------------------------
        y = 80
        for action in ["end_turn", "rest", "scavenge", "pause"]:
            rect = pygame.Rect(40, y, 260, 32)
            self.general_widgets.append(RebindButton(rect, action, self.input))
            y += 40

        vol_y = 80
        for key in ["master", "step", "hit", "ui"]:
            val = self.cfg.get(f"volume_{key}", self.cfg.get("volume", 1.0))
            self.general_widgets.append(
                Slider(pygame.Rect(360, vol_y, 200, 20), 0, 100, val * 100, lambda v, k=key: self._on_volume(k, v))
            )
            vol_y += 40
        self.general_widgets.append(
            Slider(pygame.Rect(360, vol_y, 200, 20), 100, 200, max(1.0, self.cfg.get("ui_scale", 1.0)) * 100, self._on_scale)
        )

        self.general_widgets.append(
            Dropdown(
                pygame.Rect(360, 160, 200, 32),
                [("en", "en"), ("ru", "ru")],
                self.cfg.get("lang", "en"),
                self._on_lang,
            )
        )
        self.general_widgets.append(
            Dropdown(
                pygame.Rect(40, y, 260, 32),
                [
                    ("light", _("theme_light")),
                    ("dark", _("theme_dark")),
                    ("apocalypse", _("theme_apocalypse")),
                    ("high_contrast", _("high_contrast")),
                ],
                self.cfg.get("theme", "dark"),
                self._on_theme,
            )
        )
        y += 40
        self.general_widgets.append(
            Toggle(
                _("show_minimap"),
                pygame.Rect(40, y, 260, 32),
                self.cfg.get("minimap_enabled", True),
                self._on_minimap,
            )
        )
        self.general_widgets.append(
            Slider(pygame.Rect(360, y, 200, 20), 100, 300, self.cfg.get("minimap_size", 200), self._on_minimap_size)
        )
        y += 40
        self.general_widgets.append(
            Dropdown(
                pygame.Rect(40, y, 260, 32),
                [
                    ("ask", _("ask")),
                    ("prefer_local", _("prefer_local")),
                    ("prefer_cloud", _("prefer_cloud")),
                ],
                self.cfg.get("save_conflict_policy", gconfig.DEFAULT_SAVE_CONFLICT_POLICY),
                self._on_conflict_policy,
            )
        )
        y += 40
        self.general_widgets.append(
            Toggle(
                _("telemetry_opt_in"),
                pygame.Rect(40, y, 260, 32),
                self.cfg.get("telemetry_opt_in", False),
                self._on_tel_opt,
            )
        )
        y += 40
        self.endpoint_input = InputField(
            pygame.Rect(40, y, 260, 32),
            self.cfg.get("telemetry_endpoint", ""),
            self._on_endpoint,
        )
        self.general_widgets.append(self.endpoint_input)
        y += 40
        self.general_widgets.append(
            Button(_("send_test_event"), pygame.Rect(40, y, 260, 32), self._send_test_event)
        )

        for fx in ["vignette", "desaturate", "bloom"]:
            self.general_widgets.append(
                Toggle(
                    _(f"fx_{fx}"),
                    pygame.Rect(40, y, 260, 32),
                    self.cfg.get(f"fx_{fx}", False),
                    lambda v, k=fx: self._on_fx_toggle(k, v),
                )
            )
            self.general_widgets.append(
                Slider(
                    pygame.Rect(360, y, 200, 20),
                    0,
                    100,
                    self.cfg.get(f"fx_{fx}_intensity", 0.5) * 100,
                    lambda v, k=fx: self._on_fx_intensity(k, v),
                )
            )
            y += 40
        self.general_widgets.append(
            Toggle(
                _("fx_color"),
                pygame.Rect(40, y, 260, 32),
                self.cfg.get("fx_color", False),
                lambda v: self._on_fx_toggle("color", v),
            )
        )
        curve = self.cfg.get("fx_color_curve", [1.0, 1.0, 1.0])
        for i, name in enumerate(["R", "G", "B"]):
            self.general_widgets.append(
                Slider(
                    pygame.Rect(360, y, 200, 20),
                    0,
                    200,
                    curve[i] * 100,
                    lambda v, idx=i: self._on_curve(idx, v),
                )
            )
            y += 40
        self.general_widgets.append(Button(_("apply"), pygame.Rect(w // 2 - 60, h - 80, 120, 40), self._apply))

        # accessibility tab ---------------------------------------------
        ay = 80
        self.access_widgets.append(
            Slider(pygame.Rect(40, ay, 200, 20), 100, 200, max(1.0, self.cfg.get("ui_scale", 1.0)) * 100, self._on_scale)
        )
        ay += 40
        self.access_widgets.append(
            LargeTextToggle(pygame.Rect(40, ay, 260, 32), self.cfg.get("large_text", False), self._on_large_text)
        )
        ay += 40
        self.access_widgets.append(
            Toggle(_("subtitles"), pygame.Rect(40, ay, 260, 32), self.cfg.get("subtitles", False), self._on_subtitles)
        )
        ay += 40
        self.access_widgets.append(
            Toggle(
                _("dyslexia_font"),
                pygame.Rect(40, ay, 260, 32),
                self.cfg.get("dyslexia_font", False),
                self._on_dyslexia,
            )
        )
        ay += 40
        self.access_widgets.append(
            Toggle(
                _("high_contrast"),
                pygame.Rect(40, ay, 260, 32),
                self.cfg.get("theme") == "high_contrast",
                self._on_high_contrast,
            )
        )
        ay += 40
        self.access_widgets.append(
            Toggle(
                _("invert_zoom"),
                pygame.Rect(40, ay, 260, 32),
                self.cfg.get("invert_zoom", False),
                self._on_invert_zoom,
            )
        )

    # callbacks ----------------------------------------------------------
    def _on_volume(self, channel: str, value: float) -> None:
        vol = round(value / 100.0, 2)
        self.cfg[f"volume_{channel}"] = vol
        if channel == "master":
            # legacy key used by menu scene
            self.cfg["volume"] = vol
        sfx.set_volume(vol, channel)

    def _on_scale(self, value: float) -> None:
        self.cfg["ui_scale"] = max(1.0, round(value / 100.0, 2))

    def _on_lang(self, value: str) -> None:
        self.cfg["lang"] = value
        i18n.set_language(value)

    def _on_theme(self, value: str) -> None:
        self.cfg["theme"] = value
        set_theme(value)

    def _on_minimap(self, value: bool) -> None:
        self.cfg["minimap_enabled"] = value

    def _on_minimap_size(self, value: float) -> None:
        self.cfg["minimap_size"] = int(value)

    def _on_tel_opt(self, value: bool) -> None:
        self.cfg["telemetry_opt_in"] = value

    def _on_endpoint(self, value: str) -> None:
        self.cfg["telemetry_endpoint"] = value

    def _on_conflict_policy(self, value: str) -> None:
        self.cfg["save_conflict_policy"] = value

    def _on_fx_toggle(self, key: str, value: bool) -> None:
        self.cfg[f"fx_{key}" if key != "color" else "fx_color"] = value

    def _on_fx_intensity(self, key: str, value: float) -> None:
        self.cfg[f"fx_{key}_intensity"] = round(value / 100.0, 2)

    def _on_curve(self, idx: int, value: float) -> None:
        curve = self.cfg.get("fx_color_curve", [1.0, 1.0, 1.0])
        curve[idx] = round(value / 100.0, 2)
        self.cfg["fx_color_curve"] = curve

    def _on_high_contrast(self, value: bool) -> None:
        self.cfg["theme"] = "high_contrast" if value else "dark"
        set_theme(self.cfg["theme"])

    def _on_subtitles(self, value: bool) -> None:
        self.cfg["subtitles"] = value

    def _on_dyslexia(self, value: bool) -> None:
        self.cfg["dyslexia_font"] = value

    def _set_tab(self, name: str) -> None:
        self.widgets = self.general_widgets if name == "general" else self.access_widgets

    def _on_invert_zoom(self, value: bool) -> None:
        self.cfg["invert_zoom"] = value
        self.input.invert_zoom = value

    def _on_large_text(self, value: bool) -> None:
        self.cfg["large_text"] = value

    def _send_test_event(self) -> None:
        from telemetry import send, events

        send(events.perf_tick(0, 0, 0, self.app.screen.get_size()))

    def _apply(self) -> None:
        w, h = self.cfg.get("window_size", self.app.screen.get_size())
        self.cfg["window_size"] = [max(320, int(w)), max(240, int(h))]
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
        self.btn_general.handle_event(event)
        self.btn_access.handle_event(event)
        for w in self.widgets:
            w.handle_event(event)

    def update(self, dt: float) -> None:  # pragma: no cover - nothing dynamic
        pass

    def draw(self, surface: pygame.Surface) -> None:
        from .ui.theme import get_theme

        surface.fill(get_theme().colors["bg"])
        self.btn_general.draw(surface)
        self.btn_access.draw(surface)
        for w in self.widgets:
            w.draw(surface)
        hover_hints.draw(surface)
