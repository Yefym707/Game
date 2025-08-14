from __future__ import annotations

import json
import os
from types import SimpleNamespace

from game_board import GameBoard
from player import Player
from turn_manager import TurnManager
from event_deck import GameState
from scenario import Scenario


def _colored_board(board: GameBoard) -> str:
    """Return a colorized ASCII representation of ``board``.

    Only a couple of entity symbols are colorised to keep the implementation
    simple: ``P`` (players) are rendered in green and ``Z`` (zombies) in red.
    All other characters are passed through unchanged.  Colour codes use ANSI
    escape sequences which are widely supported on modern terminals.
    """

    mapping = {"P": "\x1b[32mP\x1b[0m", "Z": "\x1b[31mZ\x1b[0m"}
    lines = []
    for line in board.display_board().splitlines():
        lines.append("".join(mapping.get(ch, ch) for ch in line))
    return "\n".join(lines)


def run_game_cli() -> None:
    """Run an interactive console session of the game.

    The function wires together :class:`GameBoard`, :class:`Player`,
    :class:`TurnManager` and the event deck to provide a very small playable
    experience.  The player is prompted for textual commands and the game
    continues until the scenario is completed, the player dies or the user
    quits the session.
    """

    # ------------------------------------------------------------------
    # load scenarios
    scenarios_file = os.path.join(os.path.dirname(__file__), "scenarios.json")
    try:
        with open(scenarios_file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        # Fallback scenario when the file is missing.  Survive three rounds.
        data = [
            {
                "id": "intro",
                "name": "Intro",
                "description": "Survive three rounds.",
                "win_condition": {"survive_turns": 3},
                "next_scenario": None,
            }
        ]

    scenarios = {sc["id"]: sc for sc in data}
    current_id = data[0]["id"] if data else None

    player = Player()

    # ------------------------------------------------------------------
    # scenario loop
    while current_id:
        sc_def = scenarios[current_id]
        scenario = Scenario(
            name=sc_def.get("name", current_id),
            description=sc_def.get("description", ""),
            win_condition=sc_def.get("win_condition", {}),
            special_conditions=sc_def.get("special_conditions", {}),
        )

        # Prepare a fresh board and state for the scenario
        board = GameBoard()
        board.items = {}
        player.set_position(0, 0)
        board.place_entity(player.x, player.y, player.symbol)
        scenario.setup(board, [player])

        game_state = GameState(board=board, players=[player], items=board.items, zombies=[])
        game_state.turn = 0
        manager = TurnManager([player], game_state=game_state)

        print(f"Starting scenario: {scenario.name}")
        if scenario.description:
            print(scenario.description)

        scenario_finished = False
        while not scenario_finished:
            current, actions = manager.start_turn()
            current.start_turn(actions)
            while not current.turn_over and current.is_alive():
                print(_colored_board(board))
                inv = dict(getattr(current.inventory, "items", {}))
                print(
                    f"{current.name} | HP {current.health}/{current.max_health} | "
                    f"Inventory: {inv} | Actions: {current.actions_left}"
                )
                cmd = (
                    input("Action (move <dir>/attack x y/search/end/quit)> ")
                    .strip()
                    .lower()
                )
                if cmd in {"end", "pass"}:
                    current.end_turn()
                    break
                if cmd in {"quit", "exit"}:
                    print("Quitting game.")
                    return
                parts = cmd.split()
                if not parts:
                    continue
                if parts[0] == "move" and len(parts) == 2:
                    mapping = {
                        "north": (0, -1),
                        "south": (0, 1),
                        "east": (1, 0),
                        "west": (-1, 0),
                        "n": (0, -1),
                        "s": (0, 1),
                        "e": (1, 0),
                        "w": (-1, 0),
                    }
                    offset = mapping.get(parts[1])
                    if offset:
                        if not current.move(offset[0], offset[1], board):
                            print("Cannot move in that direction.")
                    else:
                        print("Unknown direction.")
                elif parts[0] == "attack" and len(parts) == 3:
                    try:
                        tx, ty = int(parts[1]), int(parts[2])
                    except ValueError:
                        print("Invalid coordinates.")
                        continue
                    if abs(current.x - tx) + abs(current.y - ty) != 1:
                        print("Target must be adjacent.")
                        continue
                    if not board.within_bounds(tx, ty) or board.grid[ty][tx] != "Z":
                        print("No zombie there.")
                        continue
                    dummy = SimpleNamespace(x=tx, y=ty, health=1)

                    def _take_damage(amount: int, d: SimpleNamespace = dummy) -> None:
                        d.health = max(0, d.health - amount)

                    dummy.take_damage = _take_damage
                    if current.attack(dummy):
                        if dummy.health <= 0:
                            board.remove_entity(tx, ty)
                            try:
                                game_state.zombies.remove((tx, ty))
                            except ValueError:
                                pass
                            print("Zombie defeated.")
                    else:
                        print("Attack failed.")
                elif parts[0] == "search":
                    item = current.search(board)
                    if item:
                        print(f"Found {item}.")
                    else:
                        print("Nothing found.")
                else:
                    print("Unknown command.")

            if not current.is_alive():
                print("All players died. Game Over.")
                return

            manager.end_turn()
            game_state.turn = manager.round - 1
            if scenario.is_completed(game_state):
                print(f"{current.name} completed '{scenario.name}'!")
                scenario_finished = True

        current_id = sc_def.get("next_scenario")

    print("Campaign finished.")


__all__ = ["run_game_cli"]
