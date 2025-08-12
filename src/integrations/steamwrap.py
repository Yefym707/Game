from __future__ import annotations

"""Thin wrapper around the Steamworks API.

The module tries to load the real Steamworks SDK when the environment variable
``STEAM_SDK_PATH`` is set.  If anything fails we fall back to a lightweight
stub so the game keeps functioning outside of Steam.
"""

import os
from typing import Optional

STEAMWORKS = None
try:  # pragma: no cover - import is optional
    sdk_path = os.environ.get("STEAM_SDK_PATH")
    if sdk_path:
        import sys

        sys.path.append(sdk_path)
        from steamworks import STEAMWORKS  # type: ignore
except Exception:  # pragma: no cover - fall back to stub
    STEAMWORKS = None


class _StubSteam:
    """Fallback implementation used when Steam is unavailable."""

    cloud_saves = False

    def __init__(self) -> None:
        self._achievements: set[str] = set()

    def set_achievement(self, ach_id: str) -> None:  # pragma: no cover - trivial
        self._achievements.add(ach_id)

    def is_achievement_unlocked(self, ach_id: str) -> bool:  # pragma: no cover - trivial
        return ach_id in self._achievements

    def store_stats(self) -> None:  # pragma: no cover - trivial
        pass

    def save(self, name: str, data: bytes) -> bool:  # pragma: no cover - stub
        return False

    def load(self, name: str) -> Optional[bytes]:  # pragma: no cover - stub
        return None


if STEAMWORKS:
    class _Steam(_StubSteam):  # pragma: no cover - requires SDK
        cloud_saves = True

        def __init__(self) -> None:
            super().__init__()
            self._sw = STEAMWORKS()
            self._sw.initialize()

        def set_achievement(self, ach_id: str) -> None:
            self._sw.UserStats.SetAchievement(ach_id)

        def is_achievement_unlocked(self, ach_id: str) -> bool:
            ok, achieved = self._sw.UserStats.GetAchievement(ach_id)
            return bool(achieved)

        def store_stats(self) -> None:
            self._sw.UserStats.StoreStats()

        def save(self, name: str, data: bytes) -> bool:
            self._sw.RemoteStorage.FileWrite(name, data)
            return True

        def load(self, name: str) -> Optional[bytes]:
            if self._sw.RemoteStorage.FileExists(name):
                return self._sw.RemoteStorage.FileRead(name)
            return None

    steam = _Steam()
else:
    steam = _StubSteam()
