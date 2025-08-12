import json
from pathlib import Path

import pytest

from gamecore import balance, board, saveio


def test_default_balance_loads():
    data = balance.load_balance()
    assert data["player"]["hp"] == 20


def test_balance_validation(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"player":{"hp":-1,"damage":1},"zombie":{"hp":5,"damage":1,"agro_range":3,"limit":5}}')
    with pytest.raises(ValueError):
        balance.load_balance(bad)


def test_map_export_import(tmp_path):
    b = board.Board.generate(2, 2)
    b.tiles[0][1] = "#"
    path = tmp_path / "map.json"
    board.export_map(b, path)
    loaded = board.import_map(path)
    assert loaded.tiles == b.tiles


def test_saveio_export(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    b = board.Board.generate(1, 1)
    saveio.export_map(b, "test")
    path = Path("mods/maps/test.json")
    assert path.exists()
    loaded = board.import_map(path)
    assert loaded.tiles == b.tiles
