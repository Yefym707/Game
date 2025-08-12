from __future__ import annotations

import pathlib
import sys
import random

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))

from gamecore import board, ai, rules, saveio


def test_save_load_fuzz(tmp_path):
    rules.set_seed(0)
    for i in range(10):
        w = random.randint(5, 8)
        h = random.randint(5, 8)
        state = board.create_game(width=w, height=h, zombies=1)
        for _ in range(5):
            direction = random.choice(list(rules.DIRECTIONS))
            board.player_move(state, direction)
            ai.zombie_turns(state)
            board.end_turn(state)
        path = tmp_path / f'state_{i}.json'
        saveio.save_game(state, path)
        loaded = saveio.load_game(path)
        assert [(p.x, p.y) for p in loaded.players] == [
            (p.x, p.y) for p in state.players
        ]
        assert loaded.active == state.active
        assert len(loaded.zombies) == len(state.zombies)
