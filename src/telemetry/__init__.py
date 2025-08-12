from __future__ import annotations

from typing import Any, Dict, Optional

from .sender import TelemetrySender
from . import events, crash

_sender: Optional[TelemetrySender] = None


def init(cfg: Dict[str, Any]) -> None:
    """Initialize telemetry based on configuration."""

    global _sender
    endpoint = cfg.get("telemetry_endpoint", "")
    opt_in = cfg.get("telemetry_opt_in", False)
    anon_id = cfg.get("telemetry_anonymous_id", "")
    if opt_in and endpoint:
        _sender = TelemetrySender(endpoint, anon_id)
        crash.install(_sender)
        _sender.send(events.session_start())
    else:
        _sender = None


def get_sender() -> Optional[TelemetrySender]:
    return _sender


def send(evt: Dict[str, Any]) -> None:
    if _sender:
        _sender.send(evt)


def shutdown(reason: str = "exit") -> None:
    """Flush queued events and send session end."""

    global _sender
    if _sender:
        _sender.send(events.session_end(reason))
        _sender.flush()
        _sender = None
