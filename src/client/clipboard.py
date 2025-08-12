from __future__ import annotations

"""Simple cross-platform clipboard helper."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


try:  # pragma: no cover - optional
    import pygame
    pygame.scrap.init()
except Exception:  # pragma: no cover
    pygame = None  # type: ignore

try:  # pragma: no cover - optional
    import tkinter
    _tk = tkinter.Tk()
    _tk.withdraw()
except Exception:  # pragma: no cover
    _tk = None

FALLBACK_FILE = Path.home() / ".oko_zombie" / "clipboard.txt"


def copy(text: str) -> bool:
    """Copy ``text`` to the clipboard returning ``True`` on success."""

    if pygame and pygame.scrap.get_init():  # pragma: no cover - UI path
        pygame.scrap.put(pygame.SCRAP_TEXT, text.encode("utf-8"))
        return True
    if _tk is not None:  # pragma: no cover - UI path
        _tk.clipboard_clear()
        _tk.clipboard_append(text)
        return True
    cmd: list[str] | None = None
    if os.name == "nt":
        cmd = ["clip"]
    elif sys.platform == "darwin":
        cmd = ["pbcopy"]
    else:
        cmd = ["xclip", "-selection", "clipboard"]
    try:
        if cmd:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            proc.communicate(text.encode("utf-8"))
            if proc.returncode == 0:
                return True
    except Exception:
        pass
    FALLBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    FALLBACK_FILE.write_text(text, encoding="utf-8")
    return False


def paste() -> Optional[str]:
    """Return text from clipboard or ``None``."""

    if pygame and pygame.scrap.get_init():  # pragma: no cover - UI path
        data = pygame.scrap.get(pygame.SCRAP_TEXT)
        if data:
            return data.decode("utf-8")
    if _tk is not None:  # pragma: no cover - UI path
        try:
            return _tk.clipboard_get()
        except Exception:
            return None
    try:
        if os.name == "nt":
            out = subprocess.check_output(["powershell", "-command", "Get-Clipboard"], text=True)
            return out.strip()
        if sys.platform == "darwin":
            out = subprocess.check_output(["pbpaste"], text=True)
            return out.strip()
        out = subprocess.check_output(["xclip", "-selection", "clipboard", "-o"], text=True)
        return out.strip()
    except Exception:
        pass
    if FALLBACK_FILE.exists():
        return FALLBACK_FILE.read_text(encoding="utf-8")
    return None


__all__ = ["copy", "paste"]
