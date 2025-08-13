from __future__ import annotations

"""Helpers for resolving save conflicts between local and cloud versions."""

from dataclasses import dataclass
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Dict, Literal, Optional

from integrations import steamwrap

log = logging.getLogger(__name__)

LOG_FILE = Path.home() / ".oko_zombie" / "conflict.log"


@dataclass
class SaveMeta:
    created: float
    modified: float
    duration: int
    turn: int
    seed: int
    size: int
    sha256: str

    @classmethod
    def from_dict(cls, data: Dict) -> "SaveMeta":
        return cls(
            created=float(data.get("created", 0)),
            modified=float(data.get("modified", 0)),
            duration=int(data.get("duration", 0)),
            turn=int(data.get("turn", 0)),
            seed=int(data.get("seed", 0)),
            size=int(data.get("size", 0)),
            sha256=str(data.get("sha256", "")),
        )


def read_local_meta(path: Path) -> SaveMeta:
    """Return metadata for a local save file."""

    raw = path.read_bytes()
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:  # pragma: no cover - malformed save
        data = {}
    meta = data.get("meta", {})
    stat = path.stat()
    meta.setdefault("created", stat.st_ctime)
    meta.setdefault("modified", stat.st_mtime)
    meta.setdefault("size", len(raw))
    meta.setdefault("sha256", hashlib.sha256(raw).hexdigest())
    return SaveMeta.from_dict(meta)


def read_cloud_meta(key: str) -> Optional[SaveMeta]:
    """Return metadata for a cloud save key, if available."""

    meta = steamwrap.steam.cloud_meta(key)
    if not meta:
        return None
    return SaveMeta.from_dict(meta)


def _log(choice: str, local: SaveMeta, cloud: SaveMeta) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": time.time(),
        "choice": choice,
        "local": local.__dict__,
        "cloud": cloud.__dict__,
    }
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        json.dump(entry, fh)
        fh.write("\n")


Policy = Literal["ask", "prefer_local", "prefer_cloud"]


def resolve(local: SaveMeta, cloud: SaveMeta, policy: Policy) -> str:
    """Return which version should win given ``policy``."""

    if local.sha256 == cloud.sha256:
        choice = "local"
    elif policy == "prefer_local":
        choice = "local"
    elif policy == "prefer_cloud":
        choice = "cloud"
    else:  # ask -> pick the newer one as default
        choice = "local" if local.modified >= cloud.modified else "cloud"
    _log(choice, local, cloud)
    return choice
