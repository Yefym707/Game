import os
import sys
import pathlib
from types import SimpleNamespace

import pygame

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.extend([str(ROOT), str(ROOT / "src")])

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame.init()
pygame.font.init()

from client import scene_settings  # noqa: E402  pylint: disable=wrong-import-position
from client.ui import widgets  # noqa: E402  pylint: disable=wrong-import-position
from client.input_map import InputManager  # noqa: E402  pylint: disable=wrong-import-position


def test_settings_scene(monkeypatch) -> None:
    widgets.init_ui()
    monkeypatch.setattr(scene_settings.gconfig, "save_config", lambda cfg: None)
    monkeypatch.setattr(scene_settings.gconfig, "DEFAULT_SAVE_CONFLICT_POLICY", "ask", False)

    cfg: dict[str, object] = {
        "ui_theme": "dark",
        "language": "en",
        "ui_scale": 1.0,
        "large_text": False,
    }
    input_mgr = InputManager.from_config(cfg.get("keybinds"))
    app = SimpleNamespace(cfg=cfg, input=input_mgr, screen=pygame.display.set_mode((640, 480)))
    scene = scene_settings.SettingsScene(app)

    surface = pygame.Surface((640, 480))
    scene.draw(surface)

    # language dropdown --------------------------------------------------
    lang_dd = next(
        w
        for w in scene.general_widgets
        if isinstance(w, widgets.Dropdown) and w.options == [("en", "en"), ("ru", "ru")]
    )
    lang_dd.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=lang_dd.rect.center, button=1))
    pos_ru = (lang_dd.rect.x + 5, lang_dd.rect.bottom + lang_dd.row_h + lang_dd.row_h // 2)
    lang_dd.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos_ru, button=1))
    assert cfg["language"] == "ru"

    # theme dropdown -----------------------------------------------------
    theme_dd = next(
        w
        for w in scene.general_widgets
        if isinstance(w, widgets.Dropdown) and any(opt[0] == "light" for opt in w.options)
    )
    theme_dd.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=theme_dd.rect.center, button=1))
    pos_light = (theme_dd.rect.x + 5, theme_dd.rect.bottom + theme_dd.row_h // 2)
    theme_dd.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos_light, button=1))
    assert cfg["ui_theme"] == "light"

    # ui scale slider ----------------------------------------------------
    scale_slider = next(
        w
        for w in scene.general_widgets
        if isinstance(w, widgets.Slider) and w.vmin == 100 and w.vmax == 200
    )
    pos_max = (scale_slider.rect.right - 1, scale_slider.rect.centery)
    scale_slider.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos_max, button=1))
    scale_slider.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos_max, button=1))
    assert cfg["ui_scale"] == 2.0

    # large text toggle --------------------------------------------------
    scene._set_tab("access")
    scene.draw(surface)
    lt_toggle = next(w for w in scene.access_widgets if isinstance(w, widgets.LargeTextToggle))
    lt_toggle.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=lt_toggle.rect.center, button=1))
    assert cfg["large_text"] is True

