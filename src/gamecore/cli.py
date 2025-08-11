from __future__ import annotations

import argparse

from . import ai, board, io_textures, rules
from .i18n import gettext as _


def render(state: board.GameState, textures: dict[str, str]) -> str:
    b = state.board
    lines = []
    for y in range(b.height):
        row = ""
        for x in range(b.width):
            ch = b.tiles[y][x]
            if (x, y) not in b.visible:
                ch = "?"
            for z in state.zombies:
                if z.x == x and z.y == y:
                    ch = z.symbol
            if state.player.x == x and state.player.y == y:
                ch = state.player.symbol
            row += textures.get(ch, ch)
        lines.append(row)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args(argv)
    if args.seed is not None:
        rules.set_seed(args.seed)
    textures = io_textures.load_textures()
    state = board.create_game()
    while True:
        print(render(state, textures))
        if state.log:
            print("\n".join(state.log[-5:]))
        cmd = input(_("action_prompt")).strip()
        if cmd == "q":
            break
        board.player_move(state, cmd)
        ai.zombie_turns(state)
        board.end_turn(state)
