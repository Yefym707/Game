"""Main pygame application and scene manager."""
from __future__ import annotations

import pygame
import time
from typing import Optional
from pathlib import Path
import logging

from gamecore.i18n import gettext as _
from gamecore import config as gconfig
from telemetry import init as telemetry_init, shutdown as telemetry_shutdown
from integrations import steam
from . import input as cinput
from .gfx.anim import FadeTransition, SlideTransition, SceneTransitions
from . import sfx
from .scene_replay import ReplayScene  # imported for routing; used by menu
from .scene_photo import PhotoScene  # imported for hotkey access
from .gfx import postfx
from .ui import theme as ui_theme
from .scene_loading import LoadingScene


class Scene:
    """Base class for scenes."""

    def __init__(self, app: "App") -> None:
        self.app = app
        self.next_scene: Optional[Scene] = None

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle pygame events."""

    def update(self, dt: float) -> None:
        """Update scene state."""

    def draw(self, surface: pygame.Surface) -> None:
        """Draw scene to the surface."""


class App:
    """Pygame application managing scenes."""

    def __init__(self, width: int = 800, height: int = 600) -> None:
        pygame.init()
        # configuration -------------------------------------------------
        self.cfg = gconfig.load_config()
        ui_theme.set_theme(self.cfg.get("theme", "dark"))
        telemetry_init(self.cfg)
        flags = pygame.FULLSCREEN if self.cfg.get("fullscreen") else 0
        w, h = self.cfg.get("window_size", [width, height])
        pygame.display.set_caption(_("window_title"))
        self.screen = pygame.display.set_mode((w, h), flags)
        sfx.init(self.cfg)
        pygame.mouse.set_visible(False)
        # unified input layer
        self.input = cinput.InputManager(self.cfg)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24)
        self.scene: Scene = LoadingScene(self)
        self.transition: FadeTransition | SlideTransition | None = None
        steam.on_join_request(self._steam_join)
        self._global_toasts: list[str] = []

    def run(self) -> None:
        log_dir = Path.home() / ".oko_zombie" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "app.log"
        if log_file.exists() and log_file.stat().st_size > 256 * 1024:
            log_file.write_text("")
        logging.basicConfig(filename=log_file, level=logging.INFO)

        while True:
            try:
                self._loop()
                break
            except Exception:  # pragma: no cover - safety net
                logging.exception("main loop crash")
                if not self._error_dialog():
                    break

        pygame.quit()
        telemetry_shutdown("quit")

    def _loop(self) -> None:
        running = True
        fps = self.cfg.get("fps_cap", 60)
        target_dt = 1.0 / fps
        prev = time.perf_counter()
        while running:
            frame_start = time.perf_counter()
            dt = frame_start - prev
            prev = frame_start
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
                    self.cfg["perf_overlay"] = not self.cfg.get("perf_overlay", False)
                if not self.transition:
                    self.scene.handle_event(event)
            if self.transition:
                self.transition.update(dt)
            else:
                self.scene.update(dt)
                if self.scene.next_scene:
                    next_scene = self.scene.next_scene
                    self.scene.next_scene = None
                    curr = self.scene.__class__.__name__
                    nxt = next_scene.__class__.__name__
                    if curr == "MenuScene" and nxt == "GameScene":
                        self.transition = SceneTransitions.fade_out(self, next_scene, 0.3)
                    elif curr == "GameScene" and nxt == "MenuScene":
                        self.transition = SceneTransitions.fade_out(self, next_scene, 0.3)
                    elif curr == "MenuScene" and nxt == "SettingsScene":
                        self.transition = SceneTransitions.slide_out(self, next_scene, 0.3)
                    elif curr == "SettingsScene" and nxt == "MenuScene":
                        self.transition = SceneTransitions.slide_in(self, next_scene, 0.3)
                    else:
                        self.transition = SceneTransitions.fade_out(self, next_scene, 0.3)
            self.scene.draw(self.screen)
            if self.transition:
                self.transition.draw(self.screen)
                if self.transition.finished:
                    self.transition = None

            fx_time = 0.0
            if postfx.count_enabled(self.cfg):
                start_fx = time.perf_counter()
                frame = self.screen.copy()
                frame = postfx.apply_chain(frame, self.cfg)
                fx_time = (time.perf_counter() - start_fx) * 1000.0
                self.screen.blit(frame, (0, 0))

            if self.cfg.get("perf_overlay"):
                txt = f"dt:{dt*1000:.1f}ms fps:{1.0/dt if dt else 0:.1f} calls:{1+postfx.count_enabled(self.cfg)} fx:{fx_time:.1f}ms"
                img = self.font.render(txt, True, (255, 255, 255))
                self.screen.blit(img, (8, 8))

            pygame.display.flip()

            elapsed = time.perf_counter() - frame_start
            delay = target_dt - elapsed
            if delay > 0:
                time.sleep(delay)

    def _error_dialog(self) -> bool:
        msg = _("error")
        font = self.font
        surface = self.screen
        surface.fill((0, 0, 0))
        txt = font.render(msg, True, (255, 0, 0))
        retry = font.render(_("restart"), True, (255, 255, 255))
        quit_txt = font.render(_("menu_quit"), True, (255, 255, 255))
        surface.blit(txt, (20, 20))
        surface.blit(retry, (20, 60))
        surface.blit(quit_txt, (20, 90))
        pygame.display.flip()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_q, pygame.K_ESCAPE):
                        return False
                    if event.key in (pygame.K_r, pygame.K_RETURN):
                        return True
            time.sleep(0.05)

    # steam integration -------------------------------------------------
    def _steam_join(self, data: str) -> None:
        from .scene_online import OnlineScene

        scene = OnlineScene(self)
        scene.join_from_invite(data)
        self.scene = scene

    # global toast helper ---------------------------------------------
    def toast(self, text: str) -> None:
        """Record a toast message (placeholder implementation)."""

        self._global_toasts.append(text)


def main(demo: bool = False) -> None:
    """Entry point used by ``scripts.run_gui``.

    Parameters
    ----------
    demo:
        When ``True`` the game runs in limited demo mode and corresponding
        restrictions are enabled.
    """

    if demo:
        from gamecore import rules

        rules.DEMO_MODE = True
    App().run()


if __name__ == "__main__":  # pragma: no cover
    main()
