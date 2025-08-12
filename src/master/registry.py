"""In-memory registry of active game servers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Callable
import time
import uuid


@dataclass
class LobbyInfo:
    """Information about a single lobby entry."""

    host: str
    port: int
    name: str
    mode: str
    max_players: int
    cur_players: int
    region: str
    build: str
    protocol: int

    def to_dict(self) -> Dict[str, object]:
        return {
            "host": self.host,
            "port": self.port,
            "name": self.name,
            "mode": self.mode,
            "max_players": self.max_players,
            "cur_players": self.cur_players,
            "region": self.region,
            "build": self.build,
            "protocol": self.protocol,
        }


@dataclass
class _Entry:
    info: LobbyInfo
    last_seen: float = field(default_factory=lambda: time.time())


class MasterRegistry:
    """Track registered game servers and purge stale ones."""

    def __init__(self, timeout: float = 45.0, time_func: Callable[[], float] = time.time) -> None:
        self._timeout = timeout
        self._time = time_func
        self._entries: Dict[str, _Entry] = {}

    # -- internal helpers -------------------------------------------------
    def _purge(self) -> None:
        now = self._time()
        stale = [sid for sid, entry in self._entries.items() if now - entry.last_seen > self._timeout]
        for sid in stale:
            self._entries.pop(sid, None)

    # -- public API -------------------------------------------------------
    def register(self, info: LobbyInfo) -> str:
        """Add a new lobby to the registry returning its ``server_id``."""

        server_id = uuid.uuid4().hex
        self._entries[server_id] = _Entry(info, self._time())
        return server_id

    def heartbeat(self, server_id: str, cur_players: int) -> None:
        entry = self._entries.get(server_id)
        if not entry:
            raise KeyError("unknown server_id")
        entry.info.cur_players = cur_players
        entry.last_seen = self._time()

    def unregister(self, server_id: str) -> None:
        self._entries.pop(server_id, None)

    def list(self, mode: Optional[str] = None, region: Optional[str] = None,
             build: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, object]]:
        self._purge()
        entries: Iterable[tuple[str, _Entry]] = self._entries.items()
        result: List[Dict[str, object]] = []
        for sid, entry in entries:
            info = entry.info
            if mode and info.mode != mode:
                continue
            if region and info.region != region:
                continue
            if build and info.build != build:
                continue
            item = info.to_dict()
            item["server_id"] = sid
            result.append(item)
            if limit is not None and len(result) >= limit:
                break
        return result


__all__ = ["LobbyInfo", "MasterRegistry"]
