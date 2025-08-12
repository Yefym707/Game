from __future__ import annotations

import sys
import pathlib
import os

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))

from gamecore import board, rules
from replay.recorder import Recorder
from replay.player import Player


def test_replay_roundtrip(tmp_path):
    os.environ["REPLAY_HMAC_KEY"] = "secret"
    rules.set_seed(1)
    state = board.create_game(players=1)
    path = tmp_path / 'rep.jsonl'
    rec = Recorder(path)
    rec.start({'seed': 1, 'mode': state.mode.name})
    rec.checkpoint(state)

    board.player_move(state, 'd')
    rec.record({'type': 'MOVE', 'turn': state.turn, 'player': 0, 'dir': 'd'})
    board.end_turn(state)
    rec.checkpoint(state)

    board.player_move(state, 's')
    rec.record({'type': 'MOVE', 'turn': state.turn, 'player': 0, 'dir': 's'})
    board.end_turn(state)
    rec.checkpoint(state)

    rec.stop()

    ply = Player.load(path)
    s1 = ply.seek(1)
    s2 = ply.seek(2)
    assert s1.turn == 1
    assert s2.turn == 2
    assert (s1.players[0].x, s1.players[0].y) == (1, 0)
    assert (s2.players[0].x, s2.players[0].y) == (1, 1)

    lines = path.read_text().splitlines()
    lines[3] = lines[3].replace('"d"', '"l"')
    path.write_text("\n".join(lines) + "\n")
    with pytest.raises(ValueError):
        Player.load(path)
