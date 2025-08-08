"""Turn-based survival board game prototype.

This module implements a simple console survival game where the player
attempts to gather supplies while avoiding zombies on a grid based map.

Features
--------
* 10x10 board with player, zombies and supply tokens.
* Player has two actions per turn: move, attack, scavenge or pass.
* Melee combat with a chance to hit. Failed attacks cost health.
* Random scavenge system for finding additional supplies.
* Zombies pursue the player and new ones may spawn each round.
* Player wins by collecting enough supplies or loses when health reaches
  zero.

The code is intentionally compact and uses only the Python standard
library so it can run in any environment with Python 3.12 or newer.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Set, Tuple


BOARD_SIZE = 10
ACTIONS_PER_TURN = 2
STARTING_HEALTH = 10
STARTING_ZOMBIES = 5
STARTING_SUPPLIES = 5
SUPPLIES_TO_WIN = 5
INVENTORY_LIMIT = 8
ATTACK_HIT_CHANCE = 0.7
SCAVENGE_FIND_CHANCE = 0.5
ZOMBIE_SPAWN_CHANCE = 0.3
MEDKIT_FIND_CHANCE = 0.2
MEDKIT_HEAL = 3
TURN_LIMIT = 20
REVEAL_RADIUS = 1
REVEAL_SUPPLY_CHANCE = 0.05
REVEAL_ZOMBIE_CHANCE = 0.05


DIFFICULTY_SETTINGS = {
    "easy": {
        "starting_health": STARTING_HEALTH + 2,
        "starting_zombies": max(1, STARTING_ZOMBIES - 2),
        "zombie_spawn_chance": ZOMBIE_SPAWN_CHANCE * 0.7,
        "supplies_to_win": max(1, SUPPLIES_TO_WIN - 1),
        "turn_limit": TURN_LIMIT + 5,
    },
    "normal": {
        "starting_health": STARTING_HEALTH,
        "starting_zombies": STARTING_ZOMBIES,
        "zombie_spawn_chance": ZOMBIE_SPAWN_CHANCE,
        "supplies_to_win": SUPPLIES_TO_WIN,
        "turn_limit": TURN_LIMIT,
    },
    "hard": {
        "starting_health": max(1, STARTING_HEALTH - 2),
        "starting_zombies": STARTING_ZOMBIES + 2,
        "zombie_spawn_chance": ZOMBIE_SPAWN_CHANCE * 1.3,
        "supplies_to_win": SUPPLIES_TO_WIN + 1,
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

    def __init__(self, x: int, y: int, starting_health: int) -> None:
        super().__init__(x, y, "@")
        self.max_health: int = starting_health
        self.health: int = starting_health
        self.supplies: int = 0
        self.medkits: int = 0

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

    def __init__(self, difficulty: str = "normal") -> None:
        settings = DIFFICULTY_SETTINGS.get(difficulty.lower())
        if settings is None:
            raise ValueError("Unknown difficulty")
        self.difficulty = difficulty.lower()
        self.zombie_spawn_chance = settings["zombie_spawn_chance"]
        self.supplies_to_win = settings["supplies_to_win"]
        self.turn_limit = settings["turn_limit"]
        starting_health = settings["starting_health"]
        self.player = Player(self.board_size // 2, self.board_size // 2, starting_health)
        self.zombies: List[Zombie] = []
        self.supplies_positions: Set[Tuple[int, int]] = set()
        self.revealed: Set[Tuple[int, int]] = set()
        self.spawn_zombies(settings["starting_zombies"])
        self.spawn_supplies(STARTING_SUPPLIES)
        self.reveal_area(self.player.x, self.player.y)
        self.turn: int = 0
        self.actions_per_turn: int = ACTIONS_PER_TURN

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

    # ------------------------------------------------------------------
    # Board setup helpers
    def spawn_zombies(self, count: int) -> None:
        for _ in range(count):
            while True:
                x, y = random.randrange(self.board_size), random.randrange(
                    self.board_size
                )
                if (x, y) != (self.player.x, self.player.y) and (x, y) not in {
                    (z.x, z.y) for z in self.zombies
                }:
                    self.zombies.append(Zombie(x, y))
                    break

    def spawn_supplies(self, count: int) -> None:
        for _ in range(count):
            while True:
                x, y = random.randrange(self.board_size), random.randrange(
                    self.board_size
                )
                if (x, y) not in self.supplies_positions and (x, y) != (
                    self.player.x,
                    self.player.y,
                ):
                    self.supplies_positions.add((x, y))
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

        board[self.player.y][self.player.x] = self.player.symbol
        for x, y in self.supplies_positions:
            if (x, y) in self.revealed:
                board[y][x] = "R"
        for z in self.zombies:
            if (z.x, z.y) in self.revealed:
                board[z.y][z.x] = z.symbol

        print(
            f"Health: {self.player.health}    Medkits: {self.player.medkits}    Supplies: {self.player.supplies}    Inventory: {self.player.inventory_size}/{INVENTORY_LIMIT}"
        )
        for row in board:
            print(" ".join(row))

    # ------------------------------------------------------------------
    # Player actions
    def move_player(self, direction: str) -> bool:
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

        nx, ny = self.player.x + dx, self.player.y + dy
        if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
            self.player.x, self.player.y = nx, ny
            self.reveal_area(nx, ny)
            return True
        return False

    def attack(self) -> bool:
        # Find adjacent zombie (4-directional)
        for z in list(self.zombies):
            if abs(z.x - self.player.x) + abs(z.y - self.player.y) == 1:
                if random.random() < ATTACK_HIT_CHANCE:
                    self.zombies.remove(z)
                    print("You slay a zombie!")
                else:
                    self.player.health -= 1
                    print("Your attack misses! You take 1 damage.")
                return True
        return False

    def scavenge(self) -> None:
        pos = (self.player.x, self.player.y)
        if pos in self.supplies_positions:
            if self.player.inventory_size < INVENTORY_LIMIT:
                self.supplies_positions.remove(pos)
                self.player.supplies += 1
                print("You pick up a supply.")
            else:
                print("Your pack is full. You leave the supply behind.")
            return

        if self.player.inventory_size >= INVENTORY_LIMIT:
            print("Your pack is full. You can't carry more.")
            return

        found = False
        if random.random() < SCAVENGE_FIND_CHANCE:
            self.player.supplies += 1
            found = True
            print("You find a supply!")
        if (
            self.player.inventory_size < INVENTORY_LIMIT
            and random.random() < MEDKIT_FIND_CHANCE
        ):
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

    # ------------------------------------------------------------------
    # Zombie behaviour
    def move_zombies(self) -> None:
        for z in list(self.zombies):
            dx = 0 if z.x == self.player.x else (1 if z.x < self.player.x else -1)
            dy = 0 if z.y == self.player.y else (1 if z.y < self.player.y else -1)
            z.x += dx
            z.y += dy
            if z.x == self.player.x and z.y == self.player.y:
                self.player.health -= 1
                print("A zombie bites you! -1 health")

    def spawn_random_zombie(self) -> None:
        if random.random() < self.zombie_spawn_chance:
            self.spawn_zombies(1)
            print("A zombie shambles in from the darkness...")

    def random_event(self) -> None:
        """Trigger a random event at the end of the round."""
        event = random.choice(
            ["nothing", "heal", "supply", "horde", "storm", "adrenaline"]
        )
        if event == "heal" and self.player.health < self.player.max_health:
            self.player.health = min(self.player.max_health, self.player.health + 1)
            print("You catch your breath and recover 1 health.")
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

    # ------------------------------------------------------------------
    # Turn handling and game state
    def player_turn(self) -> None:
        actions_left = self.actions_per_turn
        self.actions_per_turn = ACTIONS_PER_TURN
        while actions_left > 0 and self.player.health > 0:
            self.draw_board()
            cmd = input(
                f"Action ({actions_left} left) [w/a/s/d=move, f=attack, g=scavenge, h=medkit, p=pass]: "
            ).strip().lower()

            if cmd in {"w", "a", "s", "d"}:
                if self.move_player(cmd):
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
            elif cmd == "p":
                break
            else:
                print("Unknown command.")

    def check_victory(self) -> bool:
        return self.player.supplies >= self.supplies_to_win

    def check_defeat(self) -> bool:
        return self.player.health <= 0

    def run(self) -> None:
        print(
            "Collect supplies and survive. Your pack holds at most eight items. Ctrl+C to quit."
        )
        try:
            while True:
                self.player_turn()
                if self.check_victory():
                    print("You gathered enough supplies and escape. You win!")
                    break
                if self.check_defeat():
                    print("You have fallen to the zombies...")
                    break
                self.move_zombies()
                if self.check_defeat():
                    print("You have fallen to the zombies...")
                    break
                self.spawn_random_zombie()
                self.random_event()
                self.turn += 1
                if self.turn >= self.turn_limit:
                    print("Time runs out and the area is overrun. You perish...")
                    break
        except (KeyboardInterrupt, EOFError):
            print("\nThanks for playing!")


if __name__ == "__main__":
    diff = input("Choose difficulty [easy/normal/hard]: ").strip().lower() or "normal"
    Game(diff).run()

