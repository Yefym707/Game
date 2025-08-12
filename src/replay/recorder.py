"""Utility to record deterministic game sessions."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

from . import format as fmt
from . import storage
from gamecore import saveio


class Recorder:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.fh = None

    def start(self, meta: Dict[str, Any]) -> None:
        """Begin recording and write ``meta`` information."""

        self.fh = storage.open_write(self.path)
        storage.write_jsonl(self.fh, fmt.make_header())
        storage.write_jsonl(self.fh, meta)

    def record(self, event: Dict[str, Any]) -> None:
        if not self.fh:
            raise RuntimeError("Recorder not started")
        storage.write_jsonl(self.fh, event)

    def checkpoint(self, state) -> None:
        if not self.fh:
            raise RuntimeError("Recorder not started")
        snap = saveio.snapshot(state)
        storage.write_jsonl(
            self.fh,
            {"type": "CHECKPOINT", "turn": state.turn, "state": snap},
        )

    def stop(self, path: str | Path | None = None) -> Path:
        """Finish recording and optionally move the file to ``path``."""

        if not self.fh:
            raise RuntimeError("Recorder not started")
        self.fh.close()
        self.fh = None
        final_path = Path(path) if path else self.path
        if path and final_path != self.path:
            self.path.replace(final_path)
            self.path = final_path
        return self.path
