from __future__ import annotations

import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

from gamecore.config import CONFIG_DIR
from . import breadcrumbs, events, system

CRASH_DIR = CONFIG_DIR / "crashes"


def install(sender) -> None:
    """Install a global ``sys.excepthook`` that records crashes."""

    old_hook = sys.excepthook

    def _hook(exctype, value, tb):
        report = {
            "type": "crash",
            "exc_type": exctype.__name__,
            "message": str(value),
            "stack": traceback.format_exception(exctype, value, tb),
            "breadcrumbs": breadcrumbs.get(),
            "system": system.system_info(),
        }
        CRASH_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        path = CRASH_DIR / f"{ts}.json"
        with path.open("w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        if sender:
            sender.send(report)
            sender.flush()
        old_hook(exctype, value, tb)

    sys.excepthook = _hook
