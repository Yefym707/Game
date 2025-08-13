import os
import sys
import pathlib
import pygame
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.extend([str(ROOT), str(ROOT / "src")])
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame.init()
from src.client.ui.theme import set_theme, get_theme
from src.client.ui.widgets import SubtitleBar, HelpOverlay
from src.client.input import InputManager


def test_accessibility_flags():
    set_theme("high_contrast")
    th = get_theme()
    assert th.border_width >= 2

    cfg = {"ui_scale": 2.0, "subtitles": True}
    app = type("App", (), {"cfg": cfg, "screen": pygame.Surface((640, 480)), "input": InputManager(cfg)})
    sb = SubtitleBar()
    sb.show("test")
    sb.update(0.1)
    ho = HelpOverlay(app.input)
    ho.toggle()
    ho.draw(pygame.Surface((100, 100)))
