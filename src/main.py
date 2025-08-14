"""Entry point for running the text based survival game.

The original ``main.py`` in this repository was intentionally truncated and
only contained a few comments.  This file provides a minimal interactive
loop that ties together the other modules.  The goal is not to create a
feature complete roguelike but to showcase how the provided building blocks
can be combined into a playable experience.  The module can also serve as a
reference for unit tests which exercise parts of the game logic.
"""

from __future__ import annotations

import json
import os
from typing import List

from campaign import Campaign


# ---------------------------------------------------------------------------
# helper functions


def _data_path(filename: str) -> str:
    """Return the absolute path to a data file located next to this module."""

    return os.path.join(os.path.dirname(__file__), filename)


def load_scenarios() -> List[dict]:
    with open(_data_path("scenarios.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def print_help() -> None:
    print(
        "Commands: n/s/e/w – move, map – map, rest – rest,\n",
        "  trader – interact with trader, inv – inventory,\n",
        "  save/load – save or load game, quit – exit."
    )


def interact_with_trader(campaign: Campaign) -> None:
    trader = campaign.get_trader_at_player()
    if not trader:
        print("There is no trader here.")
        return
    print(trader.list_goods(campaign))
    while True:
        cmd = input("(buy item qty / sell item qty / exit)> ").strip().lower()
        if cmd == "exit":
            break
        parts = cmd.split()
        if len(parts) != 3:
            print("Invalid command.")
            continue
        action, item, qty = parts[0], parts[1], int(parts[2])
        if action == "buy":
            print(trader.sell_to_player(item, campaign.inventory, qty, campaign))
        elif action == "sell":
            print(trader.buy_from_player(item, campaign.inventory, qty, campaign))
        else:
            print("Unknown command.")


# ---------------------------------------------------------------------------
# Simple text front end for the survival game.

# The module now contains a small start menu which lets the player choose
# between starting a new campaign or exiting the application.  The menu loop is
# kept separate from ``game_loop`` so that once a play session finishes the
# player is returned to the menu and may start another run or quit gracefully.

# game loop

def game_loop(campaign: Campaign) -> None:
    print("Welcome to the text-based survival game!")
    print_help()
    while campaign.player.is_alive():
        print(f"\nTurn: {campaign.turn_count} | Time: {campaign.time_of_day}")
        print(campaign.game_map.__str__(campaign.enemies.enemies))
        command = input("> ").strip().lower()

        # ----- player actions -----
        if command in ("n", "s", "e", "w"):
            dx = 1 if command == "e" else -1 if command == "w" else 0
            dy = 1 if command == "s" else -1 if command == "n" else 0
            campaign.game_map.move_player(dx, dy)
            campaign.turn_count += 1
        elif command == "map":
            print(campaign.game_map.__str__(campaign.enemies.enemies))
            continue
        elif command == "rest":
            print(campaign.rest_at_camp())
            continue
        elif command == "inv":
            print(campaign.inventory)
            continue
        elif command.startswith("use "):
            item = command.split(maxsplit=1)[1]
            print(campaign.inventory.use_item(item, campaign))
            continue
        elif command == "trader":
            interact_with_trader(campaign)
            continue
        elif command == "save":
            campaign.save(_data_path("savegame.json"))
            print("Game saved.")
            continue
        elif command == "load":
            try:
                campaign = Campaign.load(_data_path("savegame.json"), campaign.scenarios)
                print("Loaded.")
            except FileNotFoundError:
                print("Save not found.")
            continue
        elif command == "help":
            print_help()
            continue
        elif command == "quit":
            break
        else:
            print("Unknown command. Type 'help' for a list of commands.")
            continue

        # ----- enemy phase -----
        campaign.enemies.move_towards_player(
            campaign.game_map.player_pos,
            campaign.game_map.width,
            campaign.game_map.height,
            campaign,
        )
        enemy = campaign.enemies.get_enemy_at(campaign.game_map.player_pos)
        if enemy:
            effect = enemy.perform_attack(campaign)
            print("An enemy attacks you!")
            if effect:
                print(f"You gained effect: {effect.effect_type}")

        campaign.tick_time()

    print("Game over.")


def main_menu() -> None:
    """Display the start menu and dispatch to the game loop."""

    while True:
        print("\n=== Survival Game ===")
        print("1. Start New Game")
        print("2. Exit")
        choice = input("> ").strip().lower()
        if choice in {"1", "start", "new"}:
            campaign = Campaign(load_scenarios())
            game_loop(campaign)
        elif choice in {"2", "exit", "quit"}:
            break
        else:
            print("Unknown command. Choose 1 or 2.")


def main() -> None:
    main_menu()


if __name__ == "__main__":  # pragma: no cover - manual execution only
    main()
