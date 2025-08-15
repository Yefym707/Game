import random
import re
from typing import Tuple

DICE_RE = re.compile(r'^\s*(\d*)d(\d+)\s*([+-]\s*\d+)?\s*$')


def roll(dice_notation: str) -> Tuple[int, str]:
    """Roll dice using NdM+K notation (e.g. "1d6", "2d8+1", "d6-1").
    Returns a tuple of ``(value, detail_string)``.
    """
    m = DICE_RE.match(dice_notation)
    if not m:
        # attempt to parse a plain number
        try:
            v = int(dice_notation.strip())
            return v, f"const {v}"
        except ValueError as exc:
            raise ValueError(f"Invalid dice notation: '{dice_notation}'") from exc
    n_str, sides_str, mod_str = m.groups()
    n = int(n_str) if n_str else 1
    sides = int(sides_str)
    mod = 0
    if mod_str:
        mod = int(mod_str.replace(" ", ""))
    rolls = [random.randint(1, sides) for _ in range(n)]
    total = sum(rolls) + mod
    detail = f"{n}d{sides}={rolls}"
    if mod:
        detail += f"{mod:+d}"
    detail += f" -> {total}"
    return total, detail
