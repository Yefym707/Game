import random
import re
from typing import Tuple

DICE_RE = re.compile(r'^\s*(\d*)d(\d+)\s*([+-]\s*\d+)?\s*$')

def roll(dice_notation: str) -> Tuple[int, str]:
    """
    Бросок кубиков по нотации NdM+K (например: "1d6", "2d8+1", "d6-1").
    Возвращает (value, detail_string).
    """
    m = DICE_RE.match(dice_notation)
    if not m:
        # попытка разобрать простое число
        try:
            v = int(dice_notation.strip())
            return v, f"const {v}"
        except Exception:
            raise ValueError(f"Неправильная нотация кубиков: '{dice_notation}'")
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