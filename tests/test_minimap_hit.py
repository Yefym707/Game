import os
import sys
import pathlib
import pygame

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.extend([str(ROOT), str(ROOT / "src")])
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame.init()

from src.client.gfx.camera import SmoothCamera
from src.client.gfx.tileset import TILE_SIZE
from src.client.ui import widgets


def test_minimap_click_and_draw() -> None:
    cam = SmoothCamera((100, 100), (10 * TILE_SIZE, 10 * TILE_SIZE))
    mini = widgets.Minimap(pygame.Rect(0, 0, 100, 100), (10, 10), cam)

    # click roughly in the centre -> cell (5,5)
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(50, 50), button=1)
    mini.handle_event(event)
    assert int(cam.x) == 5 * TILE_SIZE - cam.screen_w // 2
    assert int(cam.y) == 5 * TILE_SIZE - cam.screen_h // 2

    # drawing the minimap renders the current view rectangle in white
    surf = pygame.Surface((100, 100))
    mini.draw(surf)
    vx = int((cam.x / cam.world_w) * mini.rect.width)
    vy = int((cam.y / cam.world_h) * mini.rect.height)
    assert surf.get_at((vx, vy))[:3] == (255, 255, 255)
