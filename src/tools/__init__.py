"""Runtime shim for optional developer tools.

This package provides a safe stub for ``import tools`` in release builds
where the developer-only ``tools`` package is absent.  The shim exposes
no-op placeholders for common entry points and lazily proxies to real
modules if a ``tools`` directory exists next to the project root.
"""
from __future__ import annotations

from importlib import import_module
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


class _Noop:
    """Object that ignores all calls and attribute access."""

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        return None

    def __getattr__(self, name: str) -> "_Noop":
        return self


# Extend import search path with the developer ``tools`` directory if it exists
_DEV_DIR = Path(__file__).resolve().parents[2] / "tools"
if _DEV_DIR.is_dir():
    __path__.append(str(_DEV_DIR))  # type: ignore[name-defined]


def _load(name: str) -> Any:
    try:
        module = import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    except Exception:
        log.warning("[tools shim] missing tools.%s", name)
        obj = _Noop()
        globals()[name] = obj
        return obj


# Commonly expected helpers -------------------------------------------------
profiler = _load("profiler")
build = _load("build")
assets = _load("assets")
misc = _load("misc")


def __getattr__(name: str) -> Any:
    return _load(name)


__all__ = ["_Noop", "profiler", "build", "assets", "misc"]
