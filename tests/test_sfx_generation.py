from __future__ import annotations

import sys
import pathlib

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from client import sfx


def test_sfx_generation():
    buf = sfx.generate_buffer("sine", 440, 100, (10, 10, 0.5, 20))
    # correct length
    assert len(buf) == int(44100 * 0.1)
    assert buf.dtype == np.int16
    # start near zero due to attack and end near zero due to release
    assert abs(int(buf[0])) < 100
    assert abs(int(buf[-1])) < 100
    # amplitude within range
    assert np.max(buf) <= 32767
    assert np.max(buf) > 10000
