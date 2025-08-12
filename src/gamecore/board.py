from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Iterable

from . import rules, entities


@dataclass
class Board:
    width: int
    height: int
    tiles: List[List[str]]
    noise: Dict[Tuple[int, int], int] = field(default_factory=dict)
    visible: Set[Tuple[int, int]] = field(default_factory=set)

    @classmethod
    def generate(cls, width: int, height: int) -> "Board":
        tiles = [["." for _ in range(width)] for _ in range(height)]
        return cls(width, height, tiles)

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_empty(self, x: int, y: int) -> bool:
        return self.tiles[y][x] == "."

    def add_noise(self, pos: Tuple[int, int], duration: int = 2) -> None:
        self.noise[pos] = duration

    def decay_noise(self) -> None:
        expired = []
        for k in list(self.noise):
            self.noise[k] -= 1
            if self.noise[k] <= 0:
                expired.append(k)
        for k in expired:
            del self.noise[k]

    def reveal(self, x: int, y: int, radius: int = 3) -> None:
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                if self.in_bounds(nx, ny):
                    self.visible.add((nx, ny))

    def to_dict(self) -> Dict:
        return {
            "width": self.width,
            "height": self.height,
            "tiles": self.tiles,
            "noise": {f"{x},{y}": v for (x, y), v in self.noise.items()},
            "visible": [list(pos) for pos in self.visible],
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Board":
        noise = {}
        for k, v in data.get("noise", {}).items():
            x, y = map(int, k.split(","))
            noise[(x, y)] = v
        visible = {tuple(v) for v in data.get("visible", [])}
        return cls(data["width"], data["height"], data["tiles"], noise, visible)


@dataclass
class GameState:
    mode: rules.GameMode
    board: Board
    players: List[entities.Player]
    zombies: List[entities.Zombie]
    active: int = 0
    turn: int = 0
    log: List[str] = field(default_factory=list)

    def add_log(self, msg: str) -> None:
        self.log.append(msg)

    @property
    def current(self) -> entities.Player:
        return self.players[self.active]

    def to_dict(self) -> Dict:
        return {
            "board": self.board.to_dict(),
            "zombies": [z.to_dict() for z in self.zombies],
            "active": self.active,
            "turn": self.turn,
            "log": list(self.log),
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict,
        mode: rules.GameMode = rules.GameMode.SOLO,
        players: List[entities.Player] | None = None,
    ) -> "GameState":
        board = Board.from_dict(data["board"])
        zombies = [entities.Zombie.from_dict(z) for z in data.get("zombies", [])]
        return cls(mode, board, players or [], zombies, data.get("active", 0), data.get("turn", 0), data.get("log", []))


def create_game(
    width: int = rules.BOARD_SIZE,
    height: int = rules.BOARD_SIZE,
    zombies: int = rules.STARTING_ZOMBIES,
    players: int = 1,
    mode: rules.GameMode | None = None,
) -> GameState:
    board = Board.generate(width, height)
    player_list: List[entities.Player] = []
    for i in range(players):
        x = i
        y = 0
        p = entities.Player(x, y, "@", id=i, team=i)
        player_list.append(p)
        board.reveal(x, y)
    zombie_list: List[entities.Zombie] = []
    for _ in range(zombies):
        while True:
            x = rules.RNG.randrange(width)
            y = rules.RNG.randrange(height)
            if all((x, y) != (p.x, p.y) for p in player_list) and all(
                z.x != x or z.y != y for z in zombie_list
            ):
                zombie_list.append(entities.Zombie(x, y, "Z"))
                break
    gmode = mode or (rules.GameMode.LOCAL_COOP if players > 1 else rules.GameMode.SOLO)
    state = GameState(gmode, board, player_list, zombie_list)
    return state


def player_move(state: GameState, direction: str) -> bool:
    offset = rules.DIRECTIONS.get(direction)
    if not offset:
        return False
    dx, dy = offset
    player = state.current
    nx, ny = player.x + dx, player.y + dy
    if not state.board.in_bounds(nx, ny):
        return False
    if not state.board.is_empty(nx, ny):
        return False
    if any(z.x == nx and z.y == ny for z in state.zombies):
        return False
    if any(p is not player and p.x == nx and p.y == ny for p in state.players):
        return False
    player.x, player.y = nx, ny
    state.board.add_noise((nx, ny))
    state.board.reveal(nx, ny)
    state.add_log(f"player {player.id} to {(nx, ny)}")
    return True


def end_turn(state: GameState) -> None:
    state.turn += 1
    state.active = (state.active + 1) % len(state.players)
    state.board.decay_noise()
    player = state.current
    state.board.reveal(player.x, player.y)
