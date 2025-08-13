import json
from pathlib import Path

from gamecore import board, saveio, save_conflict, config


def test_backup_created(tmp_path, monkeypatch):
    # redirect home to temp path
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    state = board.create_game()
    path = tmp_path / "save.json"
    saveio.save_game(state, path)
    # second save should create backup
    state.turn += 1
    saveio.save_game(state, path)
    backups = home / ".oko_zombie" / "backups"
    assert list(backups.rglob("save.json*"))


def test_policy_resolution(tmp_path):
    local = save_conflict.SaveMeta(0, 1, 0, 0, 0, 1, "a")
    cloud = save_conflict.SaveMeta(0, 2, 0, 0, 0, 1, "b")
    assert save_conflict.resolve(local, cloud, "prefer_local") == "local"
    assert save_conflict.resolve(local, cloud, "prefer_cloud") == "cloud"
    assert save_conflict.resolve(local, cloud, "ask") == "cloud"
