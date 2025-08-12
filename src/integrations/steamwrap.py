from __future__ import annotations

"""ctypes based Steamworks wrapper with graceful fallback."""

import ctypes
import logging
import os
from pathlib import Path
from typing import Dict, Optional

log = logging.getLogger(__name__)


class Steam:
    """Minimal wrapper around ``steam_api`` via :mod:`ctypes`.

    When the environment variable ``STEAM_SDK_PATH`` points to a Steamworks SDK
    this class attempts to load ``steam_api`` and call ``SteamAPI_Init``.  Any
    failure results in :attr:`available` being ``False`` and all public methods
    becoming no-ops.
    """

    def __init__(self) -> None:
        self.available = False
        self._sdk: Optional[ctypes.CDLL] = None
        self._achievements: set[str] = set()
        self._progress: Dict[str, float] = {}
        self._rich: Dict[str, str] = {}
        sdk_path = os.environ.get("STEAM_SDK_PATH")
        try:
            if sdk_path:
                lib = self._find_library(Path(sdk_path))
                if lib:
                    self._sdk = ctypes.CDLL(str(lib))
                    init = getattr(self._sdk, "SteamAPI_Init", None)
                    if init:
                        init.restype = ctypes.c_bool
                        self.available = bool(init())
                        if not self.available:
                            log.warning("SteamAPI_Init failed")
                    else:
                        log.warning("SteamAPI_Init symbol missing")
                else:
                    log.warning("steam_api library not found")
            else:
                log.warning("STEAM_SDK_PATH not set")
        except Exception as exc:  # pragma: no cover - initialisation errors
            log.warning("Steam init error: %s", exc)
            self.available = False

    # ------------------------------------------------------------------ utils
    def _find_library(self, base: Path) -> Optional[Path]:
        names = ["libsteam_api.so", "steam_api.dll", "libsteam_api.dylib"]
        subdirs = [
            "redistributable_bin",
            "redistributable_bin/linux64",
            "redistributable_bin/linux32",
            "redistributable_bin/win64",
            "redistributable_bin/win32",
        ]
        for sub in subdirs:
            for name in names:
                cand = base / sub / name
                if cand.exists():
                    return cand
        return None

    # ----------------------------------------------------------------- queries
    def is_available(self) -> bool:
        return self.available

    def is_overlay_active(self) -> bool:
        if not self.available or not self._sdk:
            return False
        func = getattr(self._sdk, "SteamAPI_ISteamUtils_IsOverlayEnabled", None)
        if func:
            func.restype = ctypes.c_bool
            try:
                return bool(func(None))
            except Exception:
                pass
        return False

    # ------------------------------------------------------------- achievements
    def set_achievement(self, aid: str) -> None:
        if self.available and self._sdk:
            func = getattr(
                self._sdk, "SteamAPI_ISteamUserStats_SetAchievement", None
            )
            if func:
                try:
                    func(None, aid.encode("utf-8"))
                except Exception:
                    pass
        self._achievements.add(aid)

    def is_achievement_unlocked(self, aid: str) -> bool:
        return aid in self._achievements

    def indicate_progress(self, aid: str, value: float) -> None:
        if self.available and self._sdk:
            func = getattr(
                self._sdk, "SteamAPI_ISteamUserStats_IndicateAchievementProgress", None
            )
            if func:
                try:
                    func(None, aid.encode("utf-8"), int(value * 100), 100)
                except Exception:
                    pass
        self._progress[aid] = value

    def store_stats(self) -> None:
        if self.available and self._sdk:
            func = getattr(self._sdk, "SteamAPI_ISteamUserStats_StoreStats", None)
            if func:
                try:
                    func(None)
                except Exception:
                    pass

    # ------------------------------------------------------------ rich presence
    def set_rich_presence(self, key: str, val: str) -> None:
        if self.available and self._sdk:
            func = getattr(
                self._sdk, "SteamAPI_ISteamFriends_SetRichPresence", None
            )
            if func:
                try:
                    func(None, key.encode("utf-8"), str(val).encode("utf-8"))
                except Exception:
                    pass
        self._rich[key] = val

    # ------------------------------------------------------------------ cloud
    def cloud_write(self, key: str, data: bytes) -> bool:
        if self.available and self._sdk:
            func = getattr(
                self._sdk, "SteamAPI_ISteamRemoteStorage_FileWrite", None
            )
            if func:
                try:
                    res = func(None, key.encode("utf-8"), data, len(data))
                    return bool(res)
                except Exception:
                    return False
        return False

    def cloud_read(self, key: str) -> Optional[bytes]:
        if self.available and self._sdk:
            fsize = getattr(
                self._sdk, "SteamAPI_ISteamRemoteStorage_GetFileSize", None
            )
            fread = getattr(
                self._sdk, "SteamAPI_ISteamRemoteStorage_FileRead", None
            )
            if fsize and fread:
                try:
                    size = fsize(None, key.encode("utf-8"))
                    if size > 0:
                        buf = ctypes.create_string_buffer(size)
                        read = fread(None, key.encode("utf-8"), buf, size)
                        if read == size:
                            return buf.raw
                except Exception:
                    pass
        return None


steam = Steam()

__all__ = ["steam", "Steam"]
