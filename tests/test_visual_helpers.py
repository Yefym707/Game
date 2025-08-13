import os
import sys
import pathlib
import pygame

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.extend([str(ROOT), str(ROOT / "src")])
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame.init()

import types

dummy_replay = types.ModuleType("scene_replay")
dummy_replay.ReplayScene = type("ReplayScene", (), {})
sys.modules["src.client.scene_replay"] = dummy_replay

dummy_photo = types.ModuleType("scene_photo")
dummy_photo.PhotoScene = type("PhotoScene", (), {})
sys.modules["src.client.scene_photo"] = dummy_photo

from src.client.gfx import anim
from src.client import scene_game
from src.client.ui import widgets


def test_float_text_and_highlights_smoke() -> None:
    pygame.init()
    surf = pygame.Surface((100, 100), pygame.SRCALPHA)
    ft = anim.FloatText("1", (10.5, 10.5))
    ft.update(0.1)
    ft.draw(surf)

    scene = scene_game.GameScene.__new__(scene_game.GameScene)
    scene.camera = type("Cam", (), {"zoom": 1.0, "world_to_screen": lambda self, p: p})()
    player = type("P", (), {"x": 0, "y": 0})()
    zombie = type("Z", (), {"x": 1, "y": 0})()
    scene.state = type("State", (), {"active": 0, "players": [player], "zombies": [zombie]})()
    scene.hover_tile = (2, 0)
    scene._simple_path = scene_game.GameScene._simple_path.__get__(scene, scene_game.GameScene)

    scene._draw_highlights(surf)

    focus = widgets.FocusRing(pygame.Rect(0, 0, 10, 10))
    hover = widgets.HoverOutline(pygame.Rect(0, 0, 10, 10))
    icon = widgets.IconLabel("★", "")
    focus.draw(surf)
    hover.draw(surf)
    icon.draw(surf, (0, 0))
