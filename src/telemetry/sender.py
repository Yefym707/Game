from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from gamecore.config import CONFIG_DIR

TELEMETRY_DIR = CONFIG_DIR / "telemetry"


class TelemetrySender:
    """Queue based telemetry sender writing unsent events to disk."""

    def __init__(self, endpoint: str, anon_id: str) -> None:
        self.endpoint = endpoint
        self.anon_id = anon_id
        self.queue: List[Dict] = []
        self._backoff = 1.0
        self._next_attempt = 0.0
        TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
        self._load_pending()

    # ------------------------------------------------------------------
    def _load_pending(self) -> None:
        for file in TELEMETRY_DIR.glob("*.jsonl"):
            try:
                with file.open("r", encoding="utf-8") as fh:
                    for line in fh:
                        self.queue.append(json.loads(line))
                file.unlink()
            except Exception:
                pass

    # ------------------------------------------------------------------
    def send(self, event: Dict) -> None:
        event["anon_id"] = self.anon_id
        self.queue.append(event)
        self.flush()

    # ------------------------------------------------------------------
    def flush(self) -> None:
        if not self.endpoint:
            self.queue.clear()
            return
        if time.time() < self._next_attempt:
            if self.queue:
                self._persist(self.queue)
                self.queue = []
            return
        remaining: List[Dict] = []
        for evt in self.queue:
            try:
                data = json.dumps(evt).encode("utf-8")
                req = urllib.request.Request(
                    self.endpoint,
                    data=data,
                    headers={"Content-Type": "application/json"},
                )
                urllib.request.urlopen(req, timeout=2)
            except Exception:
                remaining.append(evt)
        self.queue = []
        if remaining:
            self._backoff = min(self._backoff * 2, 60.0)
            self._next_attempt = time.time() + self._backoff
            self._persist(remaining)
        else:
            self._backoff = 1.0

    # ------------------------------------------------------------------
    def _persist(self, events: List[Dict]) -> None:
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        path = TELEMETRY_DIR / f"{ts}.jsonl"
        with path.open("w", encoding="utf-8") as fh:
            for evt in events:
                json.dump(evt, fh)
                fh.write("\n")
