from __future__ import annotations

from collections import deque
from typing import Dict, List

_MAX = 50
_breadcrumbs: deque[Dict[str, str]] = deque(maxlen=_MAX)


def add(msg: str) -> None:
    _breadcrumbs.append({"msg": msg})


def get() -> List[Dict[str, str]]:
    return list(_breadcrumbs)
