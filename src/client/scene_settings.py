"""Settings menu scene."""
from __future__ import annotations

import pygame

from gamecore.i18n import gettext as _
from gamecore import config as gconfig
from .app import Scene
from .ui.widgets import Button


class SettingsScene(Scene):
    """Allow the player to tweak basic configuration options."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self.cfg = gconfig.load_config()
        width, height = app.screen.get_size()
        cx = width // 2 - 100
        y = 120
        self.buttons: list[Button] = []

        def add(name: str, cb) -> Button:
            nonlocal y
            rect = pygame.Rect(cx, y, 200, 40)
            btn = Button("", rect, cb)
            setattr(self, name, btn)
            self.buttons.append(btn)
            y += 60
            return btn

        add("btn_volume", self.change_volume)
        add("btn_lang", self.change_lang)
        add("btn_window", self.change_window)
        add("btn_fullscreen", self.toggle_fullscreen)
        add("btn_back", self.back)
        self._update_texts()

    # helpers ------------------------------------------------------------
    def _update_texts(self) -> None:
        self.btn_volume.text = f"Volume: {int(self.cfg['volume'] * 100)}%"
        self.btn_lang.text = f"Language: {self.cfg['lang']}"
        ws = self.cfg["window_size"]
        self.btn_window.text = f"Window: {ws[0]}x{ws[1]}"
        self.btn_fullscreen.text = f"Fullscreen: {'on' if self.cfg['fullscreen'] else 'off'}"
        self.btn_back.text = "Back"

    # button callbacks --------------------------------------------------
    def change_volume(self) -> None:
        vol = self.cfg["volume"] + 0.1
        if vol > 1.0:
            vol = 0.0
        self.cfg["volume"] = round(vol, 2)
        self._update_texts()
        try:
            pygame.mixer.music.set_volume(self.cfg["volume"])
        except Exception:
            pass

    def change_lang(self) -> None:
        self.cfg["lang"] = "ru" if self.cfg.get("lang") == "en" else "en"
        self._update_texts()

    def change_window(self) -> None:
        sizes = [(800, 600), (1024, 768), (1280, 720)]
        current = tuple(self.cfg["window_size"])
        if current in sizes:
            idx = (sizes.index(current) + 1) % len(sizes)
        else:
            idx = 0
        self.cfg["window_size"] = list(sizes[idx])
        flags = pygame.FULLSCREEN if self.cfg.get("fullscreen") else 0
        pygame.display.set_mode(tuple(self.cfg["window_size"]), flags)
        self._update_texts()

    def toggle_fullscreen(self) -> None:
        self.cfg["fullscreen"] = not self.cfg.get("fullscreen")
        flags = pygame.FULLSCREEN if self.cfg["fullscreen"] else 0
        pygame.display.set_mode(tuple(self.cfg["window_size"]), flags)
        self._update_texts()

    def back(self) -> None:
        gconfig.save_config(self.cfg)
        from .scene_menu import MenuScene

        self.next_scene = MenuScene(self.app)

    # scene API ---------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        for btn in self.buttons:
            btn.handle_event(event)

    def update(self, dt: float) -> None:  # pragma: no cover - nothing to update
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((25, 25, 25))
        for btn in self.buttons:
            btn.draw(surface)
