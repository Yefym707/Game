from __future__ import annotations

import pathlib
import sys

# ensure src on path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from client.input import InputManager  # noqa
from gamecore import config as gconfig  # noqa


def test_rebind_and_serialize(tmp_path, monkeypatch):
    # redirect configuration paths to temporary directory
    monkeypatch.setattr(gconfig, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(gconfig, "SAVE_DIR", tmp_path / "saves")
    monkeypatch.setattr(gconfig, "CONFIG_FILE", tmp_path / "config.json")

    cfg = gconfig.load_config()
    mgr = InputManager(cfg)

    # rebind end_turn action
    mgr.rebind("end_turn", ord("x"))
    mgr.save(cfg)
    gconfig.save_config(cfg)

    # reload and ensure binding persisted
    cfg2 = gconfig.load_config()
    mgr2 = InputManager(cfg2)
    assert mgr2.bindings["end_turn"] == ord("x")
