import os
import sys
import types
import pathlib
import pygame

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.extend([str(ROOT), str(ROOT / "src")])
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame.init()
pygame.font.init()

# stub optional scenes used by GameScene
stub_replay = types.ModuleType("client.scene_replay")
stub_replay.ReplayScene = object
sys.modules["client.scene_replay"] = stub_replay
stub_photo = types.ModuleType("client.scene_photo")
stub_photo.PhotoScene = object
sys.modules["client.scene_photo"] = stub_photo

from client.app import App
import client.scene_game as scene_game
from client.ui import widgets
widgets.init_ui()
scene_game.hover_hints = widgets.hover_hints
GameScene = scene_game.GameScene


def test_ui_smoke() -> None:
    """Creating scenes and basic widgets should not crash."""
    app = App(200, 150)
    scene = GameScene(app, new_game=True)
    app.scene = scene

    surf = pygame.Surface((200, 150))
    # basic widgets
    panel = widgets.Panel(pygame.Rect(0, 0, 50, 50))
    label = widgets.Label("lbl", pygame.Rect(0, 0, 40, 20))
    btn = widgets.Button("ok", pygame.Rect(0, 0, 40, 20), lambda: None)
    tooltip = widgets.Tooltip("tip")
    toast = widgets.Toast("msg")

    panel.draw(surf)
    label.draw(surf)
    btn.draw(surf)
    tooltip.draw(surf, (10, 10))
    toast.draw(surf, 100)

    ho = widgets.HelpOverlay(app.input)
    ho.toggle()
    ho.draw(surf)

    scene.draw(app.screen)
