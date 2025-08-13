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


def test_jump_stays_within_bounds() -> None:
    cam = SmoothCamera((200, 200), (20 * TILE_SIZE, 20 * TILE_SIZE))
    cam.jump_to((-5, -5))
    assert cam.x >= 0 and cam.y >= 0
    cam.jump_to((50, 50))
    max_x = max(0.0, cam.world_w - cam.screen_w / cam.zoom)
    max_y = max(0.0, cam.world_h - cam.screen_h / cam.zoom)
    assert cam.x <= max_x and cam.y <= max_y
