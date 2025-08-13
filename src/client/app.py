"""Main pygame application and scene manager."""
from __future__ import annotations

import logging
import os
import platform
import sys
import time
import traceback

import pygame

from gamecore.i18n import gettext as _, set_language
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
from .ui.widgets import ModalError
from .scene_loading import LoadingScene
from .util_paths import logs_dir

from .scene_base import Scene

class App:
    """Pygame application managing scenes."""

    def __init__(self, width: int = 800, height: int = 600, safe_mode: bool = False) -> None:
        pygame.init()
        self.safe_mode = safe_mode
        # configuration -------------------------------------------------
        self.cfg = gconfig.load_config()
        if safe_mode:
            self.cfg["fx_preset"] = "OFF"
            self.cfg["audio_enabled"] = False
            self.cfg["disable_online"] = True
            self.cfg["ui_theme"] = "high_contrast"
            self.cfg["language"] = "en"
        set_language(self.cfg.get("language", "en"))
        ui_theme.set_theme(self.cfg.get("ui_theme", self.cfg.get("theme", "dark")))
        telemetry_init(self.cfg)
        flags = pygame.FULLSCREEN if self.cfg.get("fullscreen") else 0
        w, h = self.cfg.get("window_size", [width, height])
        pygame.display.set_caption(_("window_title"))
        self.screen = pygame.display.set_mode((w, h), flags)
        if self.cfg.get("audio_enabled", True):
            sfx.init(self.cfg)
        else:  # pragma: no cover - mixer optional
            try:
                pygame.mixer.quit()
            except Exception:
                pass
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
        while True:
            try:
                self._loop()
                break
            except Exception:
                tb = traceback.format_exc()
                logging.exception("main loop crash")
                dialog = ModalError(
                    _("error"),
                    tb,
                    [
                        ("restart", _("restart")),
                        ("quit", _("menu_quit")),
                        ("copy", _("copy_details")),
                    ],
                )
                if dialog.run(self.screen) != "restart":
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


def main(demo: bool = False, safe_mode: bool = False) -> None:
    """Entry point used by ``scripts.run_gui``."""

    log_dir = logs_dir()
    log_file = log_dir / "app.log"
    if log_file.exists() and log_file.stat().st_size > 1_000_000:
        log_file.write_text("", encoding="utf-8")
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_file)
    root_logger.addHandler(fh)
    logging.info(
        "python=%s pygame=%s os=%s cwd=%s meipass=%s safe_mode=%s",
        sys.version.split()[0],
        pygame.version.ver,
        platform.platform(),
        os.getcwd(),
        getattr(sys, "_MEIPASS", None),
        safe_mode,
    )

    if demo:
        from gamecore import rules

        rules.DEMO_MODE = True

    while True:
        try:
            App(safe_mode=safe_mode).run()
            break
        except Exception:
            tb = traceback.format_exc()
            logging.exception("startup crash")
            pygame.init()
            screen = pygame.display.set_mode((640, 480))
            dialog = ModalError(
                _("error"),
                tb,
                [
                    ("restart", _("restart")),
                    ("quit", _("menu_quit")),
                    ("copy", _("copy_details")),
                ],
            )
            if dialog.run(screen) != "restart":
                break
            pygame.quit()


if __name__ == "__main__":  # pragma: no cover
    main()
