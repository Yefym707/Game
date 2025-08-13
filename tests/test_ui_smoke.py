import os
import sys
import pathlib
import pygame

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.extend([str(ROOT), str(ROOT / "src")])
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame.init()
pygame.font.init()

from client.app import App
from client.gfx.camera import SmoothCamera
from client.gfx.tileset import TILE_SIZE
from client.ui import widgets
from client.scene_game import GameScene
from gamecore import board as gboard


def test_ui_smoke() -> None:
    widgets.init_ui()
    widgets.hover_hints[:] = ["h1", "h2"]

    app = App({})
    scene = GameScene(app, new_game=True)
    app.scene = scene

    surf = pygame.Surface((200, 150))

    panel = widgets.Panel(pygame.Rect(0, 0, 20, 20))
    label = widgets.Label("lbl", pygame.Rect(0, 0, 20, 10))
    btn = widgets.Button("ok", pygame.Rect(0, 0, 20, 10), lambda: None)
    toast = widgets.Toast("msg")
    tooltip = widgets.Tooltip("tip")

    panel.draw(surf)
    label.draw(surf)
    btn.draw(surf)
    toast.draw(surf, 40)
    tooltip.draw(surf, (5, 5))

    ho = widgets.HelpOverlay(app.input_map)
    ho.toggle()
    ho.draw(surf)

    cam = SmoothCamera((100, 100), (10 * TILE_SIZE, 10 * TILE_SIZE))
    board = gboard.Board.generate(10, 10)
    mm = widgets.MinimapWidget(pygame.Rect(0, 0, 50, 50), board, cam)
    mm.draw(surf)
    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(25, 25), button=1)
    mm.handle_event(ev)
    cx, cy = int(cam.x // TILE_SIZE), int(cam.y // TILE_SIZE)
    assert 0 <= cx < board.width and 0 <= cy < board.height

    scene.draw(app.screen)
