import sys
import types
import pathlib

import pytest


BASE = pathlib.Path(__file__).resolve().parents[1]
if str(BASE / "src") not in sys.path:
    sys.path.insert(0, str(BASE / "src"))


def test_continue_guard(tmp_path, monkeypatch):
    pygame = pytest.importorskip("pygame")
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.init(); pygame.display.init(); pygame.font.init()

    # stub scenes
    mod_new = types.ModuleType("client.scene_newgame")
    class DummyNew:
        def __init__(self, app):
            self.app = app
    mod_new.NewGameScene = DummyNew
    sys.modules["client.scene_newgame"] = mod_new

    mod_game = types.ModuleType("client.scene_game")
    class DummyGame:
        def __init__(self, app):
            self.app = app
    mod_game.GameScene = DummyGame
    sys.modules["client.scene_game"] = mod_game

    from client.scene_menu import MenuScene

    app = types.SimpleNamespace()
    menu = MenuScene(app)

    # pretend no save exists
    monkeypatch.setattr("gamecore.saveio.find_last_save", lambda: None)

    menu._continue()
    assert menu.next_scene is None
    assert menu.error_modal is not None
    menu.error_modal.on_yes()
    assert isinstance(menu.next_scene, DummyNew)
    assert menu.error_modal is None

    # now pretend the last save is invalid
    menu.next_scene = None
    monkeypatch.setattr("gamecore.saveio.find_last_save", lambda: 1)
    monkeypatch.setattr("gamecore.saveio.validate", lambda slot: False)

    menu._continue()
    assert menu.next_scene is None
    assert menu.error_modal is not None

