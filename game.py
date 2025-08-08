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
ATTACK_HIT_CHANCE = 0.7
SCAVENGE_FIND_CHANCE = 0.5
ZOMBIE_SPAWN_CHANCE = 0.3


@dataclass
class Entity:
    x: int
    y: int
    symbol: str


class Player(Entity):
    """Player entity with health and collected supplies."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y, "@")
        self.health: int = STARTING_HEALTH
        self.supplies: int = 0


class Zombie(Entity):
    """Simple zombie that pursues the player."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y, "Z")


class Game:
    """Main game controller handling turns and board state."""

    board_size: int = BOARD_SIZE

    def __init__(self) -> None:
        self.player = Player(self.board_size // 2, self.board_size // 2)
        self.zombies: List[Zombie] = []
        self.supplies_positions: Set[Tuple[int, int]] = set()
        self.spawn_zombies(STARTING_ZOMBIES)
        self.spawn_supplies(STARTING_SUPPLIES)

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
        board = [["." for _ in range(self.board_size)] for _ in range(self.board_size)]
        board[self.player.y][self.player.x] = self.player.symbol
        for x, y in self.supplies_positions:
            board[y][x] = "R"
        for z in self.zombies:
            board[z.y][z.x] = z.symbol

        print(f"Health: {self.player.health}    Supplies: {self.player.supplies}")
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
            self.supplies_positions.remove(pos)
            self.player.supplies += 1
            print("You pick up a supply.")
            return

        if random.random() < SCAVENGE_FIND_CHANCE:
            self.player.supplies += 1
            print("You find a supply!")
        else:
            print("You find nothing of use.")

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
        if random.random() < ZOMBIE_SPAWN_CHANCE:
            self.spawn_zombies(1)
            print("A zombie shambles in from the darkness...")

    # ------------------------------------------------------------------
    # Turn handling and game state
    def player_turn(self) -> None:
        actions_left = ACTIONS_PER_TURN
        while actions_left > 0 and self.player.health > 0:
            self.draw_board()
            cmd = input(
                f"Action ({actions_left} left) [w/a/s/d=move, f=attack, g=scavenge, p=pass]: "
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
            elif cmd == "p":
                break
            else:
                print("Unknown command.")

    def check_victory(self) -> bool:
        return self.player.supplies >= SUPPLIES_TO_WIN

    def check_defeat(self) -> bool:
        return self.player.health <= 0

    def run(self) -> None:
        print("Collect supplies and survive. Ctrl+C to quit.")
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
        except (KeyboardInterrupt, EOFError):
            print("\nThanks for playing!")


if __name__ == "__main__":
    Game().run()

