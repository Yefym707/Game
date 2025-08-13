import sys, pathlib, time
import pygame

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / 'src'))
sys.path.append(str(ROOT))

from client.gfx.tileset import Tileset, TILE_SIZE
from client.gfx.layers import Layer
from client.gfx import postfx


class DummyBoard:
    def __init__(self, w, h):
        self.tiles = [["." for _ in range(w)] for _ in range(h)]


class DummyCamera:
    def __init__(self, zoom=0.1):
        self.zoom = zoom

    def world_to_screen(self, pos):
        return (int(pos[0] * self.zoom), int(pos[1] * self.zoom))


def test_fx_off_fast():
    pygame.init()
    pygame.display.set_mode((1, 1))
    board = DummyBoard(50, 50)
    camera = DummyCamera()
    tileset = Tileset()
    if "." not in tileset.tiles:
        tileset.tiles["."] = pygame.Surface((TILE_SIZE, TILE_SIZE))
    layers = {Layer.TILE: pygame.Surface((int(50 * TILE_SIZE * camera.zoom), int(50 * TILE_SIZE * camera.zoom)), pygame.SRCALPHA)}
    frames = 5
    start = time.perf_counter()
    for _ in range(frames):
        tileset.draw_map(board, camera, layers)
        postfx.apply_preset(layers[Layer.TILE], "OFF")
    avg = (time.perf_counter() - start) / frames
    fps = 1.0 / avg if avg else float("inf")
    pygame.quit()
    assert fps >= 55
