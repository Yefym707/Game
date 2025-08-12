from __future__ import annotations

import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))

from gamecore import board, rules
from replay.recorder import Recorder
from replay.player import Player


def test_replay_loop(tmp_path):
    os.environ['REPLAY_HMAC_KEY'] = 'secret'
    rules.set_seed(0)
    state = board.create_game(players=1)
    path = tmp_path / 'rep.jsonl'
    rec = Recorder(path)
    rec.start({'seed': 0, 'mode': state.mode.name})
    rec.checkpoint(state)
    for _ in range(5):
        board.player_move(state, 'd')
        rec.record({'type': 'MOVE', 'turn': state.turn, 'player': 0, 'dir': 'd'})
        board.end_turn(state)
        rec.checkpoint(state)
    rec.stop()
    ply = Player.load(path)
    for t in range(1, 6):
        snap = ply.seek(t)
        assert snap.turn == t
