from __future__ import annotations

import pathlib
import sys
import time
import os

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))

from gamecore import board, ai, rules


def _rss_mb() -> float:
    with open('/proc/self/statm') as fh:
        rss = int(fh.readline().split()[1]) * os.sysconf('SC_PAGE_SIZE')
    return rss / (1024 * 1024)


def test_performance():
    rules.set_seed(0)
    state = board.create_game(width=50, height=50, zombies=0)
    frames = 60
    start = time.perf_counter()
    for _ in range(frames):
        direction = rules.RNG.choice(list(rules.DIRECTIONS))
        board.player_move(state, direction)
        ai.zombie_turns(state)
        board.end_turn(state)
    elapsed = time.perf_counter() - start
    fps = frames / elapsed
    assert fps >= 55
    assert _rss_mb() <= 500
