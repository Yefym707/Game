from __future__ import annotations

"""Simple ban list handling."""

import json
import time
from pathlib import Path
from typing import Dict, Optional


class BanList:
    def __init__(self, path: str | Path = "data/banlist.json") -> None:
        self.path = Path(path)
        self.bans: Dict[str, float | None] = {}
        self.load()

    def load(self) -> None:
        if self.path.exists():
            try:
                self.bans = json.loads(self.path.read_text())
            except Exception:
                self.bans = {}
        else:
            self.bans = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.bans))

    def ban_ip(self, ip: str, *, seconds: Optional[int] = None) -> None:
        until = time.time() + seconds if seconds else None
        self.bans[ip] = until
        self.save()

    def is_banned(self, ip: str) -> bool:
        until = self.bans.get(ip)
        if until is None:
            return ip in self.bans
        if until < time.time():
            self.bans.pop(ip, None)
            self.save()
            return False
        return True

__all__ = ["BanList"]
