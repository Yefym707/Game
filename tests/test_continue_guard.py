import sys
import types
import pathlib

import pytest

BASE = pathlib.Path(__file__).resolve().parents[1]
if str(BASE / "src") not in sys.path:
    sys.path.insert(0, str(BASE / "src"))
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))


def test_continue_guard(tmp_path, monkeypatch):
    pygame = pytest.importorskip("pygame")
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    pygame.init()
    pygame.display.init()
    pygame.font.init()

    # stub heavy scene modules referenced at runtime
    mod_new = types.ModuleType("client.scene_newgame")
    class DummyNew:
        def __init__(self, app):
            self.app = app
    mod_new.NewGameScene = DummyNew
    sys.modules["client.scene_newgame"] = mod_new

    mod_game = types.ModuleType("client.scene_game")
    class DummyGame:
        def __init__(self, app, new_game=False):
            self.app = app
            self.new_game = new_game
    mod_game.GameScene = DummyGame
    sys.modules["client.scene_game"] = mod_game

    from client.scene_menu import MenuScene

    app = types.SimpleNamespace(screen=pygame.Surface((100, 100)))
    menu = MenuScene(app)

    # force continue to fail
    monkeypatch.setattr("gamecore.saveio.last_slot", lambda: 1)
    def bad_load(slot):
        raise ValueError("corrupt")
    monkeypatch.setattr("gamecore.saveio.load", bad_load)

    menu._continue()
    assert menu.next_scene is None
    assert menu.error_modal is not None

    menu.error_modal.on_yes()
    assert menu.error_modal is None
    assert isinstance(menu.next_scene, DummyNew)

