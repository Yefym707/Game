"""Minimal pygame application wrapper with safe mode and crash handling.

The real game boots a fairly involved stack.  For the unit tests we only need a
tiny shell that initialises pygame, manages a single scene and provides a global
exception handler.  ``main()`` takes an optional ``safe_mode`` flag which
disables audio and heavy post processing and forces a high‑contrast theme.  Any
uncaught exception is written to ``app.log`` with log rotation and displayed via
``ModalError`` which offers a *Copy details* shortcut.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
import traceback
from types import SimpleNamespace
from typing import Dict

import pygame

from gamecore.i18n import gettext as _
from gamecore import config as gconfig

from . import sfx
from .util_paths import logs_dir
from .input_map import InputMap
from .scene_menu import MenuScene
from .ui.widgets import HelpOverlay, ModalError, init_ui

# optional subsystems are represented by tiny namespaces so tests can monkeypatch
telemetry_init = lambda cfg: None
telemetry_shutdown = lambda reason: None
ui_theme = SimpleNamespace(set_theme=lambda theme: None)
postfx = SimpleNamespace(count_enabled=lambda cfg: 0)
steam = SimpleNamespace(on_join_request=lambda cb: None)


def _setup_logging() -> None:
    log_file = logs_dir() / "app.log"
    handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    logging.basicConfig(level=logging.INFO, handlers=[handler])


class App:
    """Small pygame application managing a single scene."""

    def __init__(self, cfg: Dict, safe_mode: bool = False) -> None:
        pygame.init()
        pygame.font.init()
        init_ui(cfg.get("ui_scale", 1.0))
        pygame.mouse.set_visible(True)
        self.safe_mode = safe_mode
        self.cfg = cfg
        self.screen = pygame.display.set_mode((640, 480))
        self.font = pygame.font.SysFont(None, 16)
        self.input_map = InputMap()
        self.scene = MenuScene(self)
        self.scene.enter()
        self.help = HelpOverlay(self.input_map)
        self.running = True

    # main loop ---------------------------------------------------------
    def run(self) -> None:
        self._loop()

    def _loop(self) -> None:  # pragma: no cover - exercised indirectly
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                self.handle_event(event)
            self.scene.update(0.0)
            if self.scene.next_scene:
                self.scene.exit()
                self.scene = self.scene.next_scene
                self.scene.enter()
                continue
            self.screen.fill((0, 0, 0))
            self.scene.draw(self.screen)
            if self.help.visible:
                self.help.draw(self.screen)
            pygame.display.flip()
            clock.tick(60)

    # event dispatch ----------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        action = self.input_map.map_event(event)
        if action == "help":
            self.help.toggle()
            return
        if action == "pause":
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return
        self.scene.handle_event(event)


def main(safe_mode: bool = False) -> None:
    """Entry point used by ``scripts.run_gui``."""

    _setup_logging()
    cfg = gconfig.load_config()
    if safe_mode:
        cfg["fx_preset"] = "OFF"
        cfg["audio_enabled"] = False
        cfg["disable_online"] = True
        cfg["language"] = "en"
        cfg["ui_theme"] = "high_contrast"

    try:
        telemetry_init(cfg)
        steam.on_join_request(lambda _info: None)
        ui_theme.set_theme(cfg.get("ui_theme", "dark"))
        postfx.count_enabled(cfg)
        if cfg.get("audio_enabled", True):
            sfx.init(cfg)
        app = App(cfg, safe_mode=safe_mode)
        app.run()
    except Exception:  # pragma: no cover - error handling
        logging.exception("app crash")
        pygame.init()
        pygame.font.init()
        screen = pygame.display.set_mode((640, 480))
        etype, value, tb = sys.exc_info()
        stack = "".join(traceback.format_exception(etype, value, tb))
        title = f"{etype.__name__}: {value}" if etype else _("error")
        dialog = ModalError(title, stack)
        dialog.run(screen)
    finally:  # pragma: no cover - defensive
        telemetry_shutdown("exit")


__all__ = ["App", "main"]

