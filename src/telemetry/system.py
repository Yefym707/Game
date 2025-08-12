from __future__ import annotations

import locale
import platform
from typing import Dict


def system_info() -> Dict[str, str]:
    """Return basic, non-PII system information."""

    loc = locale.getdefaultlocale()[0] or ""
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "python": platform.python_version(),
        "locale": loc,
    }
