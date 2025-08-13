from __future__ import annotations

import json
import gzip
import hashlib
import logging
import shutil
import time
from pathlib import Path
from typing import Any, Dict

from . import board, rules, entities, config
from .save_migrations import apply_migrations
from integrations import steam

log = logging.getLogger(__name__)

SAVE_VERSION = 2

CLOUD_MAP_PATH = Path.home() / ".oko_zombie" / "cloud_map.json"
_cloud_map: Dict[str, str] | None = None


def _load_cloud_map() -> Dict[str, str]:
    global _cloud_map
    if _cloud_map is None:
        try:
            with CLOUD_MAP_PATH.open("r", encoding="utf-8") as fh:
                _cloud_map = json.load(fh)
        except Exception:
            _cloud_map = {}
    return _cloud_map


def _save_cloud_map() -> None:
    CLOUD_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CLOUD_MAP_PATH.open("w", encoding="utf-8") as fh:
        json.dump(_load_cloud_map(), fh)


def _cloud_key(path: Path, create: bool) -> str | None:
    cmap = _load_cloud_map()
    key = cmap.get(str(path))
    if key or not create:
        return key
    key = path.name
    cmap[str(path)] = key
    _save_cloud_map()
    return key

# Directory where user-created maps are stored
MOD_MAPS_DIR = Path("mods") / "maps"

# directory for shadow backups of overwritten saves
BACKUP_DIR = Path.home() / ".oko_zombie" / "backups"


def _shadow_backup(path: Path) -> Path | None:
    """Create a dated backup of ``path`` if it exists.

    The backup directory structure is ``~/.oko_zombie/backups/YYYYmmdd/`` and the
    file name is suffixed with the current time to avoid collisions.
    """

    if not path.exists():
        return None
    date_dir = BACKUP_DIR / time.strftime("%Y%m%d")
    date_dir.mkdir(parents=True, exist_ok=True)
    backup = date_dir / f"{path.name}.{time.strftime('%H%M%S')}"
    try:
        shutil.copy2(path, backup)
        log.info("backup created at %s", backup)
        return backup
    except Exception:  # pragma: no cover - best effort only
        return None


def save_game(state: board.GameState, path: str | Path) -> None:
    """Persist ``state`` to ``path``.

    Network matches are intentionally not saved to disk to avoid accidental
    spoilers or cheating.  The caller can still create manual snapshots by
    serialising the state with :mod:`net.serialization` if required.
    """

    if state.mode is rules.GameMode.ONLINE:
        return
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    meta = {
        "created": path.stat().st_ctime if path.exists() else time.time(),
        "modified": time.time(),
        "duration": getattr(state, "duration", 0),
        "turn": getattr(state, "turn", 0),
        "seed": rules.RNG.get_state().get("seed", 0),
    }
    data = {
        "save_version": SAVE_VERSION,
        "mode": state.mode.name,
        "players": [p.to_dict() for p in state.players],
        "state": state.to_dict(),
        "rng": rules.RNG.get_state(),
        "meta": meta,
    }
    # compute size & checksum iteratively until stable
    while True:
        text = json.dumps(data)
        payload = text.encode("utf-8")
        size = len(payload)
        sha = hashlib.sha256(payload).hexdigest()
        if meta.get("size") == size and meta.get("sha256") == sha:
            break
        meta["size"] = size
        meta["sha256"] = sha
    if steam.is_available():
        cloud_payload = payload
        if path.suffix == ".gz":
            cloud_payload = gzip.compress(payload)
        key = _cloud_key(path, True)
        if key and steam.cloud_write(key, cloud_payload):
            return
    backup = _shadow_backup(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        if path.suffix == ".gz":
            with gzip.open(tmp, "wb") as fh:
                fh.write(payload)
        else:
            with tmp.open("wb") as fh:
                fh.write(payload)
        tmp.replace(path)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def load_game(path: str | Path) -> board.GameState:
    path = Path(path)
    data = None
    if steam.is_available():
        key = _cloud_key(path, False)
        if key:
            raw = steam.cloud_read(key)
            if raw is not None:
                if path.suffix == ".gz":
                    data = json.loads(gzip.decompress(raw).decode("utf-8"))
                else:
                    data = json.loads(raw.decode("utf-8"))
    if data is None:
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                data = json.load(fh)
        else:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
    version = data.get("save_version", 1)
    if version > SAVE_VERSION:
        raise ValueError("Unsupported save version")
    if version < SAVE_VERSION:
        data = apply_migrations(data, SAVE_VERSION)
    mode = rules.GameMode[data.get("mode", "SOLO")]
    players = [entities.Player.from_dict(p) for p in data.get("players", [])]
    rng_state = data.get("rng")
    if rng_state:
        rules.RNG.set_state(rng_state)
    return board.GameState.from_dict(data["state"], mode=mode, players=players)


def snapshot(state: board.GameState) -> Dict[str, Any]:
    """Return a serialisable snapshot of ``state`` used for replays."""

    return {
        "mode": state.mode.name,
        "players": [p.to_dict() for p in state.players],
        "state": state.to_dict(),
        "rng": rules.RNG.get_state(),
    }


def restore(data: Dict[str, Any]) -> board.GameState:
    """Reconstruct a :class:`board.GameState` from ``data``."""

    mode = rules.GameMode[data.get("mode", "SOLO")]
    players = [entities.Player.from_dict(p) for p in data.get("players", [])]
    rng_state = data.get("rng")
    if rng_state:
        rules.RNG.set_state(rng_state)
    return board.GameState.from_dict(data["state"], mode=mode, players=players)


def export_map(b: board.Board, name: str) -> Path:
    """Export ``b`` to ``mods/maps`` using ``name`` as filename."""
    MOD_MAPS_DIR.mkdir(parents=True, exist_ok=True)
    path = MOD_MAPS_DIR / f"{name}.json"
    board.export_map(b, path)
    return path


def import_map(name: str) -> board.Board:
    """Load a map previously exported with :func:`export_map`."""
    path = MOD_MAPS_DIR / f"{name}.json"
    return board.import_map(path)


# restart helpers ---------------------------------------------------------


def restart_allowed(cfg: Dict[str, Any] | None = None) -> bool:
    """Check configuration flag controlling restart availability."""

    if cfg is None:
        cfg = config.load_config()
    return bool(cfg.get("allow_restart", True))


def restart_state(state: board.GameState, seed: int, cfg: Dict[str, Any] | None = None) -> board.GameState:
    """Return a fresh game state using ``seed`` if restarts are allowed."""

    if not restart_allowed(cfg):
        return state
    rules.set_seed(seed)
    return board.create_game(players=len(state.players), mode=state.mode)
