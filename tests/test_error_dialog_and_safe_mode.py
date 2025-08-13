import os
import pathlib
import sys
import types

import pytest

BASE = pathlib.Path(__file__).resolve().parents[1]
if str(BASE / "src") not in sys.path:
    sys.path.insert(0, str(BASE / "src"))
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))


def test_error_dialog_and_safe_mode(tmp_path, monkeypatch):
    pygame = pytest.importorskip("pygame")
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    pygame.init()
    pygame.display.init()
    pygame.font.init()

    # stub optional modules used during init
    stub_replay = types.ModuleType("client.scene_replay")
    stub_replay.ReplayScene = object
    sys.modules["client.scene_replay"] = stub_replay
    stub_photo = types.ModuleType("client.scene_photo")
    stub_photo.PhotoScene = object
    sys.modules["client.scene_photo"] = stub_photo
    monkeypatch.setattr("client.app.telemetry_init", lambda cfg: None)
    monkeypatch.setattr("client.app.telemetry_shutdown", lambda reason: None)
    monkeypatch.setattr("client.app.steam.on_join_request", lambda cb: None)
    monkeypatch.setattr("client.app.ui_theme.set_theme", lambda theme: None)
    monkeypatch.setattr("client.app.postfx.count_enabled", lambda cfg: 0)

    # track sfx.init usage
    init_called = {"called": False}

    def fake_sfx_init(cfg):
        init_called["called"] = True

    monkeypatch.setattr("client.app.sfx.init", fake_sfx_init)

    # minimal configuration
    cfg_container: list[dict] = []

    def fake_load_config():
        cfg = {
            "fx_preset": "HIGH",
            "audio_enabled": True,
            "disable_online": False,
            "ui_theme": "dark",
            "language": "en",
        }
        cfg_container.append(cfg)
        return cfg

    monkeypatch.setattr("client.app.gconfig.load_config", fake_load_config)

    # force the loop to raise
    def boom(self):  # pragma: no cover - behaviour under test
        raise RuntimeError("kaboom")

    monkeypatch.setattr("client.app.App._loop", boom)

    # stub modal error to capture details and stop after one iteration
    called = {}

    class DummyModal:
        def __init__(self, message, details, buttons):
            called["message"] = message
            called["details"] = details
            called["buttons"] = buttons

        def run(self, surface):
            return "quit"

    monkeypatch.setattr("client.app.ModalError", DummyModal)

    from client.app import main

    main(safe_mode=True)

    # log file created with traceback
    log_file = tmp_path / ".oko_zombie" / "logs" / "app.log"
    assert log_file.exists()
    assert "RuntimeError" in log_file.read_text()

    # modal received details
    assert "kaboom" in called["details"]

    # safe mode adjusted config and skipped audio
    assert any(c["fx_preset"] == "OFF" for c in cfg_container)
    assert any(c["audio_enabled"] is False for c in cfg_container)
    assert any(c["disable_online"] is True for c in cfg_container)
    assert init_called["called"] is False
