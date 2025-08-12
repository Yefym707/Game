from __future__ import annotations

"""Server side handling of player reports."""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict

from .security import RateLimiter


class ReportManager:
    def __init__(self, root: str | Path = "data/reports") -> None:
        self.root = Path(root)
        self.rate = RateLimiter(5, 60.0)  # max 5 reports per minute per server

    def submit(self, report: Dict[str, str]) -> Path:
        if not self.rate.hit():
            raise ValueError("too many reports")
        self.root.mkdir(parents=True, exist_ok=True)
        fname = datetime.utcfromtimestamp(time.time()).strftime("%Y%m%d") + ".jsonl"
        path = self.root / fname
        with path.open("a", encoding="utf8") as fh:
            fh.write(json.dumps(report, ensure_ascii=False) + "\n")
        return path

__all__ = ["ReportManager"]
