import os
import sys
import pathlib

import pygame

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.extend([str(ROOT), str(ROOT / "src")])

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame.init()

from gamecore import config as gconfig


def test_normalize_save_conflict_policy() -> None:
    norm = gconfig.normalize_save_conflict_policy
    assert norm("ask") == "ask"
    assert norm("prefer_local") == "prefer_local"
    assert norm("prefer_cloud") == "prefer_cloud"
    assert norm("WTF") == gconfig.DEFAULT_SAVE_CONFLICT_POLICY


def test_default_loaded(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(gconfig, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(gconfig, "CONFIG_FILE", tmp_path / "config.json")
    cfg = gconfig.load_config()
    assert cfg["save_conflict_policy"] == gconfig.DEFAULT_SAVE_CONFLICT_POLICY
