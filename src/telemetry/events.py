from __future__ import annotations

from typing import Any, Dict

from .system import system_info


def session_start() -> Dict[str, Any]:
    info = system_info()
    return {"type": "session_start", **info}


def session_end(reason: str) -> Dict[str, Any]:
    return {"type": "session_end", "reason": reason}


def settings_changed(changes: Dict[str, Any]) -> Dict[str, Any]:
    return {"type": "settings_changed", "changes": changes}


def match_start(mode: str) -> Dict[str, Any]:
    return {"type": "match_start", "mode": mode}


def match_end(mode: str, duration: float, result: str) -> Dict[str, Any]:
    return {
        "type": "match_end",
        "mode": mode,
        "duration": duration,
        "result": result,
    }


def error(message: str, stack: str) -> Dict[str, Any]:
    return {"type": "error", "message": message, "stack": stack}


def perf_tick(fps: float, cpu: float, gpu: float, window: tuple[int, int]) -> Dict[str, Any]:
    return {
        "type": "perf_tick",
        "fps": fps,
        "cpu": cpu,
        "gpu": gpu,
        "window": list(window),
    }
