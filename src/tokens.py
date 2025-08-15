import json
from typing import Dict, List, Tuple, Any

Position = Tuple[int, int]

class TokenManager:
    """Store tokens/markers on tiles: mapping "x,y" -> list of token dicts.
    Each token: {"token": str, "duration": Optional[int]}
    New features:
      - ``get_symbols_at(pos)``: short string of symbols for map rendering
      - ``apply_enter`` handles new token types ``spike`` and ``dense_smoke``
    """
    SYMBOLS = {
        "smoke": "~",
        "dense_smoke": "≈",
        "trap_marker": "^",
        "spike": "*",
        "healing_aura": "+",
        "flag": "F",
        "bear_trap": "T",
        "trap": "!",
    }

    def __init__(self, tokens: Dict[str, List[Dict[str, Any]]] = None):
        self._map: Dict[str, List[Dict[str, Any]]] = {}
        if tokens:
            self._map = {k: list(v) for k, v in tokens.items()}

    def _key(self, pos: Position) -> str:
        x, y = pos
        return f"{x},{y}"

    def add_token(self, pos: Position, token: str, duration: int = None):
        k = self._key(pos)
        self._map.setdefault(k, [])
        self._map[k].append({"token": token, "duration": int(duration) if duration is not None else None})

    def remove_token(self, pos: Position, token: str) -> bool:
        k = self._key(pos)
        if k in self._map:
            for entry in list(self._map[k]):
                if entry.get("token") == token:
                    self._map[k].remove(entry)
                    if not self._map[k]:
                        del self._map[k]
                    return True
        return False

    def get_tokens(self, pos: Position) -> List[Dict[str, Any]]:
        return [dict(e) for e in self._map.get(self._key(pos), [])]

    def list_all(self) -> Dict[Position, List[Dict[str, Any]]]:
        out: Dict[Position, List[Dict[str, Any]]] = {}
        for k, lst in self._map.items():
            x_str, y_str = k.split(",")
            out[(int(x_str), int(y_str))] = [dict(e) for e in lst]
        return out

    def tick(self) -> List[Tuple[Position, Dict[str, Any]]]:
        """Decrease duration for tokens with numeric duration and remove expired ones.
        Returns a list of removed tokens ``[(pos, token_entry), ...]``.
        """
        removed = []
        to_delete = []
        for k, lst in list(self._map.items()):
            new_lst = []
            for entry in lst:
                dur = entry.get("duration")
                if dur is None:
                    new_lst.append(entry)
                    continue
                dur -= 1
                if dur > 0:
                    new_lst.append({"token": entry["token"], "duration": dur})
                else:
                    x_str, y_str = k.split(",")
                    pos = (int(x_str), int(y_str))
                    removed.append((pos, {"token": entry["token"], "duration": 0}))
            if new_lst:
                self._map[k] = new_lst
            else:
                to_delete.append(k)
        for k in to_delete:
            if k in self._map:
                del self._map[k]
        return removed

    def to_dict(self) -> Dict[str, Any]:
        return {"tokens": dict(self._map)}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> 'TokenManager':
        tm = TokenManager(tokens=d.get("tokens", {}))
        return tm

    def save(self, filename: str = "tokens.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @staticmethod
    def load(filename: str = "tokens.json") -> 'TokenManager':
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            return TokenManager.from_dict(data)
        except Exception as exc:  # pragma: no cover - file may not exist
            import logging

            logging.getLogger(__name__).debug(
                "Failed loading tokens from %s: %s", filename, exc
            )
            return TokenManager()

    # --------------------------
    # Token game logic
    # --------------------------

    def apply_enter(self, pos: Position, entity_type: str, campaign) -> List[Dict[str, Any]]:
        """Called when an entity enters tile ``pos``.
        ``entity_type``: ``'player'`` or ``'enemy'``.
        Returns a list of triggers:
          ``{'token':str, 'type':'damage'|'heal'|'info', 'amount':int, 'consume':bool}``
        Additional rules:
          - ``trap_marker``  : deals 2 damage and is consumed
          - ``spike``        : deals 2 damage and is consumed (new type)
          - ``bear_trap``    : deals 3 damage and is consumed
          - ``dense_smoke``  : no damage but makes hits harder (handled elsewhere)
          - ``healing_aura`` : no trigger on enter, heals during cleanup phase
        """
        triggers = []
        for entry in self.get_tokens(pos):
            t = entry.get("token")
            if t == "trap_marker":
                triggers.append({"token": t, "type": "damage", "amount": 2, "consume": True})
            elif t == "spike":
                triggers.append({"token": t, "type": "damage", "amount": 2, "consume": True})
            elif t == "bear_trap":
                triggers.append({"token": t, "type": "damage", "amount": 3, "consume": True})
            elif t == "flag":
                triggers.append({"token": t, "type": "info", "amount": 0, "consume": False})
            elif t == "smoke":
                triggers.append({"token": t, "type": "info", "amount": 0, "consume": False})
            elif t == "dense_smoke":
                triggers.append({"token": t, "type": "info", "amount": 0, "consume": False})
            else:
                triggers.append({"token": t, "type": "info", "amount": 0, "consume": False})
        # remove consumed tokens
        for trig in list(triggers):
            if trig.get("consume"):
                self.remove_token(pos, trig["token"])
        return triggers

    def get_hit_threshold_modifier(self, attacker_pos: Position, defender_pos: Position) -> int:
        """Return modifier for hit threshold added to the base value.
        Smoke on attacker/defender -> +1, dense_smoke -> +2.
        """
        mod = 0
        for pos in (attacker_pos, defender_pos):
            for entry in self.get_tokens(pos):
                if entry.get("token") == "smoke":
                    mod += 1
                if entry.get("token") == "dense_smoke":
                    mod += 2
        return mod

    def get_symbols_at(self, pos: Position, max_symbols: int = 2) -> str:
        """Return a short string representing tokens on a tile.
        Limited to ``max_symbols`` characters for compactness.
        """
        syms: List[str] = []
        for entry in self.get_tokens(pos):
            t = entry.get("token")
            sym = self.SYMBOLS.get(t, "?")
            if sym not in syms:
                syms.append(sym)
            if len(syms) >= max_symbols:
                break
        return "".join(syms)