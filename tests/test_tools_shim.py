import importlib
import sys
from pathlib import Path


def _import_shim(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    monkeypatch.syspath_prepend(str(src))
    monkeypatch.delitem(sys.modules, "tools", raising=False)
    return importlib.import_module("tools")


def test_noop_available(monkeypatch):
    tools = _import_shim(monkeypatch)
    assert tools.profiler.start() is None
    assert tools.profiler.stop() is None


def test_proxy_real_module(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    profiler_file = root / "tools" / "profiler.py"
    profiler_file.write_text(
        "def start():\n    return 'started'\n\n"
        "def stop():\n    return 'stopped'\n",
        encoding="utf-8",
    )
    try:
        tools = _import_shim(monkeypatch)
        assert tools.profiler.start() == "started"
        assert tools.profiler.stop() == "stopped"
    finally:
        monkeypatch.delitem(sys.modules, "tools.profiler", raising=False)
        profiler_file.unlink()
        cache = profiler_file.parent / "__pycache__"
        if cache.exists():
            for f in cache.glob("profiler.*"):
                f.unlink()
            try:
                cache.rmdir()
            except OSError:
                pass
