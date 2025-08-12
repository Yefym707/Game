import os
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from gamecore import config as gconfig


def _prepare(tmp_path, opt_in: bool, endpoint: str):
    os.environ["HOME"] = str(tmp_path)
    import importlib

    importlib.reload(gconfig)
    cfg = gconfig.load_config()
    cfg["telemetry_opt_in"] = opt_in
    cfg["telemetry_endpoint"] = endpoint
    gconfig.save_config(cfg)
    return cfg


def test_opt_out_creates_nothing(tmp_path):
    cfg = _prepare(tmp_path, False, "")
    import telemetry
    import importlib

    importlib.reload(telemetry)
    importlib.reload(telemetry.sender)
    init, send, shutdown = telemetry.init, telemetry.send, telemetry.shutdown

    init(cfg)
    send({"type": "test"})
    shutdown("x")
    tdir = gconfig.CONFIG_DIR / "telemetry"
    assert not tdir.exists()


def test_unreachable_buffers(tmp_path):
    cfg = _prepare(tmp_path, True, "http://localhost:9")
    import telemetry
    import importlib

    importlib.reload(telemetry)
    importlib.reload(telemetry.sender)
    init, send, shutdown, events = (
        telemetry.init,
        telemetry.send,
        telemetry.shutdown,
        telemetry.events,
    )

    init(cfg)
    send(events.perf_tick(0, 0, 0, (0, 0)))
    shutdown("x")
    tdir = gconfig.CONFIG_DIR / "telemetry"
    assert tdir.exists()
    files = list(tdir.glob("*.jsonl"))
    assert files
    with files[0].open("r", encoding="utf-8") as fh:
        assert fh.readline().strip()
