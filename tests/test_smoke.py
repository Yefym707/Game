from __future__ import annotations

import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))

from gamecore import ai, board, rules, saveio


def test_smoke(tmp_path):
    rules.set_seed(42)
    state = board.create_game(width=8, height=8, zombies=2)
    for _ in range(4):
        direction = rules.RNG.choice(list(rules.DIRECTIONS))
        board.player_move(state, direction)
        ai.zombie_turns(state)
        board.end_turn(state)
    path = tmp_path / "save.json"
    saveio.save_game(state, path)
    loaded = saveio.load_game(path)
    assert [(p.x, p.y) for p in loaded.players] == [
        (p.x, p.y) for p in state.players
    ]
    assert loaded.active == state.active
    assert len(loaded.zombies) == len(state.zombies)
    for z1, z2 in zip(loaded.zombies, state.zombies):
        assert (z1.x, z1.y) == (z2.x, z2.y)
    ai.zombie_turns(loaded)
    board.end_turn(loaded)
