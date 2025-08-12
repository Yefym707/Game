from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))

from gamecore import board, rules, saveio


def test_local_coop_turns(tmp_path):
    rules.set_seed(0)
    state = board.create_game(players=3, mode=rules.GameMode.LOCAL_COOP)
    for _ in range(5):
        board.end_turn(state)
    path = tmp_path / 'coop.json'
    saveio.save_game(state, path)
    loaded = saveio.load_game(path)
    assert loaded.mode == rules.GameMode.LOCAL_COOP
    assert loaded.active == state.active
    assert [p.id for p in loaded.players] == [0, 1, 2]
