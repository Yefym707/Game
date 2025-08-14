import os
import sys
import pathlib

import pygame

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.extend([str(ROOT), str(ROOT / "src")])

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame.init()
pygame.font.init()

import client.app as app_module  # noqa: E402  pylint: disable=wrong-import-position
from client.app import App  # noqa: E402  pylint: disable=wrong-import-position
import client.scene_settings as scene_settings  # noqa: E402  pylint: disable=wrong-import-position
from client.scene_menu import MenuScene  # noqa: E402  pylint: disable=wrong-import-position
from client.input import InputManager  # noqa: E402  pylint: disable=wrong-import-position
from client.ui import widgets  # noqa: E402  pylint: disable=wrong-import-position


def test_theme_and_scale_applied(monkeypatch) -> None:
    theme_calls: list[str] = []
    scale_calls: list[float] = []

    monkeypatch.setattr(app_module.ui_theme, "set_theme", lambda t: theme_calls.append(t))

    def fake_init(scale: float = 1.0) -> None:
        scale_calls.append(scale)
        widgets.init_ui(scale)

    monkeypatch.setattr(app_module, "init_ui", fake_init)

    cfg = {"ui_theme": "dark", "ui_scale": 1.0}
    monkeypatch.setattr(scene_settings.gconfig, "DEFAULT_SAVE_CONFLICT_POLICY", "ask", False)
    app = App(cfg)
    app.input = InputManager(cfg)
    settings = scene_settings.SettingsScene(app)
    app.scene = settings

    cfg["ui_theme"] = "light"
    cfg["ui_scale"] = 2.0
    settings.next_scene = MenuScene(app)
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    app._loop()

    assert theme_calls and theme_calls[-1] == "light"
    assert scale_calls and scale_calls[-1] == 2.0


def test_rebind_button_saves(monkeypatch) -> None:
    widgets.init_ui()
    cfg: dict[str, object] = {}
    app = type(
        "A",
        (),
        {"cfg": cfg, "input": InputManager(cfg), "screen": pygame.display.set_mode((10, 10))},
    )()
    monkeypatch.setattr(scene_settings.gconfig, "DEFAULT_SAVE_CONFLICT_POLICY", "ask", False)
    scene = scene_settings.SettingsScene(app)

    saved = []
    monkeypatch.setattr(scene_settings.gconfig, "save_config", lambda c: saved.append(True))

    btn = next(w for w in scene.general_widgets if isinstance(w, widgets.RebindButton))
    btn.listening = True
    btn.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z))

    assert saved
    assert app.cfg["bindings"]["0"][btn.action] == pygame.K_z

