import pathlib
import sys
import pygame
import pytest
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

stub_replay = types.ModuleType("client.scene_replay")
stub_replay.ReplayScene = object
sys.modules["client.scene_replay"] = stub_replay
stub_photo = types.ModuleType("client.scene_photo")
stub_photo.PhotoScene = object
sys.modules["client.scene_photo"] = stub_photo

pygame.init()
pygame.font.init()

from client.scene_game import GameScene
from client.gfx import postfx
from gamecore import rules


@pytest.fixture(autouse=True)
def _init_pygame(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    yield
    pygame.quit()


def _scene():
    scene = GameScene.__new__(GameScene)
    scene.cfg = {"night_vignette": 0.5}
    return scene


def test_vignette_applied_at_night(monkeypatch):
    called = {"v": False}

    def fake_vig(surf, strength, feather=0.5):
        called["v"] = True
        return surf

    monkeypatch.setattr(postfx, "vignette", fake_vig)
    monkeypatch.setattr(rules, "current_time_of_day", lambda: rules.TimeOfDay.NIGHT)
    surf = pygame.Surface((10, 10))
    _scene()._apply_postfx(surf)
    assert called["v"]


def test_vignette_skipped_in_day(monkeypatch):
    called = {"v": False}

    def fake_vig(surf, strength, feather=0.5):
        called["v"] = True
        return surf

    monkeypatch.setattr(postfx, "vignette", fake_vig)
    monkeypatch.setattr(rules, "current_time_of_day", lambda: rules.TimeOfDay.DAY)
    surf = pygame.Surface((10, 10))
    _scene()._apply_postfx(surf)
    assert not called["v"]
