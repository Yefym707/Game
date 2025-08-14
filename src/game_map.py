import json
from typing import List, Tuple, Optional, Dict, Any
import random

class Zone:
    def __init__(self, pos: Tuple[int, int], zone_type: str, explored: bool = False, quest: Optional[dict] = None, meta: Optional[dict] = None):
        self.pos = pos
        self.zone_type = zone_type  # 'resource', 'trap', 'event', 'quest', 'merchant', 'camp'
        self.explored = explored
        self.quest = quest
        self.meta = meta or {}  # extra data: for merchant — inventory, for camp — camp level

    def to_dict(self):
        return {
            "pos": self.pos,
            "zone_type": self.zone_type,
            "explored": self.explored,
            "quest": self.quest,
            "meta": self.meta
        }

    @staticmethod
    def from_dict(d):
        return Zone(tuple(d["pos"]), d["zone_type"], d.get("explored", False), d.get("quest"), d.get("meta"))

class GameMap:
    def __init__(self, width: int, height: int, player_pos: Tuple[int, int] = (0,0),
                 visible: List[List[bool]] = None, zones: List[Zone] = None):
        self.width = width
        self.height = height
        self.player_pos = player_pos
        if visible is None:
            self.visible = [[False for _ in range(width)] for _ in range(height)]
        else:
            self.visible = visible
        self.zones = zones or self.generate_zones()
        self.reveal(self.player_pos)

    def generate_zones(self) -> List[Zone]:
        zones = []
        zone_types = (["resource"] * 3) + (["trap"] * 2) + (["event"]) + (["quest"]) + (["merchant"]) + (["camp"])
        positions = set([self.player_pos])
        for ztype in zone_types:
            while True:
                x, y = random.randint(0, self.width-1), random.randint(0, self.height-1)
                if (x, y) not in positions:
                    meta = {}
                    if ztype == "merchant":
                        goods = {
                            "food": {"sell": 5, "buy": 2, "min_rep": 0},
                            "water": {"sell": 4, "buy": 2, "min_rep": 0},
                            "bandages": {"sell": 8, "buy": 4, "min_rep": 0},
                            "ancient_artifact": {"sell": 50, "buy": 20, "min_rep": 3}
                        }
                        meta = {"goods": goods, "name": f"Trader_{x}_{y}"}
                    if ztype == "camp":
                        meta = {"level": 1}
                    zones.append(Zone((x, y), ztype, meta=meta))
                    positions.add((x, y))
                    break
        return zones

    def move_player(self, dx: int, dy: int):
        x, y = self.player_pos
        new_x = max(0, min(self.width-1, x+dx))
        new_y = max(0, min(self.height-1, y+dy))
        self.player_pos = (new_x, new_y)
        self.reveal(self.player_pos)

    def reveal(self, pos: Tuple[int, int]):
        self.reveal_radius(pos, radius=1)

    def reveal_radius(self, pos: Tuple[int, int], radius: int = 1):
        x, y = pos
        for dx in range(-radius, radius+1):
            for dy in range(-radius, radius+1):
                nx, ny = x+dx, y+dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    self.visible[ny][nx] = True

    def get_zone_at(self, pos: Tuple[int, int]) -> Optional[Zone]:
        for z in self.zones:
            if z.pos == pos:
                return z
        return None

    def to_dict(self):
        return {
            "width": self.width,
            "height": self.height,
            "player_pos": self.player_pos,
            "visible": self.visible,
            "zones": [z.to_dict() for z in self.zones]
        }

    @staticmethod
    def from_dict(data):
        zones = [Zone.from_dict(z) for z in data.get("zones", [])]
        return GameMap(
            width=data["width"],
            height=data["height"],
            player_pos=tuple(data["player_pos"]),
            visible=data["visible"],
            zones=zones
        )

    def __str__(self, enemies: Optional[list]=None, token_manager: Any = None):
        """Render a text representation of the map.

        Accepts a list of enemies and optionally a ``token_manager`` to show
        token symbols. Rendering rules (for visible tiles):
          - P  — player
          - E  — enemy
          - <token_symbol> — token symbol (if no character on the tile)
          - zone-dependent symbol ($ ^ ? Q M C)
          - .  — empty visible cell
          - #  — hidden cell
        """
        enemies = enemies or []
        enemy_positions = set(e.pos for e in enemies)
        zone_positions = {tuple(z.pos): z for z in self.zones}
        lines = []
        for y in range(self.height):
            line = ""
            for x in range(self.width):
                pos = (x, y)
                if not self.visible[y][x]:
                    line += "# "
                    continue
                # player
                if pos == self.player_pos:
                    # if there is a token, show token symbol before P (e.g. "~P"), but keep two chars
                    token_sym = ""
                    if token_manager:
                        token_sym = token_manager.get_symbols_at(pos, max_symbols=1)
                    if token_sym:
                        cell = (token_sym + "P")[:2]
                    else:
                        cell = "P "
                    line += cell + " " if len(cell) == 1 else cell + " "
                    # cell already includes a trailing char, adjust spacing later
                    line = line[:-1]  # correct double spacing
                elif pos in enemy_positions:
                    # enemy present
                    token_sym = ""
                    if token_manager:
                        token_sym = token_manager.get_symbols_at(pos, max_symbols=1)
                    if token_sym:
                        cell = (token_sym + "E")[:2]
                    else:
                        cell = "E "
                    line += cell + " "
                    line = line[:-1]
                elif token_manager:
                    t = token_manager.get_symbols_at(pos, max_symbols=1)
                    if t:
                        # show token symbol
                        cell = (t + ".")[:2]
                        line += cell + " "
                        line = line[:-1]
                    elif pos in zone_positions:
                        z = zone_positions[pos]
                        if z.zone_type == "resource" and not z.explored:
                            line += "$ "
                        elif z.zone_type == "trap" and not z.explored:
                            line += "^ "
                        elif z.zone_type == "event" and not z.explored:
                            line += "? "
                        elif z.zone_type == "quest" and not z.explored:
                            line += "Q "
                        elif z.zone_type == "merchant" and not z.explored:
                            line += "M "
                        elif z.zone_type == "camp" and not z.explored:
                            line += "C "
                        else:
                            line += ". "
                    else:
                        line += ". "
                else:
                    if pos in zone_positions:
                        z = zone_positions[pos]
                        if z.zone_type == "resource" and not z.explored:
                            line += "$ "
                        elif z.zone_type == "trap" and not z.explored:
                            line += "^ "
                        elif z.zone_type == "event" and not z.explored:
                            line += "? "
                        elif z.zone_type == "quest" and not z.explored:
                            line += "Q "
                        elif z.zone_type == "merchant" and not z.explored:
                            line += "M "
                        elif z.zone_type == "camp" and not z.explored:
                            line += "C "
                        else:
                            line += ". "
                    else:
                        line += ". "
            lines.append(line.strip())
        return "\n".join(lines)