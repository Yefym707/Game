"""Turn-based survival board game prototype.

This module implements a simple console survival game where one or more
players scour a zombie infested grid for an antidote then race back to
safety.

Features
--------
* 10x10 board with up to six players, zombies and supply tokens.
* Each player has two actions per turn: move, scout, attack, scavenge or pass.
* Resting lets survivors regain hunger or a point of health.
* Melee combat with a chance to hit. Failed attacks cost health.
* Scavenging draws from a finite loot deck to mimic board-game card draws.
* Zombies pursue the player and new ones may spawn each round. Counts scale
  with how many survivors are in play.
* Player wins by finding the antidote and returning to the starting tile.
  Victory grants +1 max health for the next run, saved to disk.
* Hunger mechanic – eat supplies to avoid starving each round.
* Simple crafting allows turning supplies into medkits, traps, campfires or
  noisy molotov cocktails that burn adjacent zombies.
* Loud actions leave behind noise tokens that can draw zombies at the
  end of each round, mirroring board-game noise markers.
* Achievements track scenario victories and feats across campaigns.
* Experience points from kills and wins allow survivors to level up and
  gain permanent max health.
* Attempt to steal items from survivors sharing your tile; failure
  results in a scuffle and health loss.
* Survivors may brawl with each other, but fights are risky and attract
  additional zombies through noise tokens.
* Hidden traps may injure careless survivors or destroy wandering zombies,
  and survivors can set their own snares. Traps can also be disarmed to
  recover useful supplies.
* Campfires illuminate nearby tiles each round, granting shared visibility to
  survivors huddled around the fire.
* Rain events dampen noise, making zombies less likely to spawn from noise
  tokens in the following round.
* Zombie bites may infect survivors; without an antidote they will turn
  after a few rounds.

The code is intentionally compact and uses only the Python standard
library so it can run in any environment with Python 3.12 or newer.
"""

from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from collections import deque


BOARD_SIZE = 10
ACTIONS_PER_TURN = 2
MAX_PLAYERS = 6
STARTING_HEALTH = 10
STARTING_ZOMBIES = 5
STARTING_SUPPLIES = 5
INVENTORY_LIMIT = 8
ATTACK_HIT_CHANCE = 0.7
SCAVENGE_FIND_CHANCE = 0.5
ZOMBIE_SPAWN_CHANCE = 0.3
MEDKIT_HEAL = 3
WEAPON_HIT_CHANCE = 0.9
TURN_LIMIT = 20
REVEAL_RADIUS = 1
REVEAL_SUPPLY_CHANCE = 0.05
REVEAL_ZOMBIE_CHANCE = 0.05
STARTING_HUNGER = 10
HUNGER_DECAY = 1
HUNGER_EAT_AMOUNT = 4
HUNGER_STARVE_DAMAGE = 1
XP_PER_ZOMBIE = 1
XP_SCENARIO_WIN = 5
LEVEL_XP_BASE = 10

CAMPAIGN_FILE = "campaign_save.json"
SAVE_FILE = "savegame.json"
ANTIDOTE_SYMBOL = "A"
KEYS_SYMBOL = "K"
FUEL_SYMBOL = "F"
RADIO_PART_SYMBOL = "P"
RADIO_TOWER_SYMBOL = "T"
MEDKIT_SYMBOL = "H"
WEAPON_SYMBOL = "G"
RADIO_PARTS_REQUIRED = 3
EVACUATION_TURNS = 5
EVACUATION_CAPACITY = 2  # rescue seats available in final scenario
DOUBLE_MOVE_REWARD = 5
WEAPON_NOISE_ZOMBIE_CHANCE = 0.3
VEHICLE_NOISE_ZOMBIE_CHANCE = 0.5
NOISE_DURATION = 2  # rounds noise tokens persist
SCOUT_RADIUS = 2  # tiles revealed when scouting
RAIN_NOISE_MULTIPLIER = 0.5  # noise chance multiplier during rain events

# Special tile settings
PHARMACY_SYMBOL = "M"
ARMORY_SYMBOL = "W"
PHARMACY_COUNT = 3
ARMORY_COUNT = 2
PHARMACY_MEDKIT_CHANCE = 0.8
ARMORY_WEAPON_CHANCE = 0.6
ARMORY_SUPPLY_CHANCE = 0.4

# Shelter settings
SHELTER_SYMBOL = "U"
SHELTER_COUNT = 2


# Wall settings
WALL_SYMBOL = "#"
WALL_COUNT = 12


# Barricade settings
BARRICADE_SYMBOL = "B"
BARRICADE_SUPPLY_COST = 2

# Crafting settings
MEDKIT_CRAFT_COST = 3
MOLOTOV_SYMBOL = "L"
MOLOTOV_SUPPLY_COST = 1
MOLOTOV_NOISE_ZOMBIE_CHANCE = 0.6
TRAP_CRAFT_COST = 2
FLASHLIGHT_SYMBOL = "I"
FLASHLIGHT_CRAFT_COST = 2

# Campfire settings
CAMPFIRE_SYMBOL = "C"
CAMPFIRE_CRAFT_COST = 2
CAMPFIRE_DURATION = 5
CAMPFIRE_LIGHT_RADIUS = 2  # tiles revealed around an active campfire

# Trap settings
TRAP_SYMBOL = "!"
TRAP_DAMAGE = 2
REVEAL_TRAP_CHANCE = 0.03

# PvP stealing settings
STEAL_SUCCESS_CHANCE = 0.5

# Infection settings
INFECTION_CHANCE = 0.3  # chance a zombie bite causes infection
INFECTION_TURNS = 5  # turns until an infected survivor turns

# PvP attack settings
PVP_ATTACK_HIT_CHANCE = 0.5
PVP_ATTACK_NOISE_CHANCE = 0.8

# Player role definitions
# These light touches give each survivor a distinct flavor similar to
# character cards in a tabletop game. Roles grant small passive bonuses
# but keep the overall ruleset simple.
ROLE_DEFS = {
    "fighter": "Improved attack rolls",
    "medic": "Better healing from medkits and rest",
    "scout": "Wider vision and superior scavenging",
    "engineer": "Cheaper barricades and crafted gear",
}

# End-of-round event and loot deck configuration is now loaded from an
# external JSON file to ease modding. Defaults are provided here as
# fallbacks if the file is missing or malformed.
DECK_CONFIG_FILE = "decks.json"
BOARD_LAYOUT_FILE = "board_layout.json"

DEFAULT_EVENT_CARD_COUNTS = {
    "nothing": 3,
    "heal": 1,
    "supply": 1,
    "horde": 1,
    "storm": 1,
    "adrenaline": 1,
    "survivors": 1,
    "rain": 1,
    "fog": 1,
    "heatwave": 1,
    "firebomb": 1,
    "blizzard": 1,
    "earthquake": 1,
    "trader": 1,
}

DEFAULT_LOOT_CARD_COUNTS = {
    "supply": 8,
    "medkit": 4,
    "weapon": 2,
    "flashlight": 1,
    "nothing": 10,
}


def load_deck_config(path: str) -> tuple[dict[str, int], dict[str, int]]:
    """Load event and loot deck counts from *path* if it exists."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        events = {k: int(v) for k, v in data.get("events", {}).items()}
        loot = {k: int(v) for k, v in data.get("loot", {}).items()}
        if not events:
            events = DEFAULT_EVENT_CARD_COUNTS.copy()
        if not loot:
            loot = DEFAULT_LOOT_CARD_COUNTS.copy()
        return events, loot
    except (OSError, ValueError):
        return DEFAULT_EVENT_CARD_COUNTS.copy(), DEFAULT_LOOT_CARD_COUNTS.copy()


EVENT_CARD_COUNTS, LOOT_CARD_COUNTS = load_deck_config(DECK_CONFIG_FILE)


def load_board_layout(path: str, size: int) -> dict:
    """Load a preset board layout from *path*.

    The file should contain a JSON array of strings, one per row. Characters
    map to tiles using the same symbols as the in-game board:

    ``#`` wall, ``U`` shelter, ``M`` pharmacy, ``W`` armory and ``S`` start
    position. Missing or malformed files simply yield an empty layout, letting
    the game fall back to its procedural placement. Any rows beyond ``size`` or
    unknown characters are ignored.
    """

    layout = {
        "walls": set(),
        "shelters": set(),
        "pharmacies": set(),
        "armories": set(),
        "start_pos": None,
    }
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        rows = data if isinstance(data, list) else data.get("rows", [])
        for y, row in enumerate(rows):
            if y >= size or not isinstance(row, str):
                break
            for x, ch in enumerate(row[:size]):
                if ch == WALL_SYMBOL:
                    layout["walls"].add((x, y))
                elif ch == SHELTER_SYMBOL:
                    layout["shelters"].add((x, y))
                elif ch == PHARMACY_SYMBOL:
                    layout["pharmacies"].add((x, y))
                elif ch == ARMORY_SYMBOL:
                    layout["armories"].add((x, y))
                elif ch == "S":
                    layout["start_pos"] = (x, y)
    except (OSError, ValueError):
        return layout
    return layout

# Day/night cycle settings
DAY_LENGTH = 3  # rounds of daylight
NIGHT_LENGTH = 2  # rounds of night
NIGHT_SPAWN_MULTIPLIER = 1.5
NIGHT_REVEAL_PENALTY = 1  # visibility penalty at night

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
    "scenario_1": {
        "desc": "Complete scenario 1",
        "check": lambda data: 1 in data.get("completed_scenarios", []),
    },
    "scenario_2": {
        "desc": "Complete scenario 2",
        "check": lambda data: 2 in data.get("completed_scenarios", []),
    },
    "scenario_3": {
        "desc": "Complete scenario 3",
        "check": lambda data: 3 in data.get("completed_scenarios", []),
    },
    "scenario_4": {
        "desc": "Complete scenario 4",
        "check": lambda data: 4 in data.get("completed_scenarios", []),
    },
    "last_breath": {
        "desc": "Win a scenario with only 1 HP remaining",
        "check": lambda data: data.get("last_victory_lowest_hp") == 1,
    },
    "pacifist": {
        "desc": "Win a scenario without killing any zombies",
        "check": lambda data: data.get("last_victory_zombies_killed", 1) == 0,
    },
}


# Flavor text for each scenario. These short snippets act like
# story cards in a tabletop campaign, giving players context before
# play begins and after it ends.
SCENARIO_INTROS = {
    1: (
        "Rumors speak of a hidden lab containing a vital serum. "
        "Find the antidote and bring it back to safety."
    ),
    2: (
        "With a sample secured, escape becomes the priority. "
        "Search the ruins for car keys and enough fuel to get away."
    ),
    3: (
        "No rescue will arrive unless someone makes contact. "
        "Scavenge radio parts and assemble a working transmitter."
    ),
    4: (
        "All preparations lead here. Call for rescue and hold out "
        "until help arrives."
    ),
}

SCENARIO_OUTROS = {
    1: "The precious serum buys the group a little more time.",
    2: "An engine roars to life, cutting through the dead silence.",
    3: "The radio crackles with distant hope as your signal goes out.",
    4: (
        "Rotting streets shrink below as the last survivors lift off "
        "toward uncertain safety."
    ),
}

SCENARIO_FAILURES = {
    1: "Without the cure the infection spreads unchecked.",
    2: "The path out remains blocked and the horde closes in.",
    3: "Static is the only reply. Rescue never hears your plea.",
    4: "No one reaches safety. The outbreak consumes everything.",
}


def roll_check(chance: float, sides: int = 10, label: str = "Roll", log: bool = True) -> bool:
    """Return True if a dice roll succeeds against ``chance``.

    The function rolls a ``sides``-sided die, optionally prints the result,
    and compares it against ``chance`` (0.0–1.0). This mirrors the tactile
    randomness of tabletop games by surfacing the die roll to the player.
    """
    threshold = max(1, int(chance * sides))
    roll = random.randint(1, sides)
    if log:
        print(f"{label} d{sides}: {roll} (need <= {threshold})")
    return roll <= threshold


def load_campaign() -> dict:
    """Load persistent campaign data from disk."""
    data = {
        "hp_bonus": 0,
        "double_move_tokens": 0,
        "signal_device": 0,
        "zombies_killed": 0,
        "completed_scenarios": [],
        "achievements": [],
        "xp": 0,
        "level": 1,
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


def create_event_deck() -> deque[str]:
    """Return a shuffled deck of event cards based on EVENT_CARD_COUNTS."""
    deck: List[str] = []
    for name, count in EVENT_CARD_COUNTS.items():
        deck.extend([name] * count)
    random.shuffle(deck)
    return deque(deck)


def create_loot_deck() -> deque[str]:
    """Return a shuffled deck of loot cards based on LOOT_CARD_COUNTS."""
    deck: List[str] = []
    for name, count in LOOT_CARD_COUNTS.items():
        deck.extend([name] * count)
    random.shuffle(deck)
    return deque(deck)


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
        role: str = "fighter",
    ) -> None:
        super().__init__(x, y, symbol)
        self.is_ai: bool = is_ai
        self.role: str = role
        self.max_health: int = starting_health
        self.health: int = starting_health
        self.max_hunger: int = STARTING_HUNGER
        self.hunger: int = STARTING_HUNGER
        self.supplies: int = 0
        self.medkits: int = 0
        self.molotovs: int = 0
        self.has_antidote: bool = False
        self.has_keys: bool = False
        self.has_fuel: bool = False
        self.has_weapon: bool = False
        self.has_flashlight: bool = False
        self.kills: int = 0
        self.infection_turns: int = 0

    @property
    def inventory_size(self) -> int:
        """Total number of items currently carried."""
        return self.supplies + self.medkits + self.molotovs


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
        cooperative: bool = False,
        roles: Optional[List[str]] = None,
    ) -> None:
        settings = DIFFICULTY_SETTINGS.get(difficulty.lower())
        if settings is None:
            raise ValueError("Unknown difficulty")
        self.difficulty = difficulty.lower()
        self.scenario = scenario
        self.cooperative = cooperative
        self.campaign = load_campaign()
        self.level = self.campaign.get("level", 1)
        # Small consolation stash awarded after failed runs
        bonus_supplies = self.campaign.pop("supply_bonus", 0)
        if bonus_supplies:
            save_campaign(self.campaign)
        self.xp_gained = 0
        self.double_move_tokens = self.campaign.get("double_move_tokens", 0)
        self.has_signal_device = bool(self.campaign.get("signal_device"))
        self.total_players = max(1, min(MAX_PLAYERS, num_players))
        extra_players = max(0, self.total_players - 1)
        # Scale zombie spawns with campaign level to keep tension high
        level_bonus = 0.02 * (self.level - 1)
        self.zombie_spawn_chance = (
            settings["zombie_spawn_chance"] + 0.05 * extra_players + level_bonus
        )
        self.base_zombie_spawn_chance = self.zombie_spawn_chance
        self.reveal_radius = REVEAL_RADIUS
        self.is_night = False
        self.phase_turns = DAY_LENGTH
        self.turn_limit = settings["turn_limit"]
        self.evacuation_turns = EVACUATION_TURNS + extra_players
        starting_health = settings["starting_health"] + self.campaign.get("hp_bonus", 0)
        layout = load_board_layout(BOARD_LAYOUT_FILE, self.board_size)
        start_pos = layout.get("start_pos") or (self.board_size // 2, self.board_size // 2)
        offsets = [(0, 0), (0, 1), (1, 0), (-1, 0), (0, -1), (1, 1)]
        self.players: List[Player] = []
        total_players = self.total_players
        num_ai = max(0, min(num_ai, total_players - 1))
        role_list = roles or []
        for i in range(total_players):
            dx, dy = offsets[i % len(offsets)]
            is_ai = i >= total_players - num_ai
            role = (
                role_list[i]
                if i < len(role_list)
                else random.choice(list(ROLE_DEFS.keys()))
            )
            self.players.append(
                Player(
                    start_pos[0] + dx,
                    start_pos[1] + dy,
                    starting_health,
                    str(i + 1),
                    is_ai,
                    role,
                )
            )
        if bonus_supplies:
            for p in self.players:
                p.supplies = min(INVENTORY_LIMIT, p.supplies + bonus_supplies)
        self.all_players: List[Player] = list(self.players)
        self.player: Player = self.players[0]
        self.start_pos = start_pos
        self.antidote_pos: Optional[Tuple[int, int]] = None
        self.keys_pos: Optional[Tuple[int, int]] = None
        self.fuel_pos: Optional[Tuple[int, int]] = None
        self.radio_positions: Set[Tuple[int, int]] = set()
        self.radio_tower_pos: Optional[Tuple[int, int]] = None
        self.radio_parts_collected = 0
        self.called_rescue = False
        self.rescue_timer: Optional[int] = None
        self.evacuation_capacity = EVACUATION_CAPACITY
        self.evacuated_players: List[Player] = []
        self.zombies: List[Zombie] = []
        self.supplies_positions: Set[Tuple[int, int]] = set()
        self.medkit_positions: Set[Tuple[int, int]] = set()
        self.weapon_positions: Set[Tuple[int, int]] = set()
        self.molotov_positions: Set[Tuple[int, int]] = set()
        self.flashlight_positions: Set[Tuple[int, int]] = set()
        self.trap_positions: Set[Tuple[int, int]] = set()
        self.pharmacy_positions: Set[Tuple[int, int]] = set(layout.get("pharmacies", set()))
        self.armory_positions: Set[Tuple[int, int]] = set(layout.get("armories", set()))
        self.shelter_positions: Set[Tuple[int, int]] = set(layout.get("shelters", set()))
        self.barricade_positions: Set[Tuple[int, int]] = set()
        self.campfires: Dict[Tuple[int, int], int] = {}
        self.noise_markers: List[Tuple[int, int, float, int]] = []
        self.noise_dampener_turns = 0
        self.visibility_penalty_turns = 0
        self.hunger_penalty_turns = 0
        self.revealed: Set[Tuple[int, int]] = set()
        self.wall_positions: Set[Tuple[int, int]] = set(layout.get("walls", set()))
        self.spawn_walls(max(0, WALL_COUNT - len(self.wall_positions)))
        self.spawn_shelters(max(0, SHELTER_COUNT - len(self.shelter_positions)))
        self.spawn_zombies(settings["starting_zombies"] + extra_players)
        self.spawn_pharmacies(max(0, PHARMACY_COUNT - len(self.pharmacy_positions)))
        self.spawn_armories(max(0, ARMORY_COUNT - len(self.armory_positions)))
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
            self.reveal_area(p.x, p.y, player=p)
        self.turn: int = 0
        self.actions_per_turn: int = ACTIONS_PER_TURN
        self.keep_save = False
        self.zombies_killed: int = 0
        self.lowest_survivor_hp: Optional[int] = None
        self.event_deck: deque[str] = create_event_deck()
        self.loot_deck: deque[str] = create_loot_deck()

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
                    "molotovs": p.molotovs,
                    "kills": p.kills,
                    "has_antidote": p.has_antidote,
                    "has_keys": p.has_keys,
                    "has_fuel": p.has_fuel,
                    "has_weapon": p.has_weapon,
                    "has_flashlight": p.has_flashlight,
                    "infection_turns": p.infection_turns,
                    "symbol": p.symbol,
                    "is_ai": getattr(p, "is_ai", False),
                    "role": p.role,
                }
                for p in self.players
            ],
            "zombies": [(z.x, z.y) for z in self.zombies],
            "supplies_positions": list(self.supplies_positions),
            "medkit_positions": list(self.medkit_positions),
            "weapon_positions": list(self.weapon_positions),
            "molotov_positions": list(self.molotov_positions),
            "flashlight_positions": list(self.flashlight_positions),
            "trap_positions": list(self.trap_positions),
            "pharmacy_positions": list(self.pharmacy_positions),
            "armory_positions": list(self.armory_positions),
            "shelter_positions": list(self.shelter_positions),
            "wall_positions": list(self.wall_positions),
            "barricade_positions": list(self.barricade_positions),
            "campfires": [[x, y, t] for (x, y), t in self.campfires.items()],
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
            "cooperative": self.cooperative,
            "event_deck": list(self.event_deck),
            "loot_deck": list(self.loot_deck),
            "noise_markers": [list(n) for n in self.noise_markers],
            "noise_dampener_turns": self.noise_dampener_turns,
            "visibility_penalty_turns": self.visibility_penalty_turns,
            "hunger_penalty_turns": self.hunger_penalty_turns,
            "xp_gained": self.xp_gained,
            "zombie_spawn_chance": self.zombie_spawn_chance,
            "base_zombie_spawn_chance": self.base_zombie_spawn_chance,
            "is_night": self.is_night,
            "phase_turns": self.phase_turns,
            "reveal_radius": self.reveal_radius,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Game":
        """Reconstruct a Game instance from serialized data."""
        game = cls(
            data["difficulty"],
            data["scenario"],
            len(data["players"]),
            cooperative=data.get("cooperative", False),
        )
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
            p.molotovs = pdata.get("molotovs", 0)
            p.kills = pdata.get("kills", 0)
            p.has_antidote = pdata["has_antidote"]
            p.has_keys = pdata["has_keys"]
            p.has_fuel = pdata["has_fuel"]
            p.has_weapon = pdata["has_weapon"]
            p.has_flashlight = pdata.get("has_flashlight", False)
            p.infection_turns = pdata.get("infection_turns", 0)
            p.symbol = pdata.get("symbol", p.symbol)
            p.is_ai = pdata.get("is_ai", False)
            p.role = pdata.get("role", "fighter")
        game.player = game.players[data.get("current_player", 0)]
        game.zombies = [Zombie(x, y) for x, y in data["zombies"]]
        game.supplies_positions = {tuple(pos) for pos in data["supplies_positions"]}
        game.medkit_positions = {tuple(pos) for pos in data.get("medkit_positions", [])}
        game.weapon_positions = {tuple(pos) for pos in data.get("weapon_positions", [])}
        game.molotov_positions = {tuple(pos) for pos in data.get("molotov_positions", [])}
        game.flashlight_positions = {tuple(pos) for pos in data.get("flashlight_positions", [])}
        game.trap_positions = {tuple(pos) for pos in data.get("trap_positions", [])}
        game.pharmacy_positions = {
            tuple(pos) for pos in data.get("pharmacy_positions", [])
        }
        game.armory_positions = {
            tuple(pos) for pos in data.get("armory_positions", [])
        }
        game.shelter_positions = {
            tuple(pos) for pos in data.get("shelter_positions", [])
        }
        game.wall_positions = {
            tuple(pos) for pos in data.get("wall_positions", [])
        }
        game.barricade_positions = {
            tuple(pos) for pos in data.get("barricade_positions", [])
        }
        game.campfires = {
            (pos[0], pos[1]): pos[2]
            for pos in data.get("campfires", [])
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
        game.xp_gained = data.get("xp_gained", 0)
        game.event_deck = deque(data.get("event_deck", []))
        game.loot_deck = deque(data.get("loot_deck", []))
        game.noise_markers = [
            (
                n[0],
                n[1],
                n[2],
                n[3] if len(n) > 3 else NOISE_DURATION,
            )
            for n in data.get("noise_markers", [])
        ]
        game.noise_dampener_turns = data.get("noise_dampener_turns", 0)
        game.visibility_penalty_turns = data.get("visibility_penalty_turns", 0)
        game.hunger_penalty_turns = data.get("hunger_penalty_turns", 0)
        game.zombie_spawn_chance = data.get("zombie_spawn_chance", game.zombie_spawn_chance)
        game.base_zombie_spawn_chance = data.get(
            "base_zombie_spawn_chance", game.zombie_spawn_chance
        )
        game.is_night = data.get("is_night", False)
        game.phase_turns = data.get(
            "phase_turns", NIGHT_LENGTH if game.is_night else DAY_LENGTH
        )
        game.reveal_radius = data.get(
            "reveal_radius",
            REVEAL_RADIUS if not game.is_night else max(0, REVEAL_RADIUS - NIGHT_REVEAL_PENALTY),
        )
        game.all_players = list(game.players)
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

    def reveal_area(
        self,
        x: int,
        y: int,
        radius: Optional[int] = None,
        player: Optional[Player] = None,
    ) -> None:
        """Reveal tiles around ``(x, y)`` within ``radius``.

        If ``player`` has a flashlight, the night visibility penalty is
        ignored.
        """
        if radius is None:
            radius = self.reveal_radius
        if player and getattr(player, "role", "") == "scout":
            radius += 1
        if self.is_night:
            if player and getattr(player, "has_flashlight", False):
                radius = max(radius, REVEAL_RADIUS)
            else:
                radius = max(0, radius - NIGHT_REVEAL_PENALTY)
        if self.visibility_penalty_turns > 0:
            radius = max(0, radius - 1)
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                    if (nx, ny) not in self.revealed:
                        self.revealed.add((nx, ny))
                        if (
                            (nx, ny) not in self.supplies_positions
                            and (nx, ny) not in self.medkit_positions
                            and (nx, ny) not in self.weapon_positions
                            and (nx, ny) not in self.molotov_positions
                            and (nx, ny) not in self.flashlight_positions
                            and (nx, ny) not in self.trap_positions
                            and (nx, ny) != self.antidote_pos
                            and (nx, ny) != self.keys_pos
                            and (nx, ny) != self.fuel_pos
                            and (nx, ny) not in self.radio_positions
                            and (nx, ny) != self.radio_tower_pos
                            and (nx, ny) not in self.pharmacy_positions
                            and (nx, ny) not in self.armory_positions
                            and (nx, ny) not in self.shelter_positions
                            and (nx, ny) not in self.barricade_positions
                            and (nx, ny) not in self.campfires
                            and (nx, ny) not in self.wall_positions
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
                            elif roll < (
                                REVEAL_SUPPLY_CHANCE
                                + REVEAL_ZOMBIE_CHANCE
                                + REVEAL_TRAP_CHANCE
                            ):
                                self.trap_positions.add((nx, ny))

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
    def spawn_walls(self, count: int) -> None:
        for _ in range(count):
            while True:
                x, y = random.randrange(self.board_size), random.randrange(
                    self.board_size
                )
                if (
                    (x, y) != self.start_pos
                    and not self.is_player_at(x, y)
                    and (x, y) not in self.wall_positions
                ):
                    self.wall_positions.add((x, y))
                    break

    def quake_walls(self, changes: int = 3) -> None:
        """Randomly collapse or raise walls to simulate an earthquake."""
        done = 0
        attempts = 0
        occupied = lambda x, y: (
            self.is_player_at(x, y)
            or (x, y) in {(z.x, z.y) for z in self.zombies}
            or (x, y) in self.barricade_positions
            or (x, y) in self.campfires
            or (x, y) in self.shelter_positions
            or (x, y) in self.trap_positions
            or (x, y) in self.supplies_positions
            or (x, y) in self.medkit_positions
            or (x, y) in self.weapon_positions
            or (x, y) in self.molotov_positions
            or (x, y) in self.flashlight_positions
            or (x, y) in self.radio_positions
            or (x, y) == self.radio_tower_pos
            or (x, y) == self.antidote_pos
            or (x, y) == self.keys_pos
            or (x, y) == self.fuel_pos
        )
        while done < changes and attempts < changes * 10:
            attempts += 1
            x, y = random.randrange(self.board_size), random.randrange(self.board_size)
            if (x, y) == self.start_pos:
                continue
            if (x, y) in self.wall_positions:
                self.wall_positions.remove((x, y))
                if (x, y) in self.revealed:
                    print("A wall crumbles.")
                done += 1
            elif not occupied(x, y):
                self.wall_positions.add((x, y))
                if (x, y) in self.revealed:
                    print("Rubble blocks a new path.")
                done += 1

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
                    and (x, y) not in self.wall_positions
                    and (x, y) not in self.medkit_positions
                    and (x, y) not in self.weapon_positions
                    and (x, y) not in self.molotov_positions
                    and (x, y) not in self.trap_positions
                    and (x, y) not in self.campfires
                    and (x, y) not in self.shelter_positions
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
                    and (x, y) not in self.shelter_positions
                    and not self.is_player_at(x, y)
                    and (x, y) not in self.barricade_positions
                    and (x, y) not in self.wall_positions
                    and (x, y) not in self.trap_positions
                    and (x, y) not in self.campfires
                    and (x, y) not in self.medkit_positions
                    and (x, y) not in self.weapon_positions
                    and (x, y) not in self.molotov_positions
                    and (x, y) not in self.supplies_positions
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
                    and (x, y) not in self.shelter_positions
                    and not self.is_player_at(x, y)
                    and (x, y) not in self.barricade_positions
                    and (x, y) not in self.wall_positions
                    and (x, y) not in self.trap_positions
                    and (x, y) not in self.campfires
                    and (x, y) not in self.medkit_positions
                    and (x, y) not in self.weapon_positions
                    and (x, y) not in self.molotov_positions
                    and (x, y) not in self.supplies_positions
                    and all((z.x, z.y) != (x, y) for z in self.zombies)
                ):
                    self.armory_positions.add((x, y))
                    break

    def spawn_shelters(self, count: int) -> None:
        for _ in range(count):
            while True:
                x, y = random.randrange(self.board_size), random.randrange(self.board_size)
                if (
                    (x, y) not in self.shelter_positions
                    and (x, y) not in self.pharmacy_positions
                    and (x, y) not in self.armory_positions
                    and not self.is_player_at(x, y)
                    and (x, y) != self.start_pos
                    and (x, y) not in self.barricade_positions
                    and (x, y) not in self.wall_positions
                    and (x, y) not in self.trap_positions
                    and (x, y) not in self.campfires
                    and (x, y) not in self.medkit_positions
                    and (x, y) not in self.weapon_positions
                    and (x, y) not in self.molotov_positions
                    and (x, y) not in self.supplies_positions
                    and all((z.x, z.y) != (x, y) for z in self.zombies)
                ):
                    self.shelter_positions.add((x, y))
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
                    and (x, y) not in self.shelter_positions
                    and not self.is_player_at(x, y)
                    and (x, y) != self.antidote_pos
                    and (x, y) not in self.barricade_positions
                    and (x, y) not in self.wall_positions
                    and (x, y) not in self.trap_positions
                    and (x, y) not in self.campfires
                    and (x, y) not in self.medkit_positions
                    and (x, y) not in self.weapon_positions
                    and (x, y) not in self.molotov_positions
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
                and (x, y) not in self.shelter_positions
                and (x, y) != self.start_pos
                and not self.is_player_at(x, y)
                and (x, y) not in self.barricade_positions
                and (x, y) not in self.wall_positions
                and (x, y) not in self.trap_positions
                and (x, y) not in self.campfires
                and (x, y) not in self.medkit_positions
                and (x, y) not in self.weapon_positions
                and (x, y) not in self.molotov_positions
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
                and (x, y) not in self.shelter_positions
                and (x, y) != self.start_pos
                and not self.is_player_at(x, y)
                and (x, y) not in self.barricade_positions
                and (x, y) not in self.trap_positions
                and (x, y) not in self.campfires
                and (x, y) not in self.medkit_positions
                and (x, y) not in self.weapon_positions
                and (x, y) not in self.molotov_positions
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
                and (x, y) not in self.shelter_positions
                and (x, y) != self.start_pos
                and (x, y) != self.keys_pos
                and not self.is_player_at(x, y)
                and (x, y) not in self.barricade_positions
                and (x, y) not in self.wall_positions
                and (x, y) not in self.trap_positions
                and (x, y) not in self.campfires
                and (x, y) not in self.medkit_positions
                and (x, y) not in self.weapon_positions
                and (x, y) not in self.molotov_positions
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
                    and (x, y) not in self.shelter_positions
                    and (x, y) != self.start_pos
                    and (x, y) not in self.radio_positions
                    and not self.is_player_at(x, y)
                    and (x, y) not in self.barricade_positions
                    and (x, y) not in self.wall_positions
                    and (x, y) not in self.trap_positions
                    and (x, y) not in self.campfires
                    and (x, y) not in self.medkit_positions
                    and (x, y) not in self.weapon_positions
                    and (x, y) not in self.molotov_positions
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
                and (x, y) not in self.shelter_positions
                and (x, y) not in self.wall_positions
                and (x, y) != self.start_pos
                and not self.is_player_at(x, y)
                and (x, y) not in self.barricade_positions
                and (x, y) not in self.trap_positions
                and (x, y) not in self.campfires
                and (x, y) not in self.medkit_positions
                and (x, y) not in self.weapon_positions
                and (x, y) not in self.molotov_positions
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
        for x, y in self.shelter_positions:
            if (x, y) in self.revealed and not self.is_player_at(x, y):
                board[y][x] = SHELTER_SYMBOL
        for x, y in self.wall_positions:
            if (x, y) in self.revealed:
                board[y][x] = WALL_SYMBOL
        for x, y in self.barricade_positions:
            if (x, y) in self.revealed and not self.is_player_at(x, y):
                board[y][x] = BARRICADE_SYMBOL
        for (x, y), _ in self.campfires.items():
            if (x, y) in self.revealed and not self.is_player_at(x, y):
                board[y][x] = CAMPFIRE_SYMBOL
        for x, y in self.supplies_positions:
            if (x, y) in self.revealed and not self.is_player_at(x, y):
                board[y][x] = "R"
        for x, y in self.medkit_positions:
            if (x, y) in self.revealed and not self.is_player_at(x, y):
                board[y][x] = MEDKIT_SYMBOL
        for x, y in self.weapon_positions:
            if (x, y) in self.revealed and not self.is_player_at(x, y):
                board[y][x] = WEAPON_SYMBOL
        for x, y in self.molotov_positions:
            if (x, y) in self.revealed and not self.is_player_at(x, y):
                board[y][x] = MOLOTOV_SYMBOL
        for x, y in self.flashlight_positions:
            if (x, y) in self.revealed and not self.is_player_at(x, y):
                board[y][x] = FLASHLIGHT_SYMBOL
        for x, y in self.trap_positions:
            if (x, y) in self.revealed and not self.is_player_at(x, y):
                board[y][x] = TRAP_SYMBOL
        for x, y, _, turns in self.noise_markers:
            if (x, y) in self.revealed and not self.is_player_at(x, y):
                board[y][x] = str(turns)
        for z in self.zombies:
            if (z.x, z.y) in self.revealed:
                board[z.y][z.x] = z.symbol

        print(
            "Health: {}    Hunger: {}/{}    Medkits: {}    Supplies: {}    Molotovs: {}    Inventory: {}/{}    Tokens: {}    Weapon: {}    Flashlight: {}    Infection: {}    Level: {}    XP: {}".format(
                self.player.health,
                self.player.hunger,
                self.player.max_hunger,
                self.player.medkits,
                self.player.supplies,
                self.player.molotovs,
                self.player.inventory_size,
                INVENTORY_LIMIT,
                self.double_move_tokens,
                "Y" if self.player.has_weapon else "N",
                "Y" if self.player.has_flashlight else "N",
                self.player.infection_turns if self.player.infection_turns > 0 else "-",
                self.level,
                self.campaign.get("xp", 0) + self.xp_gained,
            )
        )
        phase = "Night" if self.is_night else "Day"
        print(f"Turn {self.turn} - {phase} ({self.phase_turns} turns remaining)")
        header = "   " + " ".join(str(i) for i in range(self.board_size))
        print(header)
        for idx, row in enumerate(board):
            print(f"{idx:2d} " + " ".join(row))

    def show_help(self) -> None:
        """Display available controls and board legend."""
        print(
            "Controls:\n"
            "  W/A/S/D - move\n"
            "  F - attack adjacent zombie\n"
            "  G - scavenge current tile\n"
            "  H - use a medkit\n"
            "  V - use an antidote\n"
            "  E - eat supplies\n"
            "  B - build a barricade\n"
            "  U - disarm a trap\n"
            "  O - scout without moving\n"
            "  C - craft items\n"
            "  M - throw a molotov\n"
            "  R - steal from another player\n"
            "  K - attack another player\n"
            "  X - trade with another player\n"
            "  T - drop an item\n"
            "  Z - rest\n"
            "  P - pass\n"
            "  Q - save and quit\n"
            "  ? - show this help\n"
        )
        print(
            "Legend:\n"
            "  S start    . explored    ? unexplored\n"
            "  1-6 players    Z zombie    R supply    H medkit\n"
            "  G weapon    L molotov    I flashlight    B barricade\n"
            f"  {CAMPFIRE_SYMBOL} campfire (light)    {SHELTER_SYMBOL} shelter (rest bonus)    ! trap    A antidote    K keys    F fuel\n"
            f"  P radio part    T radio tower    numbers noise timers    {WALL_SYMBOL} wall"
        )

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
            if (
                0 <= nx < self.board_size
                and 0 <= ny < self.board_size
                and (nx, ny) not in self.wall_positions
            ):
                self.player.x, self.player.y = nx, ny
                self.reveal_area(nx, ny, player=self.player)
                self.check_for_trap(nx, ny)
            else:
                self.player.x, self.player.y = original
                self.reveal_area(*original, player=self.player)
                if (nx, ny) in self.wall_positions:
                    print("A wall blocks your path.")
                return False
        return True

    def check_for_trap(self, x: int, y: int) -> None:
        """Trigger a trap if the active player steps on one."""
        if (x, y) in self.trap_positions:
            self.trap_positions.remove((x, y))
            self.player.health -= TRAP_DAMAGE
            print(f"You trigger a trap! -{TRAP_DAMAGE} health")

    def attack(self) -> bool:
        # Find adjacent zombie (4-directional)
        for z in list(self.zombies):
            if abs(z.x - self.player.x) + abs(z.y - self.player.y) == 1:
                hit_chance = (
                    WEAPON_HIT_CHANCE if self.player.has_weapon else ATTACK_HIT_CHANCE
                )
                if self.player.role == "fighter":
                    hit_chance = min(1.0, hit_chance + 0.1)
                if roll_check(hit_chance, label="Attack"):
                    self.zombies.remove(z)
                    self.zombies_killed += 1
                    self.player.kills += 1
                    self.xp_gained += XP_PER_ZOMBIE
                    print("You slay a zombie!")
                else:
                    self.player.health -= 1
                    print("Your attack misses! You take 1 damage.")
                if self.player.has_weapon:
                    self.add_noise(
                        self.player.x, self.player.y, WEAPON_NOISE_ZOMBIE_CHANCE
                    )
                    print("The gunshot echoes...")
                return True
        return False

    def attack_player(self) -> bool:
        """Attempt to injure another survivor on the same tile.

        Fighting other players is risky and attracts the dead. A successful
        attack deals 1 damage to the target. On a miss the attacker takes
        the damage instead. Either way the scuffle leaves behind a noise
        marker that may spawn zombies later.
        """
        others = [
            p
            for p in self.players
            if p is not self.player and p.health > 0 and (p.x, p.y) == (self.player.x, self.player.y)
        ]
        if not others:
            return False
        target = random.choice(others)
        if roll_check(PVP_ATTACK_HIT_CHANCE, label="Skirmish"):
            target.health -= 1
            print(f"You strike player {target.symbol}! -1 HP")
            if target.health <= 0:
                self.handle_player_death(target)
        else:
            self.player.health -= 1
            print("The fight backfires! You take 1 damage.")
            if self.player.health <= 0:
                self.handle_player_death(self.player)
        self.add_noise(self.player.x, self.player.y, PVP_ATTACK_NOISE_CHANCE)
        print("The commotion may draw more zombies...")
        return True

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
                if roll_check(PHARMACY_MEDKIT_CHANCE, label="Pharmacy"):
                    self.player.medkits += 1
                    found = True
                    print("You raid the pharmacy and find a medkit!")
                if roll_check(SCAVENGE_FIND_CHANCE, label="Pharmacy"):
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
            if not self.player.has_weapon and roll_check(ARMORY_WEAPON_CHANCE, label="Armory"):
                self.player.has_weapon = True
                found = True
                print("You find a weapon in the armory!")
            if self.player.inventory_size < INVENTORY_LIMIT:
                if roll_check(ARMORY_SUPPLY_CHANCE, label="Armory"):
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
                    self.rescue_timer = self.evacuation_turns
                    print("You radio for rescue! Hold out!")
                else:
                    print("You need a radio to signal for help.")
                return
            if self.radio_tower_pos and pos == self.radio_tower_pos:
                self.called_rescue = True
                self.rescue_timer = self.evacuation_turns
                print("You activate the tower and call for rescue! Hold out!")
                return

        if pos in self.weapon_positions:
            if not self.player.has_weapon:
                self.weapon_positions.remove(pos)
                self.player.has_weapon = True
                print("You pick up a weapon.")
            else:
                print("You already have a weapon.")
            return

        if pos in self.molotov_positions:
            if self.player.inventory_size < INVENTORY_LIMIT:
                self.molotov_positions.remove(pos)
                self.player.molotovs += 1
                print("You pick up a molotov cocktail.")
            else:
                print("Your pack is full. You leave the molotov behind.")
            return

        if pos in self.flashlight_positions:
            if not self.player.has_flashlight:
                self.flashlight_positions.remove(pos)
                self.player.has_flashlight = True
                print("You pick up a flashlight.")
            else:
                print("You already have a flashlight.")
            return

        if pos in self.medkit_positions:
            if self.player.inventory_size < INVENTORY_LIMIT:
                self.medkit_positions.remove(pos)
                self.player.medkits += 1
                print("You pick up a medkit.")
            else:
                print("Your pack is full. You leave the medkit behind.")
            return

        if pos in self.supplies_positions:
            if self.player.inventory_size < INVENTORY_LIMIT:
                self.supplies_positions.remove(pos)
                self.player.supplies += 1
                print("You pick up a supply.")
            else:
                print("Your pack is full. You leave the supply behind.")
            return

        if not self.loot_deck:
            self.loot_deck = create_loot_deck()
        card = self.loot_deck.popleft()
        if self.player.role == "scout" and card == "nothing" and self.loot_deck:
            card = self.loot_deck.popleft()
        if card == "weapon":
            if not self.player.has_weapon:
                self.player.has_weapon = True
                print("You find a weapon!")
            else:
                print("You find a weapon but already have one.")
        elif card == "supply":
            if self.player.inventory_size < INVENTORY_LIMIT:
                self.player.supplies += 1
                print("You find a supply!")
            else:
                print("You find a supply but your pack is full.")
        elif card == "medkit":
            if self.player.inventory_size < INVENTORY_LIMIT:
                self.player.medkits += 1
                print("You find a medkit!")
            else:
                print("You find a medkit but your pack is full.")
        elif card == "flashlight":
            if not self.player.has_flashlight:
                self.player.has_flashlight = True
                print("You find a flashlight!")
            else:
                print("You find a flashlight but already have one.")
        else:
            print("You find nothing of use.")

    def use_medkit(self) -> bool:
        if self.player.medkits > 0 and self.player.health < self.player.max_health:
            self.player.medkits -= 1
            heal = MEDKIT_HEAL + (1 if self.player.role == "medic" else 0)
            self.player.health = min(self.player.max_health, self.player.health + heal)
            print(f"You use a medkit and recover {heal} health.")
            return True
        return False

    def use_antidote(self) -> bool:
        """Cure infection using the carried antidote."""
        if not self.player.has_antidote:
            print("You don't have an antidote.")
            return False
        if self.player.infection_turns <= 0:
            print("You aren't infected.")
            return False
        self.player.has_antidote = False
        self.player.infection_turns = 0
        print("You inject the antidote and purge the infection.")
        return True

    def eat_food(self) -> bool:
        if self.player.supplies > 0 and self.player.hunger < self.player.max_hunger:
            self.player.supplies -= 1
            self.player.hunger = min(
                self.player.max_hunger, self.player.hunger + HUNGER_EAT_AMOUNT
            )
            print("You eat some supplies and feel less hungry.")
            return True
        return False

    def rest(self) -> bool:
        """Spend an action to recover hunger or a bit of health."""
        pos = (self.player.x, self.player.y)
        bonus = 0
        if pos in self.shelter_positions:
            bonus += 1
        if pos in self.campfires:
            bonus += 1
        if self.player.hunger < self.player.max_hunger:
            gain = 1 + bonus
            self.player.hunger = min(self.player.max_hunger, self.player.hunger + gain)
            if bonus:
                if pos in self.shelter_positions and pos in self.campfires:
                    print("The shelter and fire bolster you as you regain stamina.")
                elif pos in self.shelter_positions:
                    print("The shelter lets you recover extra stamina.")
                else:
                    print("The campfire warms you as you regain stamina.")
            else:
                print("You catch your breath and regain some stamina.")
            return True
        if self.player.health < self.player.max_health:
            heal = (2 if self.player.role == "medic" else 1) + bonus
            self.player.health = min(self.player.max_health, self.player.health + heal)
            if bonus:
                if pos in self.shelter_positions and pos in self.campfires:
                    print(f"You rest in a lit shelter and heal {heal} health.")
                elif pos in self.shelter_positions:
                    print(f"You rest safely and heal {heal} health.")
                else:
                    print(f"You rest by the fire and heal {heal} health.")
            else:
                print(f"You take a moment to rest and heal {heal} health.")
            return True
        print("You feel fully rested already.")
        return False

    def build_barricade(self) -> bool:
        pos = (self.player.x, self.player.y)
        if pos in self.barricade_positions:
            print("There's already a barricade here.")
            return False
        cost = max(1, BARRICADE_SUPPLY_COST - (1 if self.player.role == "engineer" else 0))
        if self.player.supplies >= cost:
            self.player.supplies -= cost
            self.barricade_positions.add(pos)
            print("You hastily build a barricade.")
            return True
        print("Not enough supplies to build a barricade.")
        return False

    def disarm_trap(self) -> bool:
        """Remove a trap on the current tile, salvaging a supply."""
        pos = (self.player.x, self.player.y)
        if pos in self.trap_positions:
            self.trap_positions.remove(pos)
            self.player.supplies += 1
            print("You carefully disarm the trap and salvage a supply.")
            return True
        print("No trap here to disarm.")
        return False

    def scout(self) -> bool:
        """Reveal tiles in an adjacent direction without moving."""
        direction = input("Scout direction [w/a/s/d]: ").strip().lower()
        offsets = {"w": (-1, 0), "a": (0, -1), "s": (1, 0), "d": (0, 1)}
        if direction not in offsets:
            print("Invalid direction.")
            return False
        dx, dy = offsets[direction]
        nx, ny = self.player.x + dx, self.player.y + dy
        if not (0 <= nx < self.board_size and 0 <= ny < self.board_size):
            print("You can't scout past the edge of the board.")
            return False
        self.reveal_area(nx, ny, radius=SCOUT_RADIUS, player=self.player)
        print("You scout ahead, revealing more of the surroundings.")
        return True

    def craft_item(self) -> bool:
        """Craft a medkit, molotov or trap using supplies (and fuel)."""
        cost_medkit = MEDKIT_CRAFT_COST
        cost_trap = max(1, TRAP_CRAFT_COST - (1 if self.player.role == "engineer" else 0))
        cost_flash = max(1, FLASHLIGHT_CRAFT_COST - (1 if self.player.role == "engineer" else 0))
        cost_camp = max(1, CAMPFIRE_CRAFT_COST - (1 if self.player.role == "engineer" else 0))
        choice = input(
            "Craft [m]edkit (cost {0} supplies), [l]molotov (cost {1} supply + fuel), [t]rap (cost {2} supplies), [f]lashlight (cost {3} supplies) or [c]ampfire (cost {4} supplies): ".format(
                cost_medkit,
                MOLOTOV_SUPPLY_COST,
                cost_trap,
                cost_flash,
                cost_camp,
            )
        ).strip().lower()
        if choice == "m":
            if self.player.supplies >= cost_medkit:
                if self.player.inventory_size < INVENTORY_LIMIT:
                    self.player.supplies -= cost_medkit
                    self.player.medkits += 1
                    print("You craft a makeshift medkit.")
                    return True
                print("Your pack is full.")
            else:
                print("Not enough supplies to craft a medkit.")
        elif choice == "l":
            if (
                self.player.supplies >= MOLOTOV_SUPPLY_COST
                and self.player.has_fuel
                and self.player.inventory_size < INVENTORY_LIMIT
            ):
                self.player.supplies -= MOLOTOV_SUPPLY_COST
                self.player.has_fuel = False
                self.player.molotovs += 1
                print("You assemble a molotov cocktail.")
                return True
            print("You lack the materials to craft a molotov.")
        elif choice == "t":
            pos = (self.player.x, self.player.y)
            if self.player.supplies >= cost_trap:
                if pos in self.trap_positions:
                    print("There's already a trap here.")
                else:
                    self.player.supplies -= cost_trap
                    self.trap_positions.add(pos)
                    print("You rig a crude trap.")
                    return True
            else:
                print("Not enough supplies to craft a trap.")
        elif choice == "f":
            if self.player.has_flashlight:
                print("You already have a flashlight.")
            elif self.player.supplies >= cost_flash:
                self.player.supplies -= cost_flash
                self.player.has_flashlight = True
                print("You craft a simple flashlight.")
                return True
            else:
                print("Not enough supplies to craft a flashlight.")
        elif choice == "c":
            if self.player.supplies >= cost_camp:
                pos = (self.player.x, self.player.y)
                if pos in self.campfires:
                    print("There's already a campfire here.")
                else:
                    self.player.supplies -= cost_camp
                    self.campfires[pos] = CAMPFIRE_DURATION
                    print("You build a campfire to rest by. Its light reveals nearby tiles.")
                    return True
            else:
                print("Not enough supplies to build a campfire.")
        return False

    def throw_molotov(self) -> bool:
        """Throw a molotov, burning adjacent zombies."""
        if self.player.molotovs <= 0:
            return False
        self.player.molotovs -= 1
        removed = 0
        for z in list(self.zombies):
            if abs(z.x - self.player.x) <= 1 and abs(z.y - self.player.y) <= 1:
                self.zombies.remove(z)
                removed += 1
        if removed:
            self.zombies_killed += removed
            self.player.kills += removed
            self.xp_gained += XP_PER_ZOMBIE * removed
            print(f"The molotov explodes, burning {removed} zombie{'s' if removed != 1 else ''}!")
        else:
            print("The molotov explodes harmlessly.")
        self.add_noise(self.player.x, self.player.y, MOLOTOV_NOISE_ZOMBIE_CHANCE)
        print("The fiery blast draws more undead!")
        return True

    def drop_item(self) -> bool:
        pos = (self.player.x, self.player.y)
        choice = input(
            "Drop item [s]upply, [m]edkit, [w]eapon, [k]eys, [f]uel, [a]ntidote, [l]molotov, [i]flashlight: "
        ).strip().lower()
        if choice == "s" and self.player.supplies > 0:
            self.player.supplies -= 1
            self.supplies_positions.add(pos)
            print("You drop a supply.")
            return True
        if choice == "m" and self.player.medkits > 0:
            self.player.medkits -= 1
            self.medkit_positions.add(pos)
            print("You drop a medkit.")
            return True
        if choice == "w" and self.player.has_weapon:
            self.player.has_weapon = False
            self.weapon_positions.add(pos)
            print("You drop your weapon.")
            return True
        if choice == "k" and self.player.has_keys:
            self.player.has_keys = False
            self.keys_pos = pos
            print("You drop the keys.")
            return True
        if choice == "f" and self.player.has_fuel:
            self.player.has_fuel = False
            self.fuel_pos = pos
            print("You drop the fuel.")
            return True
        if choice == "a" and self.player.has_antidote:
            self.player.has_antidote = False
            self.antidote_pos = pos
            print("You drop the antidote.")
            return True
        if choice == "l" and self.player.molotovs > 0:
            self.player.molotovs -= 1
            self.molotov_positions.add(pos)
            print("You drop a molotov.")
            return True
        if choice == "i" and self.player.has_flashlight:
            self.player.has_flashlight = False
            self.flashlight_positions.add(pos)
            print("You drop the flashlight.")
            return True
        print("Nothing dropped.")
        return False

    def trade_item(self) -> bool:
        """Trade an item with another player on the same tile."""
        others = [
            p
            for p in self.players
            if p is not self.player and p.x == self.player.x and p.y == self.player.y
        ]
        if not others:
            print("No other players here to trade with.")
            return False
        print("Players here: " + ", ".join(p.symbol for p in others))
        choice = input("Trade with which player? ").strip()
        target = next((p for p in others if p.symbol == choice), None)
        if not target:
            print("Trade cancelled.")
            return False
        options = []
        if self.player.supplies > 0:
            options.append("supply")
        if self.player.medkits > 0:
            options.append("medkit")
        if self.player.molotovs > 0:
            options.append("molotov")
        if self.player.has_weapon:
            options.append("weapon")
        if self.player.has_keys:
            options.append("keys")
        if self.player.has_fuel:
            options.append("fuel")
        if self.player.has_antidote:
            options.append("antidote")
        if self.player.has_flashlight:
            options.append("flashlight")
        if not options:
            print("You have nothing to trade.")
            return False
        item = input("Trade which item {}: ".format("/".join(options))).strip().lower()
        if item not in options:
            print("Trade cancelled.")
            return False
        if item in {"supply", "medkit", "molotov"} and target.inventory_size >= INVENTORY_LIMIT:
            print(f"Player {target.symbol}'s pack is full.")
            return False
        if item == "supply":
            self.player.supplies -= 1
            target.supplies += 1
        elif item == "medkit":
            self.player.medkits -= 1
            target.medkits += 1
        elif item == "molotov":
            self.player.molotovs -= 1
            target.molotovs += 1
        elif item == "weapon":
            if target.has_weapon:
                print(f"Player {target.symbol} already has a weapon.")
                return False
            self.player.has_weapon = False
            target.has_weapon = True
        elif item == "keys":
            if target.has_keys:
                print(f"Player {target.symbol} already has keys.")
                return False
            self.player.has_keys = False
            target.has_keys = True
        elif item == "fuel":
            if target.has_fuel:
                print(f"Player {target.symbol} already has fuel.")
                return False
            self.player.has_fuel = False
            target.has_fuel = True
        elif item == "antidote":
            if target.has_antidote:
                print(f"Player {target.symbol} already has the antidote.")
                return False
            self.player.has_antidote = False
            target.has_antidote = True
        elif item == "flashlight":
            if target.has_flashlight:
                print(f"Player {target.symbol} already has a flashlight.")
                return False
            self.player.has_flashlight = False
            target.has_flashlight = True
        print(f"You trade a {item} to player {target.symbol}.")
        return True

    def steal_item(self) -> bool:
        """Attempt to steal an item from another player on the same tile."""
        # find other players on same position
        others = [p for p in self.players if p is not self.player and p.x == self.player.x and p.y == self.player.y]
        if not others:
            return False
        target = random.choice(others)
        stealable = []
        if target.supplies > 0 and self.player.inventory_size < INVENTORY_LIMIT:
            stealable.append("supply")
        if target.medkits > 0 and self.player.inventory_size < INVENTORY_LIMIT:
            stealable.append("medkit")
        if target.molotovs > 0 and self.player.inventory_size < INVENTORY_LIMIT:
            stealable.append("molotov")
        if target.has_weapon and not self.player.has_weapon:
            stealable.append("weapon")
        if target.has_keys:
            stealable.append("keys")
        if target.has_fuel:
            stealable.append("fuel")
        if target.has_antidote:
            stealable.append("antidote")
        if target.has_flashlight and not self.player.has_flashlight:
            stealable.append("flashlight")
        if not stealable:
            print(f"Player {target.symbol} has nothing you can take.")
            return False
        if roll_check(STEAL_SUCCESS_CHANCE, label="Steal"):
            item = random.choice(stealable)
            if item == "supply":
                target.supplies -= 1
                self.player.supplies += 1
            elif item == "medkit":
                target.medkits -= 1
                self.player.medkits += 1
            elif item == "molotov":
                target.molotovs -= 1
                self.player.molotovs += 1
            elif item == "weapon":
                target.has_weapon = False
                self.player.has_weapon = True
            elif item == "keys":
                target.has_keys = False
                self.player.has_keys = True
            elif item == "fuel":
                target.has_fuel = False
                self.player.has_fuel = True
            elif item == "antidote":
                target.has_antidote = False
                self.player.has_antidote = True
            elif item == "flashlight":
                target.has_flashlight = False
                self.player.has_flashlight = True
            print(f"You steal a {item} from player {target.symbol}!")
        else:
            self.player.health -= 1
            print(f"Player {target.symbol} fends you off! You take 1 damage.")
        return True

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
            if (nx, ny) in self.trap_positions:
                self.trap_positions.remove((nx, ny))
                self.zombies.remove(z)
                self.zombies_killed += 1
                print("A zombie stumbles into a trap and is destroyed!")
                continue
            if (nx, ny) in self.wall_positions:
                continue
            if not any((other.x, other.y) == (nx, ny) for other in self.zombies):
                z.x, z.y = nx, ny
            for p in self.players:
                if z.x == p.x and z.y == p.y:
                    p.health -= 1
                    print(f"Player {p.symbol} is bitten! -1 health")
                    if p.health > 0 and p.infection_turns == 0 and random.random() < INFECTION_CHANCE:
                        p.infection_turns = INFECTION_TURNS
                        print(f"Player {p.symbol} is infected!")

    def spawn_random_zombie(self) -> None:
        if random.random() < self.zombie_spawn_chance:
            self.spawn_zombies(1)
            print("A zombie shambles in from the darkness...")

    def spawn_zombie_near(self, x: int, y: int, chance: float) -> bool:
        """Spawn a zombie adjacent to (x, y) with the given chance.

        Returns True if a zombie was spawned.
        """
        if random.random() < chance:
            candidates = [
                (nx, ny)
                for nx in range(x - 1, x + 2)
                for ny in range(y - 1, y + 2)
                if 0 <= nx < self.board_size
                and 0 <= ny < self.board_size
                and (nx, ny) != (x, y)
                and (nx, ny) not in self.barricade_positions
                and (nx, ny) not in self.wall_positions
                and (nx, ny) not in self.molotov_positions
                and (nx, ny) not in self.trap_positions
                and (nx, ny) not in self.campfires
                and (nx, ny) not in self.shelter_positions
                and all((z.x, z.y) != (nx, ny) for z in self.zombies)
                and not self.is_player_at(nx, ny)
            ]
            if candidates:
                zx, zy = random.choice(candidates)
                self.zombies.append(Zombie(zx, zy))
                if (zx, zy) in self.revealed:
                    print("Noise draws a zombie nearby!")
                return True
        return False

    def find_free_tile_near(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """Return a random free tile adjacent to (x, y) or None if blocked."""
        candidates = [
            (nx, ny)
            for nx in range(x - 1, x + 2)
            for ny in range(y - 1, y + 2)
            if 0 <= nx < self.board_size
            and 0 <= ny < self.board_size
            and (nx, ny) != (x, y)
            and not self.is_player_at(nx, ny)
            and (nx, ny) not in self.barricade_positions
            and (nx, ny) not in self.supplies_positions
            and (nx, ny) not in self.medkit_positions
            and (nx, ny) not in self.weapon_positions
            and (nx, ny) not in self.molotov_positions
            and (nx, ny) not in self.trap_positions
            and (nx, ny) not in self.wall_positions
            and all((z.x, z.y) != (nx, ny) for z in self.zombies)
        ]
        return random.choice(candidates) if candidates else None

    def add_noise(self, x: int, y: int, chance: float) -> None:
        """Record a noisy action that may attract zombies later."""
        self.noise_markers.append((x, y, chance, NOISE_DURATION))

    def resolve_noise(self) -> None:
        """Spawn zombies for all accumulated noise markers."""
        remaining: List[Tuple[int, int, float, int]] = []
        for x, y, chance, turns in self.noise_markers:
            effective = chance
            if self.noise_dampener_turns > 0:
                effective *= RAIN_NOISE_MULTIPLIER
            spawned = self.spawn_zombie_near(x, y, effective)
            if not spawned and turns > 1:
                remaining.append((x, y, chance, turns - 1))
        self.noise_markers = remaining
        if self.noise_dampener_turns > 0:
            self.noise_dampener_turns -= 1
        if self.visibility_penalty_turns > 0:
            self.visibility_penalty_turns -= 1
    def update_campfires(self) -> None:
        """Reduce campfire timers, reveal their light and remove expired fires."""
        expired: List[Tuple[int, int]] = []
        for (x, y), turns in list(self.campfires.items()):
            # Campfires act as light sources, revealing nearby tiles.
            self.reveal_area(x, y, CAMPFIRE_LIGHT_RADIUS)
            if turns > 1:
                self.campfires[(x, y)] = turns - 1
            else:
                expired.append((x, y))
        for pos in expired:
            del self.campfires[pos]
            if pos in self.revealed:
                print("A campfire burns out.")

    def random_event(self) -> None:
        """Trigger an end-of-round event by drawing from the event deck."""
        if not self.event_deck:
            self.event_deck = create_event_deck()
        event = self.event_deck.popleft()
        if event == "nothing":
            print("The night is quiet...")
        elif event == "heal":
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
            joined = False
            if len(self.players) < MAX_PLAYERS:
                spot = self.find_free_tile_near(*self.start_pos)
                if spot is None and not self.is_player_at(*self.start_pos):
                    spot = self.start_pos
                if spot is not None:
                    used = {p.symbol for p in self.players}
                    symbol = next(
                        str(i) for i in range(1, MAX_PLAYERS + 1) if str(i) not in used
                    )
                    new_p = Player(
                        spot[0],
                        spot[1],
                        self.players[0].max_health,
                        symbol,
                        is_ai=True,
                    )
                    self.players.append(new_p)
                    self.reveal_area(new_p.x, new_p.y, player=new_p)
                    self.zombie_spawn_chance += 0.05
                    self.base_zombie_spawn_chance += 0.05
                    print(f"A grateful survivor joins as player {symbol}!")
                    joined = True
            if not joined:
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
        elif event == "rain":
            self.noise_dampener_turns = 1
            print(
                "Steady rain falls. Noise will attract fewer zombies next round."
            )
        elif event == "fog":
            self.reveal_random_tiles(5)
            print("A gust of wind lifts the fog, revealing more of the area.")
        elif event == "heatwave":
            self.hunger_penalty_turns = 1
            print("A brutal heatwave scorches the area. Hunger will drop faster next round.")
        elif event == "blizzard":
            self.actions_per_turn = max(1, ACTIONS_PER_TURN - 1)
            self.noise_dampener_turns = max(self.noise_dampener_turns, 1)
            self.visibility_penalty_turns = 1
            print(
                "A blizzard howls! Next round you have one fewer action and reduced visibility."
            )
        elif event == "earthquake":
            self.quake_walls()
            print("The ground rumbles, shifting rubble around you!")
        elif event == "firebomb":
            given = False
            for p in self.players:
                if p.inventory_size < INVENTORY_LIMIT:
                    p.molotovs += 1
                    print(f"Player {p.symbol} discovers a hidden molotov cache!")
                    given = True
                    break
            if not given:
                print("You find a firebomb cache but can't carry any.")
        elif event == "trader":
            bought = False
            for p in self.players:
                if p.supplies >= 2 and p.inventory_size < INVENTORY_LIMIT:
                    if p.is_ai:
                        if p.medkits == 0:
                            p.supplies -= 2
                            p.medkits += 1
                            print(
                                f"Player {p.symbol} buys a medkit from a wandering trader."
                            )
                            bought = True
                    else:
                        choice = (
                            input(
                                f"Player {p.symbol}: buy a medkit for 2 supplies? [y/N]: "
                            )
                            .strip()
                            .lower()
                        )
                        if choice == "y":
                            p.supplies -= 2
                            p.medkits += 1
                            print(
                                f"Player {p.symbol} buys a medkit from the trader."
                            )
                            bought = True
            if not bought:
                print("The wandering trader finds no buyers and moves on.")

    def handle_player_death(self, player: Player) -> None:
        """Remove a dead player and spawn a zombie at their location."""
        print(f"Player {player.symbol} has fallen to the zombies...")
        if player in self.players:
            self.players.remove(player)
        if not any(z.x == player.x and z.y == player.y for z in self.zombies):
            self.zombies.append(Zombie(player.x, player.y))
            if (player.x, player.y) in self.revealed:
                print("Their corpse rises again as a zombie!")

    def apply_hunger(self) -> None:
        decay = HUNGER_DECAY + (1 if self.hunger_penalty_turns > 0 else 0)
        for p in list(self.players):
            p.hunger = max(0, p.hunger - decay)
            if p.hunger == 0:
                p.health -= HUNGER_STARVE_DAMAGE
                print(f"Player {p.symbol} is starving! -1 health")
            if p.infection_turns > 0:
                p.infection_turns -= 1
                if p.infection_turns == 0:
                    print(f"Player {p.symbol} succumbs to infection!")
                    self.handle_player_death(p)
                    continue
            if p.health <= 0:
                self.handle_player_death(p)
        if self.hunger_penalty_turns > 0:
            self.hunger_penalty_turns -= 1

    def process_evacuation(self) -> List[Player]:
        """Determine which survivors escape when rescue arrives."""
        survivors = [p for p in self.players if p.health > 0]
        at_start = [p for p in survivors if (p.x, p.y) == self.start_pos]
        if not at_start:
            print("No survivors are at the evacuation point when rescue arrives!")
            return []
        if self.cooperative:
            if len(at_start) == len(survivors) and len(at_start) <= self.evacuation_capacity:
                for p in at_start:
                    print(f"Player {p.symbol} boards the rescue craft.")
                return at_start
            if len(at_start) < len(survivors):
                print("Some survivors fail to reach the extraction zone in time!")
            else:
                print("There aren't enough seats for everyone. Some are left behind!")
            return []
        at_start.sort(key=lambda p: p.kills, reverse=True)
        evacuated = at_start[: self.evacuation_capacity]
        for p in evacuated:
            print(f"Player {p.symbol} boards the rescue craft.")
        for p in at_start[self.evacuation_capacity :]:
            print(f"Player {p.symbol} is left behind as the craft departs!")
        return evacuated

    def print_summary(self) -> None:
        """Display a scoreboard of each player's outcome and inventory."""
        print("\nFinal results:")
        print(f"{'P':<3}{'Status':<10}{'Kills':>7}{'Supplies':>10}{'Medkits':>10}")
        for p in self.all_players:
            if p in self.evacuated_players:
                status = "escaped"
            elif p in self.players and p.health > 0:
                status = "alive"
            else:
                status = "dead"
            print(
                f"{p.symbol:<3}{status:<10}{p.kills:>7}{p.supplies:>10}{p.medkits:>10}"
            )

    def advance_time_of_day(self) -> None:
        """Advance the day/night cycle and update related modifiers."""
        self.phase_turns -= 1
        if self.phase_turns <= 0:
            self.is_night = not self.is_night
            self.phase_turns = NIGHT_LENGTH if self.is_night else DAY_LENGTH
            if self.is_night:
                self.reveal_radius = max(0, REVEAL_RADIUS - NIGHT_REVEAL_PENALTY)
                self.zombie_spawn_chance = (
                    self.base_zombie_spawn_chance * NIGHT_SPAWN_MULTIPLIER
                )
                print("Night falls. Zombies grow bolder and visibility shrinks.")
            else:
                self.reveal_radius = REVEAL_RADIUS
                self.zombie_spawn_chance = self.base_zombie_spawn_chance
                print("Dawn breaks. You can see further again.")

    def determine_turn_order(self) -> None:
        """Roll for initiative and order players each round.

        Each survivor rolls a d6 at the start of the round. Highest roll
        goes first, providing a tabletop-inspired turn order that can
        change from round to round.
        """
        rolls = [(p, random.randint(1, 6)) for p in self.players]
        rolls.sort(key=lambda pr: pr[1], reverse=True)
        self.players = [p for p, _ in rolls]
        order = ", ".join(f"{p.symbol}({r})" for p, r in rolls)
        print(f"Initiative order: {order}")

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

    def find_step_towards(
        self, start: Tuple[int, int], goals: Set[Tuple[int, int]]
    ) -> Optional[str]:
        """Return a direction that steps from start toward the nearest goal."""
        if not goals:
            return None
        queue: deque[Tuple[Tuple[int, int], List[Tuple[int, int]]]] = deque()
        queue.append((start, []))
        visited = {start}
        while queue:
            (x, y), path = queue.popleft()
            if (x, y) in goals:
                if not path:
                    return None
                nx, ny = path[0]
                if nx > start[0]:
                    return "d"
                if nx < start[0]:
                    return "a"
                if ny > start[1]:
                    return "s"
                if ny < start[1]:
                    return "w"
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if (
                    0 <= nx < self.board_size
                    and 0 <= ny < self.board_size
                    and (nx, ny) not in visited
                    and (nx, ny) not in self.barricade_positions
                    and (nx, ny) not in self.wall_positions
                    and (nx, ny) not in self.trap_positions
                    and all((z.x, z.y) != (nx, ny) for z in self.zombies)
                ):
                    visited.add((nx, ny))
                    queue.append(((nx, ny), path + [(nx, ny)]))
        return None

    # ------------------------------------------------------------------
    # Turn handling and game state
    def ai_turn(self, player: Player) -> None:
        """Execute a simple turn for an AI-controlled player."""
        actions_left = self.actions_per_turn
        while actions_left > 0 and player.health > 0:
            self.draw_board()
            if player.infection_turns > 0 and player.has_antidote:
                print(f"Player {player.symbol} uses an antidote.")
                self.use_antidote()
                actions_left -= 1
                continue
            # Heal if badly hurt
            if player.health <= player.max_health // 2 and player.medkits > 0:
                print(f"Player {player.symbol} uses a medkit.")
                self.use_medkit()
                actions_left -= 1
                continue
            if (player.x, player.y) in self.trap_positions:
                print(f"Player {player.symbol} disarms a trap.")
                self.disarm_trap()
                actions_left -= 1
                continue
            # Eat if starving
            if player.hunger <= player.max_hunger // 2 and player.supplies > 0:
                print(f"Player {player.symbol} eats a supply.")
                self.eat_food()
                actions_left -= 1
                continue
            # Rest if hurt or hungry with no supplies
            if player.medkits == 0 and player.health < player.max_health:
                print(f"Player {player.symbol} rests to recover.")
                self.rest()
                actions_left -= 1
                continue
            if player.supplies == 0 and player.hunger < player.max_hunger:
                print(f"Player {player.symbol} rests to regain hunger.")
                self.rest()
                actions_left -= 1
                continue
            # Attack if a zombie is adjacent
            if any(
                abs(z.x - player.x) + abs(z.y - player.y) == 1 for z in self.zombies
            ):
                if self.attack():
                    actions_left -= 1
                    continue

            # Always interact with scenario objectives even if packs are full.
            pos = (player.x, player.y)
            objective_here = False
            if self.scenario == 1 and not player.has_antidote and pos == self.antidote_pos:
                objective_here = True
            elif self.scenario == 2 and (
                (not player.has_keys and pos == self.keys_pos)
                or (not player.has_fuel and pos == self.fuel_pos)
            ):
                objective_here = True
            elif self.scenario == 3 and pos in self.radio_positions:
                objective_here = True
            elif (
                self.scenario == 4
                and not self.called_rescue
                and (pos == self.start_pos or pos == self.radio_tower_pos)
            ):
                # Calling for rescue uses the scavenge action.
                objective_here = True

            if objective_here:
                self.scavenge()
                actions_left -= 1
                continue

            # Scavenge regular tiles only if there's room to carry loot.
            if player.inventory_size < INVENTORY_LIMIT:
                self.scavenge()
                actions_left -= 1
                continue

            targets: Set[Tuple[int, int]] = set()
            heading_home = False
            if self.scenario == 1:
                if not player.has_antidote and self.antidote_pos:
                    targets.add(self.antidote_pos)
                else:
                    targets.add(self.start_pos)
                    heading_home = True
            elif self.scenario == 2:
                if not player.has_keys and self.keys_pos:
                    targets.add(self.keys_pos)
                elif not player.has_fuel and self.fuel_pos:
                    targets.add(self.fuel_pos)
                else:
                    targets.add(self.start_pos)
                    heading_home = True
            elif self.scenario == 3:
                if self.radio_parts_collected < RADIO_PARTS_REQUIRED:
                    targets.update(self.radio_positions)
                else:
                    targets.add(self.start_pos)
                    heading_home = True
            elif self.scenario == 4:
                if not self.called_rescue:
                    if self.has_signal_device:
                        targets.add(self.start_pos)
                    if self.radio_tower_pos:
                        targets.add(self.radio_tower_pos)
                else:
                    targets.add(self.start_pos)
                    heading_home = True

            if not heading_home:
                targets.update(self.supplies_positions)
                targets.update(self.flashlight_positions)
            direction = self.find_step_towards((player.x, player.y), targets)
            if direction and self.move_player(direction):
                actions_left -= 1
                continue
            dirs = ["w", "a", "s", "d"]
            random.shuffle(dirs)
            for d in dirs:
                if self.move_player(d):
                    actions_left -= 1
                    break
            else:
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
                f"Action ({actions_left} left) [w/a/s/d=move, f=attack, g=scavenge, h=medkit, v=antidote, e=eat, b=barricade, u=disarm, o=scout, c=craft, m=molotov, r=steal, k=fight, x=trade, t=drop, z=rest, p=pass, q=save, ?=help]: "
            ).strip().lower()

            if cmd == "?":
                self.show_help()
                continue

            if cmd in {"w", "a", "s", "d"}:
                steps = 1
                if self.double_move_tokens > 0:
                    use = input("Use double move token? [y/N]: ").strip().lower()
                    if use == "y":
                        steps = 2
                        self.double_move_tokens -= 1
                if self.move_player(cmd, steps):
                    if steps > 1:
                        self.add_noise(
                            self.player.x, self.player.y, VEHICLE_NOISE_ZOMBIE_CHANCE
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
            elif cmd == "v":
                if self.use_antidote():
                    actions_left -= 1
                else:
                    print("No antidote to use or not infected!")
            elif cmd == "e":
                if self.eat_food():
                    actions_left -= 1
                else:
                    print("Nothing to eat!")
            elif cmd == "b":
                if self.build_barricade():
                    actions_left -= 1
            elif cmd == "u":
                if self.disarm_trap():
                    actions_left -= 1
            elif cmd == "o":
                if self.scout():
                    actions_left -= 1
            elif cmd == "c":
                if self.craft_item():
                    actions_left -= 1
            elif cmd == "m":
                if self.throw_molotov():
                    actions_left -= 1
                else:
                    print("No molotovs ready!")
            elif cmd == "r":
                if self.steal_item():
                    actions_left -= 1
                else:
                    print("No one here to steal from or pack is full.")
            elif cmd == "k":
                if self.attack_player():
                    actions_left -= 1
                else:
                    print("No one here to attack!")
            elif cmd == "x":
                if self.trade_item():
                    actions_left -= 1
            elif cmd == "t":
                if self.drop_item():
                    actions_left -= 1
            elif cmd == "z":
                if self.rest():
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
        if self.cooperative:
            at_start = all((p.x, p.y) == self.start_pos for p in self.players)
            if self.scenario == 1:
                return any(p.has_antidote for p in self.players) and at_start
            if self.scenario == 2:
                return (
                    any(p.has_keys for p in self.players)
                    and any(p.has_fuel for p in self.players)
                    and at_start
                )
            if self.scenario == 3:
                return (
                    self.radio_parts_collected >= RADIO_PARTS_REQUIRED and at_start
                )
            if self.scenario == 4:
                return (
                    self.called_rescue
                    and self.rescue_timer is not None
                    and self.rescue_timer <= 0
                    and any(p.health > 0 for p in self.players)
                )
            return False
        else:
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
                return (
                    self.called_rescue
                    and self.rescue_timer is not None
                    and self.rescue_timer <= 0
                    and self.player.health > 0
                )
            return False

    def check_defeat(self) -> bool:
        return self.player.health <= 0

    def run(self) -> None:
        intro = SCENARIO_INTROS.get(self.scenario)
        if intro:
            print(intro)
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
        if self.cooperative:
            print("Cooperative mode: all survivors must reach the start to escape together.")
        print(f"Campaign level {self.level}, XP {self.campaign.get('xp', 0)}")
        if self.campaign.get("hp_bonus"):
            print(f"Campaign bonus: +{self.campaign['hp_bonus']} max health")
        if self.double_move_tokens:
            print(f"Campaign bonus: {self.double_move_tokens} double-move tokens")
        if self.has_signal_device:
            print("Campaign bonus: portable radio device")
        try:
            winner: Optional[Player] = None
            while True:
                self.determine_turn_order()
                for pl in list(self.players):
                    self.player_turn(pl)
                    if self.check_victory():
                        winner = pl
                        break
                    if self.check_defeat():
                        self.handle_player_death(pl)
                if winner or not self.players:
                    break
                self.move_zombies()
                for pl in list(self.players):
                    self.player = pl
                    if self.check_defeat():
                        self.handle_player_death(pl)
                if winner or not self.players:
                    break
                self.spawn_random_zombie()
                self.resolve_noise()
                self.update_campfires()
                self.actions_per_turn = ACTIONS_PER_TURN
                self.random_event()
                self.apply_hunger()
                if self.called_rescue and self.rescue_timer is not None:
                    self.rescue_timer -= 1
                    if self.rescue_timer <= 0:
                        self.evacuated_players = self.process_evacuation()
                        self.players = self.evacuated_players
                        if self.evacuated_players:
                            winner = self.evacuated_players[0]
                        break
                self.turn += 1
                self.advance_time_of_day()
                if self.turn >= self.turn_limit:
                    print("Time runs out and the area is overrun. You perish...")
                    fail = SCENARIO_FAILURES.get(self.scenario)
                    if fail:
                        print(fail)
                    break
            if winner:
                self.player = winner
                self.lowest_survivor_hp = min(p.health for p in self.players if p.health > 0)
                if self.scenario == 1:
                    if self.cooperative:
                        print("The survivors return with the antidote and escape together. You win!")
                    else:
                        print("You return with the antidote and escape. You win!")
                    self.campaign["hp_bonus"] = self.campaign.get("hp_bonus", 0) + 1
                    print("Max health increased for next game!")
                elif self.scenario == 2:
                    if self.cooperative:
                        print("The survivors fuel up the vehicle and drive to safety. You win!")
                    else:
                        print("You fuel up the vehicle and drive to safety. You win!")
                    self.double_move_tokens += DOUBLE_MOVE_REWARD
                    print(
                        f"You gain {DOUBLE_MOVE_REWARD} double-move tokens for future runs!"
                    )
                elif self.scenario == 3:
                    if self.cooperative:
                        print("The survivors assemble the radio and send out a signal. You win!")
                    else:
                        print("You assemble the radio and send out a signal. You win!")
                    self.has_signal_device = True
                    self.campaign["signal_device"] = 1
                    print("A portable radio will aid you in the final escape!")
                elif self.scenario == 4:
                    if self.cooperative:
                        print("The rescue helicopter arrives and lifts everyone to safety. You win!")
                    else:
                        names = ", ".join(p.symbol for p in self.evacuated_players)
                        if len(self.evacuated_players) > 1:
                            print(f"{names} escape on the rescue craft!")
                        else:
                            print("The rescue helicopter arrives and lifts you to safety. You win!")
                outro = SCENARIO_OUTROS.get(self.scenario)
                if outro:
                    print(outro)
                self.xp_gained += XP_SCENARIO_WIN
                print(f"You gain {XP_SCENARIO_WIN} XP for surviving the scenario!")
                completed = self.campaign.setdefault("completed_scenarios", [])
                if self.scenario not in completed:
                    completed.append(self.scenario)
            elif not self.players:
                print("No survivors escape the outbreak...")
                fail = SCENARIO_FAILURES.get(self.scenario)
                if fail:
                    print(fail)
                self.campaign["supply_bonus"] = self.campaign.get("supply_bonus", 0) + 1
                print("A stash of supplies is set aside to help in the next run.")
            self.print_summary()
        except (KeyboardInterrupt, EOFError):
            print("\nThanks for playing!")
        finally:
            self.campaign["hp_bonus"] = self.campaign.get("hp_bonus", 0)
            self.campaign["double_move_tokens"] = self.double_move_tokens
            self.campaign["signal_device"] = 1 if self.has_signal_device else 0
            self.campaign["zombies_killed"] = self.campaign.get("zombies_killed", 0) + self.zombies_killed
            xp_total = self.campaign.get("xp", 0) + self.xp_gained
            level = self.campaign.get("level", 1)
            while xp_total >= LEVEL_XP_BASE * level:
                xp_total -= LEVEL_XP_BASE * level
                level += 1
                self.campaign["hp_bonus"] = self.campaign.get("hp_bonus", 0) + 1
                print("Campaign level up! Max health permanently increased by 1.")
            self.campaign["xp"] = xp_total
            self.campaign["level"] = level
            self.level = level
            if self.lowest_survivor_hp is not None:
                self.campaign["last_victory_lowest_hp"] = self.lowest_survivor_hp
                self.campaign["last_victory_zombies_killed"] = self.zombies_killed
            self.check_achievements()
            save_campaign(self.campaign)
            if not self.keep_save and os.path.exists(SAVE_FILE):
                os.remove(SAVE_FILE)


if __name__ == "__main__":
    if os.path.exists(SAVE_FILE) and input("Load saved game? [y/N]: ").strip().lower() == "y":
        Game.load_game().run()
    else:
        diff = input("Choose difficulty [easy/normal/hard]: ").strip().lower() or "normal"
        players = input("Number of players [1-6]: ").strip() or "1"
        scen = (
            input("Choose scenario [1/2/3/4 or 0 for campaign]: ").strip() or "1"
        )
        try:
            scen_num = int(scen)
        except ValueError:
            scen_num = 1
        try:
            num_players = max(1, min(MAX_PLAYERS, int(players)))
        except ValueError:
            num_players = 1
        bots = input(f"AI players [0-{max(0, num_players - 1)}]: ").strip() or "0"
        try:
            num_ai = max(0, min(num_players - 1, int(bots)))
        except ValueError:
            num_ai = 0
        coop = input("Cooperative mode? [y/N]: ").strip().lower() == "y"
        role_names = "/".join(ROLE_DEFS.keys())
        roles = []
        for i in range(num_players):
            if i >= num_players - num_ai:
                roles.append(random.choice(list(ROLE_DEFS.keys())))
            else:
                r = input(f"Role for player {i+1} ({role_names}): ").strip().lower() or "fighter"
                while r not in ROLE_DEFS:
                    r = input(f"Role for player {i+1} ({role_names}): ").strip().lower() or "fighter"
                roles.append(r)
        if scen_num == 0:
            current = 1
            while current <= 4:
                game = Game(diff, current, num_players, num_ai, cooperative=coop, roles=roles)
                game.run()
                if current >= 4:
                    break
                if current not in game.campaign.get("completed_scenarios", []):
                    break
                cont = input("Proceed to next scenario? [y/N]: ").strip().lower()
                if cont != "y":
                    break
                current += 1
        else:
            game = Game(diff, scen_num, num_players, num_ai, cooperative=coop, roles=roles)
            game.run()

