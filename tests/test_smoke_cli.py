from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))

from gamecore import board, cli


def test_smoke_cli(monkeypatch):
    created = {}
    real_create = board.create_game

    def fake_create_game(*args, **kwargs):
        state = real_create(*args, **kwargs)
        created['state'] = state
        return state

    monkeypatch.setattr(board, 'create_game', fake_create_game)

    inputs = iter(['d', 's', 'a', 'q'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    cli.main(['--seed', '1'])
    assert created['state'].turn == 3
