from __future__ import annotations

import pathlib
import sys
import os
import gc

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))

from gamecore import board, ai, rules


def _rss_mb() -> float:
    with open('/proc/self/statm') as fh:
        rss = int(fh.readline().split()[1]) * os.sysconf('SC_PAGE_SIZE')
    return rss / (1024 * 1024)


def test_memleak():
    rules.set_seed(0)
    start_mem = _rss_mb()
    for _ in range(100):
        state = board.create_game()
        ai.zombie_turns(state)
        board.end_turn(state)
        del state
        gc.collect()
    end_mem = _rss_mb()
    allowed = start_mem * 0.05 + 5
    assert end_mem - start_mem <= allowed
