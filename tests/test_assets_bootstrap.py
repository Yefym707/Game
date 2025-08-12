import sys
import pathlib

root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "src"))

import pygame
from client.gfx.tileset import Tileset
from tools import build_tiles


def test_assets_bootstrap(tmp_path, monkeypatch):
    pygame.init()
    pygame.display.set_mode((1, 1))
    calls = []

    def fake_generate(path):
        calls.append(path)
        surf = pygame.Surface((1, 1))
        pygame.image.save(surf, tmp_path / "@.png")

    monkeypatch.setattr(build_tiles, "generate", fake_generate)
    Tileset(folder=tmp_path)
    assert len(calls) == 1
    Tileset(folder=tmp_path)
    assert len(calls) == 1
