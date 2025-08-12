"""Helpers for reading and writing replay files."""
from __future__ import annotations

import json
import gzip
from pathlib import Path
from typing import IO, Iterable, Dict, Any


def open_write(path: str | Path) -> IO[str]:
    """Open ``path`` for writing, handling optional gzip compression."""

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.suffix == ".gz":
        return gzip.open(p, "wt", encoding="utf-8")
    return p.open("w", encoding="utf-8")


def open_read(path: str | Path) -> IO[str]:
    """Open ``path`` for reading, handling optional gzip compression."""

    p = Path(path)
    if p.suffix == ".gz":
        return gzip.open(p, "rt", encoding="utf-8")
    return p.open("r", encoding="utf-8")


def open_append(path: str | Path) -> IO[str]:
    """Open ``path`` for appending, handling optional gzip compression."""

    p = Path(path)
    if p.suffix == ".gz":
        return gzip.open(p, "at", encoding="utf-8")
    return p.open("a", encoding="utf-8")


def write_jsonl(fh: IO[str], obj: Dict[str, Any]) -> None:
    fh.write(json.dumps(obj) + "\n")


def read_jsonl(path: str | Path) -> Iterable[Dict[str, Any]]:
    with open_read(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)
