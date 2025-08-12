from __future__ import annotations

import os
import pathlib
import sys
import types

import pytest

BASE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'src'))
sys.path.insert(0, str(BASE))


def test_smoke_gui(tmp_path, monkeypatch):
    pygame = pytest.importorskip('pygame')
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER', 'dummy')
    monkeypatch.setenv('HOME', str(tmp_path))
    pygame.init()
    pygame.font.init()

    stub_replay = types.ModuleType('client.scene_replay')
    stub_replay.ReplayScene = object
    sys.modules['client.scene_replay'] = stub_replay
    stub_photo = types.ModuleType('client.scene_photo')
    stub_photo.PhotoScene = object
    sys.modules['client.scene_photo'] = stub_photo

    from client.app import App
    from client.scene_game import GameScene
    from gamecore import board, ai, rules

    rules.set_seed(0)
    app = App(200, 150)
    scene = GameScene(app, new_game=True)
    app.scene = scene

    for _ in range(3):
        direction = rules.RNG.choice(list(rules.DIRECTIONS))
        board.player_move(scene.state, direction)
        ai.zombie_turns(scene.state)
        board.end_turn(scene.state)
        scene.update(0.016)
        scene.draw(app.screen)

    pygame.event.post(pygame.event.Event(pygame.QUIT))
    pygame.quit()
