from __future__ import annotations

"""Small helpers for locating resources and user data directories.

The functions centralise common path lookups and keep PyInstaller
bundles working by respecting ``sys._MEIPASS``.
"""

from pathlib import Path
import os
import sys


def resource_path(rel: str) -> str:
    """Return an absolute path for a bundled resource.

    ``rel`` is interpreted relative to the project root.  When running from a
    PyInstaller binary ``sys._MEIPASS`` points to the temporary extraction
    directory which must be used as the base path.  The function always returns
    a string so it can be fed directly to APIs expecting filesystem paths.
    """

    base = getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2])
    return str(Path(base) / rel)


def user_data_dir() -> Path:
    """Return the directory used for persistent user data."""

    root = Path(os.environ.get("USERPROFILE", Path.home())) / ".oko_zombie"
    root.mkdir(parents=True, exist_ok=True)
    return root


def logs_dir() -> Path:
    """Return the directory used for application logs creating it if needed."""

    path = user_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


__all__ = ["resource_path", "user_data_dir", "logs_dir"]
