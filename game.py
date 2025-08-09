"""Turn-based survival board game prototype.

This module implements a simple console survival game where one or more
players scour a zombie infested grid for an antidote then race back to
safety.

Features
--------
* 10x10 board with up to four players, zombies and supply tokens.
* Each player has two actions per turn: move, attack, scavenge or pass.
* Melee combat with a chance to hit. Failed attacks cost health.
* Random scavenge system for finding additional supplies and food.
* Zombies pursue the player and new ones may spawn each round.
* Player wins by finding the antidote and returning to the starting tile.
  Victory grants +1 max health for the next run, saved to disk.
* Hunger mechanic – eat supplies to avoid starving each round.

The code is intentionally compact and uses only the Python standard
library so it can run in any environment with Python 3.12 or newer.
"""

from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple


BOARD_SIZE = 10
ACTIONS_PER_TURN = 2
STARTING_HEALTH = 10
STARTING_ZOMBIES = 5
STARTING_SUPPLIES = 5
INVENTORY_LIMIT = 8
ATTACK_HIT_CHANCE = 0.7
SCAVENGE_FIND_CHANCE = 0.5
ZOMBIE_SPAWN_CHANCE = 0.3
MEDKIT_FIND_CHANCE = 0.2
MEDKIT_HEAL = 3
WEAPON_FIND_CHANCE = 0.1
WEAPON_HIT_CHANCE = 0.9
TURN_LIMIT = 20
REVEAL_RADIUS = 1
REVEAL_SUPPLY_CHANCE = 0.05
REVEAL_ZOMBIE_CHANCE = 0.05
STARTING_HUNGER = 10
HUNGER_DECAY = 1
HUNGER_EAT_AMOUNT = 4
HUNGER_STARVE_DAMAGE = 1

CAMPAIGN_FILE = "campaign_save.json"
SAVE_FILE = "savegame.json"
ANTIDOTE_SYMBOL = "A"
KEYS_SYMBOL = "K"
FUEL_SYMBOL = "F"
RADIO_PART_SYMBOL = "P"
RADIO_TOWER_SYMBOL = "T"
RADIO_PARTS_REQUIRED = 3
EVACUATION_TURNS = 5
DOUBLE_MOVE_REWARD = 5
WEAPON_NOISE_ZOMBIE_CHANCE = 0.3
VEHICLE_NOISE_ZOMBIE_CHANCE = 0.5

# Special tile settings
PHARMACY_SYMBOL = "M"
ARMORY_SYMBOL = "W"
PHARMACY_COUNT = 3
ARMORY_COUNT = 2
PHARMACY_MEDKIT_CHANCE = 0.8
ARMORY_WEAPON_CHANCE = 0.6
ARMORY_SUPPLY_CHANCE = 0.4

# Barricade settings
BARRICADE_SYMBOL = "B"
BARRICADE_SUPPLY_COST = 2

# Simple achievement definitions evaluated against the persistent campaign
# data. Additional achievements can be added here without touching the game
# logic.
ACHIEVEMENT_DEFS = {
    "zombie_hunter": {
        "desc": "Slay 10 zombies in total",
        "check": lambda data: data.get("zombies_killed", 0) >= 10,
    },
    "master_survivor": {
        "desc": "Complete all four scenarios",
        "check": lambda data: all(
            scen in data.get("completed_scenarios", []) for scen in (1, 2, 3, 4)
        ),
    },
}


def load_campaign() -> dict:
    """Load persistent campaign data from disk."""
    data = {
        "hp_bonus": 0,
        "double_move_tokens": 0,
        "signal_device": 0,
        "zombies_killed": 0,
        "completed_scenarios": [],
        "achievements": [],
    }
    if os.path.exists(CAMPAIGN_FILE):
        with open(CAMPAIGN_FILE, "r", encoding="utf-8") as fh:
            try:
                loaded = json.load(fh)
                if isinstance(loaded, dict):
                    data.update(loaded)
            except json.JSONDecodeError:
                pass
    return data


def save_campaign(data: dict) -> None:
    """Persist campaign data to disk."""
    with open(CAMPAIGN_FILE, "w", encoding="utf-8") as fh:
        json.dump(data, fh)


DIFFICULTY_SETTINGS = {
    "easy": {
        "starting_health": STARTING_HEALTH + 2,
        "starting_zombies": max(1, STARTING_ZOMBIES - 2),
        "zombie_spawn_chance": ZOMBIE_SPAWN_CHANCE * 0.7,
        "turn_limit": TURN_LIMIT + 5,
    },
    "normal": {
        "starting_health": STARTING_HEALTH,
        "starting_zombies": STARTING_ZOMBIES,
        "zombie_spawn_chance": ZOMBIE_SPAWN_CHANCE,
        "turn_limit": TURN_LIMIT,
    },
    "hard": {
        "starting_health": max(1, STARTING_HEALTH - 2),
        "starting_zombies": STARTING_ZOMBIES + 2,
        "zombie_spawn_chance": ZOMBIE_SPAWN_CHANCE * 1.3,
        "turn_limit": max(1, TURN_LIMIT - 5),
    },
}


@dataclass
class Entity:
    x: int
    y: int
    symbol: str


class Player(Entity):
    """Player entity with health and collected supplies."""

    def __init__(
        self,
        x: int,
        y: int,
        starting_health: int,
        symbol: str = "@",
        is_ai: bool = False,
    ) -> None:
        super().__init__(x, y, symbol)
        self.is_ai: bool = is_ai
        self.max_health: int = starting_health
        self.health: int = starting_health
        self.max_hunger: int = STARTING_HUNGER
        self.hunger: int = STARTING_HUNGER
        self.supplies: int = 0
        self.medkits: int = 0
        self.has_antidote: bool = False
        self.has_keys: bool = False
        self.has_fuel: bool = False
        self.has_weapon: bool = False

    @property
    def inventory_size(self) -> int:
        """Total number of items currently carried."""
        return self.supplies + self.medkits


class Zombie(Entity):
    """Simple zombie that pursues the player."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y, "Z")


class Game:
    """Main game controller handling turns and board state."""

    board_size: int = BOARD_SIZE

    def __init__(
        self,
        difficulty: str = "normal",
        scenario: int = 1,
        num_players: int = 1,
        num_ai: int = 0,
    ) -> None:
        settings = DIFFICULTY_SETTINGS.get(difficulty.lower())
        if settings is None:
            raise ValueError("Unknown difficulty")
        self.difficulty = difficulty.lower()
        self.scenario = scenario
        self.campaign = load_campaign()
        self.double_move_tokens = self.campaign.get("double_move_tokens", 0)
        self.has_signal_device = bool(self.campaign.get("signal_device"))
        self.zombie_spawn_chance = settings["zombie_spawn_chance"]
        self.turn_limit = settings["turn_limit"]
        starting_health = settings["starting_health"] + self.campaign.get("hp_bonus", 0)
        center = self.board_size // 2
        offsets = [(0, 0), (0, 1), (1, 0), (-1, 0), (0, -1)]
        self.players: List[Player] = []
        total_players = max(1, num_players)
        num_ai = max(0, min(num_ai, total_players - 1))
        for i in range(total_players):
            dx, dy = offsets[i % len(offsets)]
            is_ai = i >= total_players - num_ai
            self.players.append(
                Player(center + dx, center + dy, starting_health, str(i + 1), is_ai)
            )
        self.player: Player = self.players[0]
        self.start_pos = (center, center)
        self.antidote_pos: Optional[Tuple[int, int]] = None
        self.keys_pos: Optional[Tuple[int, int]] = None
        self.fuel_pos: Optional[Tuple[int, int]] = None
        self.radio_positions: Set[Tuple[int, int]] = set()
        self.radio_tower_pos: Optional[Tuple[int, int]] = None
        self.radio_parts_collected = 0
        self.called_rescue = False
        self.rescue_timer: Optional[int] = None
        self.zombies: List[Zombie] = []
        self.supplies_positions: Set[Tuple[int, int]] = set()
        self.pharmacy_positions: Set[Tuple[int, int]] = set()
        self.armory_positions: Set[Tuple[int, int]] = set()
        self.barricade_positions: Set[Tuple[int, int]] = set()
        self.revealed: Set[Tuple[int, int]] = set()
        self.spawn_zombies(settings["starting_zombies"])
        self.spawn_pharmacies(PHARMACY_COUNT)
        self.spawn_armories(ARMORY_COUNT)
        self.spawn_supplies(STARTING_SUPPLIES)
        if self.scenario == 1:
            self.spawn_antidote()
        elif self.scenario == 2:
            self.spawn_keys()
            self.spawn_fuel()
        elif self.scenario == 3:
            self.spawn_radio_parts(RADIO_PARTS_REQUIRED)
        elif self.scenario == 4:
            if not self.has_signal_device:
                self.spawn_radio_tower()
        else:
            self.spawn_antidote()
        for p in self.players:
            self.reveal_area(p.x, p.y)
        self.turn: int = 0
        self.actions_per_turn: int = ACTIONS_PER_TURN
        self.keep_save = False
        self.zombies_killed: int = 0

    def is_player_at(self, x: int, y: int) -> bool:
        """Return True if any player occupies (x, y)."""
        return any(p.x == x and p.y == y for p in self.players)

    # ------------------------------------------------------------------
    # Persistence helpers
    def to_dict(self) -> dict:
        """Serialize current game state to a dictionary."""
        return {
            "difficulty": self.difficulty,
            "scenario": self.scenario,
            "start_pos": self.start_pos,
            "players": [
                {
                    "x": p.x,
                    "y": p.y,
                    "max_health": p.max_health,
                    "health": p.health,
                    "max_hunger": p.max_hunger,
                    "hunger": p.hunger,
                    "supplies": p.supplies,
                    "medkits": p.medkits,
                    "has_antidote": p.has_antidote,
                    "has_keys": p.has_keys,
                    "has_fuel": p.has_fuel,
                    "has_weapon": p.has_weapon,
                    "symbol": p.symbol,
                    "is_ai": getattr(p, "is_ai", False),
                }
                for p in self.players
            ],
            "zombies": [(z.x, z.y) for z in self.zombies],
            "supplies_positions": list(self.supplies_positions),
            "pharmacy_positions": list(self.pharmacy_positions),
            "armory_positions": list(self.armory_positions),
            "barricade_positions": list(self.barricade_positions),
            "revealed": list(self.revealed),
            "antidote_pos": self.antidote_pos,
            "keys_pos": self.keys_pos,
            "fuel_pos": self.fuel_pos,
            "radio_positions": list(self.radio_positions),
            "radio_tower_pos": self.radio_tower_pos,
            "radio_parts_collected": self.radio_parts_collected,
            "called_rescue": self.called_rescue,
            "rescue_timer": self.rescue_timer,
            "turn": self.turn,
            "current_player": self.players.index(self.player),
            "double_move_tokens": self.double_move_tokens,
            "has_signal_device": self.has_signal_device,
            "actions_per_turn": self.actions_per_turn,
            "zombies_killed": self.zombies_killed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Game":
        """Reconstruct a Game instance from serialized data."""
        game = cls(data["difficulty"], data["scenario"], len(data["players"]))
        game.start_pos = tuple(data["start_pos"])
        for p, pdata in zip(game.players, data["players"]):
            p.x = pdata["x"]
            p.y = pdata["y"]
            p.max_health = pdata["max_health"]
            p.health = pdata["health"]
            p.max_hunger = pdata["max_hunger"]
            p.hunger = pdata["hunger"]
            p.supplies = pdata["supplies"]
            p.medkits = pdata["medkits"]
            p.has_antidote = pdata["has_antidote"]
            p.has_keys = pdata["has_keys"]
            p.has_fuel = pdata["has_fuel"]
            p.has_weapon = pdata["has_weapon"]
            p.symbol = pdata.get("symbol", p.symbol)
            p.is_ai = pdata.get("is_ai", False)
        game.player = game.players[data.get("current_player", 0)]
        game.zombies = [Zombie(x, y) for x, y in data["zombies"]]
        game.supplies_positions = {tuple(pos) for pos in data["supplies_positions"]}
        game.pharmacy_positions = {
            tuple(pos) for pos in data.get("pharmacy_positions", [])
        }
        game.armory_positions = {
            tuple(pos) for pos in data.get("armory_positions", [])
        }
        game.barricade_positions = {
            tuple(pos) for pos in data.get("barricade_positions", [])
        }
        game.revealed = {tuple(pos) for pos in data["revealed"]}
        game.antidote_pos = tuple(data["antidote_pos"]) if data["antidote_pos"] else None
        game.keys_pos = tuple(data["keys_pos"]) if data["keys_pos"] else None
        game.fuel_pos = tuple(data["fuel_pos"]) if data["fuel_pos"] else None
        game.radio_positions = {tuple(pos) for pos in data["radio_positions"]}
        game.radio_tower_pos = (
            tuple(data["radio_tower_pos"]) if data["radio_tower_pos"] else None
        )
        game.radio_parts_collected = data["radio_parts_collected"]
        game.called_rescue = data["called_rescue"]
        game.rescue_timer = data["rescue_timer"]
        game.turn = data["turn"]
        game.double_move_tokens = data.get("double_move_tokens", 0)
        game.has_signal_device = data.get("has_signal_device", False)
        game.actions_per_turn = data.get("actions_per_turn", ACTIONS_PER_TURN)
        game.zombies_killed = data.get("zombies_killed", 0)
        return game

    def save_game(self, filename: str = SAVE_FILE) -> None:
        """Write current game state to disk."""
        with open(filename, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh)

    @classmethod
    def load_game(cls, filename: str = SAVE_FILE) -> "Game":
        """Load game state from disk."""
        with open(filename, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return cls.from_dict(data)

    def reveal_area(self, x: int, y: int) -> None:
        """Reveal tiles around (x, y) and trigger discovery events."""
        for dx in range(-REVEAL_RADIUS, REVEAL_RADIUS + 1):
            for dy in range(-REVEAL_RADIUS, REVEAL_RADIUS + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                    if (nx, ny) not in self.revealed:
                        self.revealed.add((nx, ny))
                        if (
                            (nx, ny) not in self.supplies_positions
                            and (nx, ny) != self.antidote_pos
                            and (nx, ny) != self.keys_pos
                            and (nx, ny) != self.fuel_pos
                            and (nx, ny) not in self.radio_positions
                            and (nx, ny) != self.radio_tower_pos
                            and (nx, ny) not in self.pharmacy_positions
                            and (nx, ny) not in self.armory_positions
                            and (nx, ny) not in self.barricade_positions
                            and all((z.x, z.y) != (nx, ny) for z in self.zombies)
                        ):
                            roll = random.random()
                            if roll < REVEAL_SUPPLY_CHANCE:
                                self.supplies_positions.add((nx, ny))
                                if (nx, ny) == (x, y):
                                    print("You uncover a supply cache!")
                            elif roll < REVEAL_SUPPLY_CHANCE + REVEAL_ZOMBIE_CHANCE:
                                self.zombies.append(Zombie(nx, ny))
                                if (nx, ny) == (x, y):
                                    print("A lurking zombie surprises you!")

    def reveal_random_tiles(self, count: int) -> None:
        """Reveal up to *count* random hidden tiles."""
        hidden = [
            (x, y)
            for x in range(self.board_size)
            for y in range(self.board_size)
            if (x, y) not in self.revealed
        ]
        random.shuffle(hidden)
        for x, y in hidden[:count]:
            self.reveal_area(x, y)

    # ------------------------------------------------------------------
    # Board setup helpers
    def spawn_zombies(self, count: int) -> None:
        for _ in range(count):
            while True:
                x, y = random.randrange(self.board_size), random.randrange(
                    self.board_size
                )
                if (
                    not self.is_player_at(x, y)
                    and (x, y) not in {(z.x, z.y) for z in self.zombies}
                    and (x, y) not in self.barricade_positions
                ):
                    self.zombies.append(Zombie(x, y))
                    break

    def spawn_pharmacies(self, count: int) -> None:
        for _ in range(count):
            while True:
                x, y = random.randrange(self.board_size), random.randrange(
                    self.board_size
                )
                if (
                    (x, y) not in self.pharmacy_positions
                    and (x, y) not in self.armory_positions
                    and not self.is_player_at(x, y)
                    and (x, y) not in self.barricade_positions
                    and all((z.x, z.y) != (x, y) for z in self.zombies)
                ):
                    self.pharmacy_positions.add((x, y))
                    break

    def spawn_armories(self, count: int) -> None:
        for _ in range(count):
            while True:
                x, y = random.randrange(self.board_size), random.randrange(
                    self.board_size
                )
                if (
                    (x, y) not in self.pharmacy_positions
                    and (x, y) not in self.armory_positions
                    and not self.is_player_at(x, y)
                    and (x, y) not in self.barricade_positions
                    and all((z.x, z.y) != (x, y) for z in self.zombies)
                ):
                    self.armory_positions.add((x, y))
                    break

    def spawn_supplies(self, count: int) -> None:
        for _ in range(count):
            while True:
                x, y = random.randrange(self.board_size), random.randrange(
                    self.board_size
                )
                if (
                    (x, y) not in self.supplies_positions
                    and (x, y) not in self.pharmacy_positions
                    and (x, y) not in self.armory_positions
                    and not self.is_player_at(x, y)
                    and (x, y) != self.antidote_pos
                    and (x, y) not in self.barricade_positions
                ):
                    self.supplies_positions.add((x, y))
                    break

    def spawn_antidote(self) -> None:
        while True:
            x, y = random.randrange(self.board_size), random.randrange(self.board_size)
            if (
                (x, y) not in self.supplies_positions
                and (x, y) not in self.pharmacy_positions
                and (x, y) not in self.armory_positions
                and (x, y) != self.start_pos
                and not self.is_player_at(x, y)
                and (x, y) not in self.barricade_positions
                and all((z.x, z.y) != (x, y) for z in self.zombies)
            ):
                self.antidote_pos = (x, y)
                break

    def spawn_keys(self) -> None:
        while True:
            x, y = random.randrange(self.board_size), random.randrange(self.board_size)
            if (
                (x, y) not in self.supplies_positions
                and (x, y) not in self.pharmacy_positions
                and (x, y) not in self.armory_positions
                and (x, y) != self.start_pos
                and not self.is_player_at(x, y)
                and (x, y) not in self.barricade_positions
                and all((z.x, z.y) != (x, y) for z in self.zombies)
            ):
                self.keys_pos = (x, y)
                break

    def spawn_fuel(self) -> None:
        while True:
            x, y = random.randrange(self.board_size), random.randrange(self.board_size)
            if (
                (x, y) not in self.supplies_positions
                and (x, y) not in self.pharmacy_positions
                and (x, y) not in self.armory_positions
                and (x, y) != self.start_pos
                and (x, y) != self.keys_pos
                and not self.is_player_at(x, y)
                and (x, y) not in self.barricade_positions
                and all((z.x, z.y) != (x, y) for z in self.zombies)
            ):
                self.fuel_pos = (x, y)
                break

    def spawn_radio_parts(self, count: int) -> None:
        for _ in range(count):
            while True:
                x, y = random.randrange(self.board_size), random.randrange(self.board_size)
                if (
                    (x, y) not in self.supplies_positions
                    and (x, y) not in self.pharmacy_positions
                    and (x, y) not in self.armory_positions
                    and (x, y) != self.start_pos
                    and (x, y) not in self.radio_positions
                    and not self.is_player_at(x, y)
                    and (x, y) not in self.barricade_positions
                    and all((z.x, z.y) != (x, y) for z in self.zombies)
                ):
                    self.radio_positions.add((x, y))
                    break

    def spawn_radio_tower(self) -> None:
        while True:
            x, y = random.randrange(self.board_size), random.randrange(self.board_size)
            if (
                (x, y) not in self.supplies_positions
                and (x, y) not in self.pharmacy_positions
                and (x, y) not in self.armory_positions
                and (x, y) != self.start_pos
                and not self.is_player_at(x, y)
                and (x, y) not in self.barricade_positions
                and all((z.x, z.y) != (x, y) for z in self.zombies)
            ):
                self.radio_tower_pos = (x, y)
                break

    # ------------------------------------------------------------------
    # Drawing helpers
    def draw_board(self) -> None:
        board = []
        for y in range(self.board_size):
            row: List[str] = []
            for x in range(self.board_size):
                if (x, y) in self.revealed:
                    row.append(".")
                else:
                    row.append("?")
            board.append(row)
        sx, sy = self.start_pos
        if (sx, sy) in self.revealed and not self.is_player_at(sx, sy):
            board[sy][sx] = "S"

        for p in self.players:
            board[p.y][p.x] = p.symbol
        if self.antidote_pos and self.antidote_pos in self.revealed:
            ax, ay = self.antidote_pos
            board[ay][ax] = ANTIDOTE_SYMBOL
        if self.keys_pos and self.keys_pos in self.revealed:
            kx, ky = self.keys_pos
            board[ky][kx] = KEYS_SYMBOL
        if self.fuel_pos and self.fuel_pos in self.revealed:
            fx, fy = self.fuel_pos
            board[fy][fx] = FUEL_SYMBOL
        for x, y in self.radio_positions:
            if (x, y) in self.revealed:
                board[y][x] = RADIO_PART_SYMBOL
        if self.radio_tower_pos and self.radio_tower_pos in self.revealed:
            tx, ty = self.radio_tower_pos
            board[ty][tx] = RADIO_TOWER_SYMBOL
        for x, y in self.pharmacy_positions:
            if (x, y) in self.revealed:
                board[y][x] = PHARMACY_SYMBOL
        for x, y in self.armory_positions:
            if (x, y) in self.revealed:
                board[y][x] = ARMORY_SYMBOL
        for x, y in self.barricade_positions:
            if (x, y) in self.revealed and not self.is_player_at(x, y):
                board[y][x] = BARRICADE_SYMBOL
        for x, y in self.supplies_positions:
            if (x, y) in self.revealed:
                board[y][x] = "R"
        for z in self.zombies:
            if (z.x, z.y) in self.revealed:
                board[z.y][z.x] = z.symbol

        print(
            "Health: {}    Hunger: {}/{}    Medkits: {}    Supplies: {}    Inventory: {}/{}    Tokens: {}    Weapon: {}".format(
                self.player.health,
                self.player.hunger,
                self.player.max_hunger,
                self.player.medkits,
                self.player.supplies,
                self.player.inventory_size,
                INVENTORY_LIMIT,
                self.double_move_tokens,
                "Y" if self.player.has_weapon else "N",
            )
        )
        for row in board:
            print(" ".join(row))

    # ------------------------------------------------------------------
    # Player actions
    def move_player(self, direction: str, steps: int = 1) -> bool:
        dx, dy = 0, 0
        if direction == "w":
            dy = -1
        elif direction == "s":
            dy = 1
        elif direction == "a":
            dx = -1
        elif direction == "d":
            dx = 1
        else:
            return False

        original = (self.player.x, self.player.y)
        for _ in range(steps):
            nx, ny = self.player.x + dx, self.player.y + dy
            if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                self.player.x, self.player.y = nx, ny
                self.reveal_area(nx, ny)
            else:
                self.player.x, self.player.y = original
                self.reveal_area(*original)
                return False
        return True

    def attack(self) -> bool:
        # Find adjacent zombie (4-directional)
        for z in list(self.zombies):
            if abs(z.x - self.player.x) + abs(z.y - self.player.y) == 1:
                hit_chance = WEAPON_HIT_CHANCE if self.player.has_weapon else ATTACK_HIT_CHANCE
                if random.random() < hit_chance:
                    self.zombies.remove(z)
                    self.zombies_killed += 1
                    print("You slay a zombie!")
                else:
                    self.player.health -= 1
                    print("Your attack misses! You take 1 damage.")
                if self.player.has_weapon:
                    self.spawn_zombie_near(
                        self.player.x,
                        self.player.y,
                        WEAPON_NOISE_ZOMBIE_CHANCE,
                    )
                    print("The gunshot echoes...")
                return True
        return False

    def scavenge(self) -> None:
        pos = (self.player.x, self.player.y)
        if pos == self.antidote_pos:
            self.antidote_pos = None
            self.player.has_antidote = True
            print("You secure the antidote!")
            return
        if pos == self.keys_pos:
            self.keys_pos = None
            self.player.has_keys = True
            print("You grab the car keys!")
            return
        if pos == self.fuel_pos:
            self.fuel_pos = None
            self.player.has_fuel = True
            print("You siphon some fuel!")
            return
        if pos in self.radio_positions:
            self.radio_positions.remove(pos)
            self.radio_parts_collected += 1
            print(
                f"You collect a radio part ({self.radio_parts_collected}/{RADIO_PARTS_REQUIRED})!"
            )
            return
        if pos in self.pharmacy_positions:
            self.pharmacy_positions.remove(pos)
            if self.player.inventory_size < INVENTORY_LIMIT:
                found = False
                if random.random() < PHARMACY_MEDKIT_CHANCE:
                    self.player.medkits += 1
                    found = True
                    print("You raid the pharmacy and find a medkit!")
                if random.random() < SCAVENGE_FIND_CHANCE:
                    self.player.supplies += 1
                    found = True
                    print("You grab some supplies.")
                if not found:
                    print("The pharmacy shelves are empty.")
            else:
                print("Your pack is full. You leave the pharmacy untouched.")
            return
        if pos in self.armory_positions:
            self.armory_positions.remove(pos)
            found = False
            if not self.player.has_weapon and random.random() < ARMORY_WEAPON_CHANCE:
                self.player.has_weapon = True
                found = True
                print("You find a weapon in the armory!")
            if self.player.inventory_size < INVENTORY_LIMIT:
                if random.random() < ARMORY_SUPPLY_CHANCE:
                    self.player.supplies += 1
                    found = True
                    print("You scavenge some useful gear.")
            elif not found:
                print("Your pack is full. You can't carry more.")
                return
            if not found:
                print("The armory is picked clean.")
            return
        if self.scenario == 4 and not self.called_rescue:
            if pos == self.start_pos:
                if self.has_signal_device:
                    self.called_rescue = True
                    self.rescue_timer = EVACUATION_TURNS
                    print("You radio for rescue! Hold out!")
                else:
                    print("You need a radio to signal for help.")
                return
            if self.radio_tower_pos and pos == self.radio_tower_pos:
                self.called_rescue = True
                self.rescue_timer = EVACUATION_TURNS
                print("You activate the tower and call for rescue! Hold out!")
                return

        if pos in self.supplies_positions:
            if self.player.inventory_size < INVENTORY_LIMIT:
                self.supplies_positions.remove(pos)
                self.player.supplies += 1
                print("You pick up a supply.")
            else:
                print("Your pack is full. You leave the supply behind.")
            return

        weapon_found = False
        if not self.player.has_weapon and random.random() < WEAPON_FIND_CHANCE:
            weapon_found = True

        if self.player.inventory_size >= INVENTORY_LIMIT and not weapon_found:
            print("Your pack is full. You can't carry more.")
            return

        found = False
        if weapon_found:
            self.player.has_weapon = True
            found = True
            print("You find a weapon!")

        if self.player.inventory_size < INVENTORY_LIMIT:
            if random.random() < SCAVENGE_FIND_CHANCE:
                self.player.supplies += 1
                found = True
                print("You find a supply!")
            if random.random() < MEDKIT_FIND_CHANCE:
                self.player.medkits += 1
                found = True
                print("You find a medkit!")
        if not found:
            print("You find nothing of use.")

    def use_medkit(self) -> bool:
        if self.player.medkits > 0 and self.player.health < self.player.max_health:
            self.player.medkits -= 1
            self.player.health = min(self.player.max_health, self.player.health + MEDKIT_HEAL)
            print("You use a medkit and recover health.")
            return True
        return False

    def eat_food(self) -> bool:
        if self.player.supplies > 0 and self.player.hunger < self.player.max_hunger:
            self.player.supplies -= 1
            self.player.hunger = min(
                self.player.max_hunger, self.player.hunger + HUNGER_EAT_AMOUNT
            )
            print("You eat some supplies and feel less hungry.")
            return True
        return False

    def build_barricade(self) -> bool:
        pos = (self.player.x, self.player.y)
        if pos in self.barricade_positions:
            print("There's already a barricade here.")
            return False
        if self.player.supplies >= BARRICADE_SUPPLY_COST:
            self.player.supplies -= BARRICADE_SUPPLY_COST
            self.barricade_positions.add(pos)
            print("You hastily build a barricade.")
            return True
        print("Not enough supplies to build a barricade.")
        return False

    # ------------------------------------------------------------------
    # Zombie behaviour
    def move_zombies(self) -> None:
        for z in list(self.zombies):
            target = min(self.players, key=lambda p: abs(z.x - p.x) + abs(z.y - p.y))
            dx = 0 if z.x == target.x else (1 if z.x < target.x else -1)
            dy = 0 if z.y == target.y else (1 if z.y < target.y else -1)
            nx, ny = z.x + dx, z.y + dy
            if (nx, ny) in self.barricade_positions:
                self.barricade_positions.remove((nx, ny))
                print("A zombie claws at a barricade, tearing it down!")
                continue
            if not any((other.x, other.y) == (nx, ny) for other in self.zombies):
                z.x, z.y = nx, ny
            for p in self.players:
                if z.x == p.x and z.y == p.y:
                    p.health -= 1
                    print(f"Player {p.symbol} is bitten! -1 health")

    def spawn_random_zombie(self) -> None:
        if random.random() < self.zombie_spawn_chance:
            self.spawn_zombies(1)
            print("A zombie shambles in from the darkness...")

    def spawn_zombie_near(self, x: int, y: int, chance: float) -> None:
        """Spawn a zombie adjacent to (x, y) with the given chance."""
        if random.random() < chance:
            candidates = [
                (nx, ny)
                for nx in range(x - 1, x + 2)
                for ny in range(y - 1, y + 2)
                if 0 <= nx < self.board_size
                and 0 <= ny < self.board_size
                and (nx, ny) != (x, y)
                and (nx, ny) not in self.barricade_positions
                and all((z.x, z.y) != (nx, ny) for z in self.zombies)
                and not self.is_player_at(nx, ny)
            ]
            if candidates:
                zx, zy = random.choice(candidates)
                self.zombies.append(Zombie(zx, zy))
                if (zx, zy) in self.revealed:
                    print("Noise draws a zombie nearby!")

    def random_event(self) -> None:
        """Trigger a random event at the end of the round."""
        event = random.choice(
            [
                "nothing",
                "heal",
                "supply",
                "horde",
                "storm",
                "adrenaline",
                "survivors",
                "fog",
            ]
        )
        if event == "heal":
            healed = False
            for p in self.players:
                if p.health < p.max_health:
                    p.health = min(p.max_health, p.health + 1)
                    healed = True
            if healed:
                print("Everyone catches their breath and recovers 1 health.")
        elif event == "supply":
            self.spawn_supplies(1)
            print("A supply crate drops nearby!")
        elif event == "horde":
            self.spawn_zombies(2)
            print("A small horde shambles in!")
        elif event == "storm":
            self.actions_per_turn = max(1, ACTIONS_PER_TURN - 1)
            print("A fierce storm slows you down. Only one action next turn!")
        elif event == "adrenaline":
            self.actions_per_turn = ACTIONS_PER_TURN + 1
            print("Adrenaline surges through you! You gain an extra action next turn.")
        elif event == "survivors":
            given = False
            for p in self.players:
                if p.inventory_size < INVENTORY_LIMIT:
                    if random.random() < 0.5:
                        p.supplies += 1
                        print(f"Friendly survivors toss supplies to player {p.symbol}!")
                    else:
                        p.medkits += 1
                        print(f"Friendly survivors share a medkit with player {p.symbol}!")
                    given = True
            if not given:
                print("Friendly survivors pass by but everyone's packs are full.")
        elif event == "fog":
            self.reveal_random_tiles(5)
            print("A gust of wind lifts the fog, revealing more of the area.")

    def apply_hunger(self) -> None:
        for p in self.players:
            p.hunger = max(0, p.hunger - HUNGER_DECAY)
            if p.hunger == 0:
                p.health -= HUNGER_STARVE_DAMAGE
                print(f"Player {p.symbol} is starving! -1 health")

    def check_achievements(self) -> None:
        """Unlock achievements based on campaign stats."""
        unlocked = set(self.campaign.get("achievements", []))
        new = False
        for key, cfg in ACHIEVEMENT_DEFS.items():
            if key not in unlocked and cfg["check"](self.campaign):
                unlocked.add(key)
                print(f"Achievement unlocked: {cfg['desc']}!")
                new = True
        if new:
            self.campaign["achievements"] = sorted(unlocked)

    # ------------------------------------------------------------------
    # Turn handling and game state
    def ai_turn(self, player: Player) -> None:
        """Execute a simple turn for an AI-controlled player."""
        actions_left = self.actions_per_turn
        while actions_left > 0 and player.health > 0:
            self.draw_board()
            # Heal if badly hurt
            if player.health <= player.max_health // 2 and player.medkits > 0:
                print(f"Player {player.symbol} uses a medkit.")
                self.use_medkit()
                actions_left -= 1
                continue
            # Eat if starving
            if player.hunger <= player.max_hunger // 2 and player.supplies > 0:
                print(f"Player {player.symbol} eats a supply.")
                self.eat_food()
                actions_left -= 1
                continue
            # Attack if a zombie is adjacent
            if any(
                abs(z.x - player.x) + abs(z.y - player.y) == 1 for z in self.zombies
            ):
                if self.attack():
                    actions_left -= 1
                    continue
            # Scavenge if inventory not full
            if player.inventory_size < INVENTORY_LIMIT:
                self.scavenge()
                actions_left -= 1
                continue
            # Otherwise move randomly
            dirs = ["w", "a", "s", "d"]
            random.shuffle(dirs)
            moved = False
            for d in dirs:
                if self.move_player(d):
                    moved = True
                    actions_left -= 1
                    break
            if not moved:
                break

    def player_turn(self, player: Player) -> None:
        self.player = player
        print(f"Player {player.symbol}'s turn")
        if player.is_ai:
            self.ai_turn(player)
            return
        actions_left = self.actions_per_turn
        while actions_left > 0 and self.player.health > 0:
            self.draw_board()
            cmd = input(
                f"Action ({actions_left} left) [w/a/s/d=move, f=attack, g=scavenge, h=medkit, e=eat, b=barricade, p=pass, q=save]: "
            ).strip().lower()

            if cmd in {"w", "a", "s", "d"}:
                steps = 1
                if self.double_move_tokens > 0:
                    use = input("Use double move token? [y/N]: ").strip().lower()
                    if use == "y":
                        steps = 2
                        self.double_move_tokens -= 1
                if self.move_player(cmd, steps):
                    if steps > 1:
                        self.spawn_zombie_near(
                            self.player.x,
                            self.player.y,
                            VEHICLE_NOISE_ZOMBIE_CHANCE,
                        )
                        print("The engine roar attracts the dead!")
                    actions_left -= 1
                else:
                    print("You can't move there!")
            elif cmd == "f":
                if self.attack():
                    actions_left -= 1
                else:
                    print("No zombie to attack!")
            elif cmd == "g":
                self.scavenge()
                actions_left -= 1
            elif cmd == "h":
                if self.use_medkit():
                    actions_left -= 1
                else:
                    print("No medkit to use!")
            elif cmd == "e":
                if self.eat_food():
                    actions_left -= 1
                else:
                    print("Nothing to eat!")
            elif cmd == "b":
                if self.build_barricade():
                    actions_left -= 1
            elif cmd == "p":
                break
            elif cmd == "q":
                self.save_game()
                self.keep_save = True
                print("Game saved.")
                raise SystemExit
            else:
                print("Unknown command.")

    def check_victory(self) -> bool:
        if self.scenario == 1:
            return self.player.has_antidote and (self.player.x, self.player.y) == self.start_pos
        if self.scenario == 2:
            return (
                self.player.has_keys
                and self.player.has_fuel
                and (self.player.x, self.player.y) == self.start_pos
            )
        if self.scenario == 3:
            return (
                self.radio_parts_collected >= RADIO_PARTS_REQUIRED
                and (self.player.x, self.player.y) == self.start_pos
            )
        if self.scenario == 4:
            return self.called_rescue and self.rescue_timer is not None and self.rescue_timer <= 0
        return False

    def check_defeat(self) -> bool:
        return self.player.health <= 0

    def run(self) -> None:
        if self.scenario == 1:
            print(
                "Find the antidote and return to the safe zone. Your pack holds at most eight items. Press Q to save and quit."
            )
        elif self.scenario == 2:
            print(
                "Locate keys and fuel then get back to the starting tile to escape. Your pack holds at most eight items. Press Q to save and quit."
            )
        elif self.scenario == 3:
            print(
                "Gather three radio parts and return to the safe zone. Your pack holds at most eight items. Press Q to save and quit."
            )
        elif self.scenario == 4:
            print(
                "Call for rescue and survive until help arrives. Scavenge the start tile with a radio device or find the tower. Press Q to save and quit."
            )
        if self.campaign.get("hp_bonus"):
            print(f"Campaign bonus: +{self.campaign['hp_bonus']} max health")
        if self.double_move_tokens:
            print(f"Campaign bonus: {self.double_move_tokens} double-move tokens")
        if self.has_signal_device:
            print("Campaign bonus: portable radio device")
        try:
            winner: Optional[Player] = None
            while True:
                for pl in list(self.players):
                    self.player_turn(pl)
                    if self.check_victory():
                        winner = pl
                        break
                    if self.check_defeat():
                        print(f"Player {pl.symbol} has fallen to the zombies...")
                        self.players.remove(pl)
                if winner or not self.players:
                    break
                self.move_zombies()
                for pl in list(self.players):
                    self.player = pl
                    if self.check_defeat():
                        print(f"Player {pl.symbol} has fallen to the zombies...")
                        self.players.remove(pl)
                if winner or not self.players:
                    break
                self.spawn_random_zombie()
                self.actions_per_turn = ACTIONS_PER_TURN
                self.random_event()
                self.apply_hunger()
                if self.called_rescue and self.rescue_timer is not None:
                    self.rescue_timer -= 1
                    for pl in self.players:
                        self.player = pl
                        if self.check_victory():
                            winner = pl
                            print(
                                "The rescue helicopter arrives and lifts you to safety. You win!"
                            )
                            break
                    if winner:
                        break
                self.turn += 1
                if self.turn >= self.turn_limit:
                    print("Time runs out and the area is overrun. You perish...")
                    break
            if winner:
                self.player = winner
                if self.scenario == 1:
                    print("You return with the antidote and escape. You win!")
                    self.campaign["hp_bonus"] = self.campaign.get("hp_bonus", 0) + 1
                    print("Max health increased for next game!")
                elif self.scenario == 2:
                    print("You fuel up the vehicle and drive to safety. You win!")
                    self.double_move_tokens += DOUBLE_MOVE_REWARD
                    print(
                        f"You gain {DOUBLE_MOVE_REWARD} double-move tokens for future runs!"
                    )
                elif self.scenario == 3:
                    print("You assemble the radio and send out a signal. You win!")
                    self.has_signal_device = True
                    self.campaign["signal_device"] = 1
                    print("A portable radio will aid you in the final escape!")
                elif self.scenario == 4 and not (
                    self.called_rescue and self.rescue_timer is not None and self.rescue_timer <= 0
                ):
                    print("The rescue helicopter arrives and lifts you to safety. You win!")
                completed = self.campaign.setdefault("completed_scenarios", [])
                if self.scenario not in completed:
                    completed.append(self.scenario)
            elif not self.players:
                print("All players have fallen to the zombies...")
        except (KeyboardInterrupt, EOFError):
            print("\nThanks for playing!")
        finally:
            self.campaign["hp_bonus"] = self.campaign.get("hp_bonus", 0)
            self.campaign["double_move_tokens"] = self.double_move_tokens
            self.campaign["signal_device"] = 1 if self.has_signal_device else 0
            self.campaign["zombies_killed"] = self.campaign.get("zombies_killed", 0) + self.zombies_killed
            self.check_achievements()
            save_campaign(self.campaign)
            if not self.keep_save and os.path.exists(SAVE_FILE):
                os.remove(SAVE_FILE)


if __name__ == "__main__":
    if os.path.exists(SAVE_FILE) and input("Load saved game? [y/N]: ").strip().lower() == "y":
        game = Game.load_game()
    else:
        diff = input("Choose difficulty [easy/normal/hard]: ").strip().lower() or "normal"
        players = input("Number of players [1-4]: ").strip() or "1"
        scen = input("Choose scenario [1/2/3/4]: ").strip() or "1"
        try:
            scen_num = int(scen)
        except ValueError:
            scen_num = 1
        try:
            num_players = max(1, min(4, int(players)))
        except ValueError:
            num_players = 1
        bots = input(f"AI players [0-{max(0, num_players - 1)}]: ").strip() or "0"
        try:
            num_ai = max(0, min(num_players - 1, int(bots)))
        except ValueError:
            num_ai = 0
        game = Game(diff, scen_num, num_players, num_ai)
    game.run()

