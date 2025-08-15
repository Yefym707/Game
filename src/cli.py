from __future__ import annotations

import json
import os
from types import SimpleNamespace

from gamecore import i18n
tr = i18n.gettext

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


def _load_locale(lang: str = "en") -> dict:
    """Deprecated helper – kept for backward compatibility."""
    return {}


def run_game_cli() -> None:
    """Run an interactive console session of the game.

    The function wires together :class:`GameBoard`, :class:`Player`,
    :class:`TurnManager` and the event deck to provide a very small playable
    experience.  The player is prompted for textual commands and the game
    continues until the scenario is completed, the player dies or the user
    quits the session.
    """

    # ------------------------------------------------------------------
    # load scenarios ------------------------------------------------------
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

    scenarios = {}
    for sc in data:
        name = sc.get("name")
        desc = sc.get("description")
        if sc.get("name_key"):
            name = tr(sc["name_key"])
        if sc.get("desc_key"):
            desc = tr(sc["desc_key"])
        sc = dict(sc)
        sc["name"] = name
        sc["description"] = desc
        scenarios[sc["id"]] = sc

    # let the player choose a scenario ----------------------------------
    ids = list(scenarios.keys())
    current_id = ids[0] if ids else None
    if len(ids) > 1:
        print(tr("available_scenarios"))
        for sid in ids:
            sc = scenarios[sid]
            print(f"  {sid}: {sc['name']} - {sc['description']}")
        choice = input(tr("choose_scenario_prompt")).strip().lower()
        if choice in scenarios:
            current_id = choice

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

        print(tr("starting_scenario").format(name=scenario.name))
        if scenario.description:
            print(tr("objective").format(description=scenario.description))
        print(tr("help_controls_hint"))

        scenario_finished = False
        while not scenario_finished:
            current, actions = manager.start_turn()
            current.start_turn(actions)
            while not current.turn_over and current.is_alive():
                print(_colored_board(board))
                inv = dict(getattr(current.inventory, "items", {}))
                print(
                    tr("player_status").format(
                        name=current.name,
                        hp=current.health,
                        max_hp=current.max_health,
                        inv=inv,
                        actions=current.actions_left,
                    )
                )
                cmd = (
                    input(tr("action_prompt"))
                    .strip()
                    .lower()
                )
                if cmd in {"end", "pass"}:
                    current.end_turn()
                    break
                if cmd in {"quit", "exit"}:
                    print(tr("quitting_game"))
                    return
                if cmd == "help":
                    print(tr("help_text"))
                    continue
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
                            print(tr("move_blocked"))
                    else:
                        print(tr("unknown_direction"))
                elif parts[0] == "attack" and len(parts) == 3:
                    try:
                        tx, ty = int(parts[1]), int(parts[2])
                    except ValueError:
                        print(tr("invalid_coordinates"))
                        continue
                    if abs(current.x - tx) + abs(current.y - ty) != 1:
                        print(tr("target_must_be_adjacent"))
                        continue
                    if not board.within_bounds(tx, ty) or board.grid[ty][tx] != "Z":
                        print(tr("no_zombie_there"))
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
                            print(tr("zombie_defeated"))
                    else:
                        print(tr("attack_failed"))
                elif parts[0] == "search":
                    item = current.search(board)
                    if item:
                        print(tr("found_item").format(item=item))
                    else:
                        print(tr("nothing_found"))
                else:
                    print(tr("unknown_command"))

            if not current.is_alive():
                print(tr("all_players_died"))
                return

            manager.end_turn()
            game_state.turn = manager.round - 1
            if scenario.is_completed(game_state):
                print(
                    tr("scenario_completed").format(
                        player=current.name, scenario=scenario.name
                    )
                )
                scenario_finished = True

        current_id = sc_def.get("next_scenario")

    print(tr("campaign_finished"))


__all__ = ["run_game_cli"]
