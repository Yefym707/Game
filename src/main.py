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
from scenario import Scenario
from cli import _load_locale


# ---------------------------------------------------------------------------
# helper functions


def _data_path(filename: str) -> str:
    """Return the absolute path to a data file located next to this module."""

    return os.path.join(os.path.dirname(__file__), filename)


def load_scenarios() -> List[Scenario]:
    """Return list of :class:`Scenario` objects from JSON definition."""

    with open(_data_path("scenarios.json"), "r", encoding="utf-8") as f:
        data = json.load(f)

    locale = _load_locale()
    scenarios: List[Scenario] = []
    for sc in data:
        name = sc.get("name") or locale.get(sc.get("name_key", ""), sc.get("name_key", ""))
        desc = sc.get("description") or locale.get(sc.get("desc_key", ""), sc.get("desc_key", ""))
        scenarios.append(
            Scenario(
                name=name,
                description=desc,
                win_condition=sc.get("win_condition", {}),
                turn_limit=sc.get("turn_limit"),
                special_conditions=sc.get("special_conditions", {}),
                lose_condition=sc.get("lose_condition", {}),
            )
        )
    return scenarios


def print_help() -> None:
    """Display available commands and their descriptions."""

    lines = [
        "n/s/e/w - move north/south/east/west",
        "attack [x y] - attack an adjacent enemy or coordinates",
        "search - scavenge the current tile for items",
        "rest - regain some health at a camp",
        "inv - show inventory and items",
        "trader - trade with a merchant on the same tile",
        "save - write the current game to disk",
        "load - load the last save if present",
        "map - display the map again",
        "help - show this help message",
        "quit - exit the game",
    ]
    print("Commands:\n  " + "\n  ".join(lines))
    print(
        "Find supplies, manage hunger and thirst, and avoid or fight zombies.\n"
        "Objective: find the antidote and return to the start."
    )


def how_to_play() -> None:
    print("\n=== How to Play ===")
    print(
        "Find supplies, manage hunger and thirst, and avoid or fight zombies.\n"
        "Goal: locate the antidote and bring it back to the starting point."
    )
    print(
        "Use n/s/e/w to move, rest to recover, inv to view inventory, and save/load to manage progress."
    )
    print("Legend: P=Player, Z=Zombie, #=Wall, I=Item")


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
    # Display objective of the first scenario if available
    if campaign.scenarios:
        first = campaign.scenarios[0]
        desc = getattr(first, "description", "") or getattr(first, "desc", "")
        if desc:
            print(f"Objective: {desc}")
    while campaign.player.is_alive():
        print(f"\nTurn: {campaign.turn_count} | Time: {campaign.time_of_day}")
        print(campaign.game_map.__str__(campaign.enemies.enemies))
        inv = ", ".join(f"{k}({v})" for k, v in campaign.inventory.items.items()) or "empty"
        current = None
        if campaign.current_scenario_id:
            for sc in campaign.scenarios:
                sid = getattr(sc, "name", getattr(sc, "id", None))
                if sid == campaign.current_scenario_id:
                    current = sc
                    break
        else:
            current = campaign.scenarios[0] if campaign.scenarios else None
        obj = getattr(current, "description", "") if current else ""
        status = ", ".join(
            f"{e.effect_type} ({e.duration})" if e.duration >= 0 else e.effect_type
            for e in campaign.status_effects
        ) or "None"
        print(
            f"HP: {campaign.player.health}/{campaign.player.max_health} | "
            f"Inventory: {inv} | Objective: {obj} | Status: {status}"
        )
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
        elif command.startswith("attack"):
            parts = command.split()
            enemy = None
            if len(parts) == 3:
                try:
                    tx, ty = int(parts[1]), int(parts[2])
                except ValueError:
                    print("Invalid coordinates.")
                    continue
                enemy = campaign.enemies.get_enemy_at((tx, ty))
                px, py = campaign.game_map.player_pos
                if not enemy or abs(tx - px) + abs(ty - py) != 1:
                    print("No enemy in range.")
                    continue
            else:
                px, py = campaign.game_map.player_pos
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    enemy = campaign.enemies.get_enemy_at((px + dx, py + dy))
                    if enemy:
                        break
                if not enemy:
                    print("No enemy in range.")
                    continue

            campaign.player.set_position(*campaign.game_map.player_pos)
            campaign.player.start_turn(1)
            pre_hp = enemy.health
            if campaign.player.attack(enemy):
                dmg = pre_hp - enemy.health
                if dmg > 0:
                    print(f"You attack the zombie for {dmg} damage.")
                    if enemy.health <= 0:
                        print("The zombie is defeated!")
                        campaign.enemies.enemies.remove(enemy)
                else:
                    print("You miss.")
                campaign.turn_count += 1
            else:
                print("No enemy in range.")
            # proceed to enemy phase after a valid attack
        elif command == "search":
            campaign.player.set_position(*campaign.game_map.player_pos)
            campaign.player.start_turn(1)
            found = campaign.player.search(campaign.game_map)
            if found:
                print(f"You found {found}.")
            else:
                print("Nothing useful here.")
            campaign.turn_count += 1
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

    locale = _load_locale()
    while True:
        print("\n=== Survival Game ===")
        print(f"1. {locale.get('menu_new_game', 'Start New Game')}")
        print(f"2. {locale.get('menu_load', 'Load Game')}")
        print(f"3. {locale.get('menu_how_to_play', 'How to Play')}")
        print(f"4. {locale.get('menu_quit', 'Quit')}")
        choice = input("> ").strip().lower()
        if choice in {"1", "start", "new"}:
            difficulty = input("Select difficulty [easy/normal/hard]: ").strip().lower()
            players = input("Number of players [1]: ").strip()
            try:
                num_players = max(1, int(players))
            except ValueError:
                num_players = 1
            if num_players > 1:
                print("Multiplayer not yet supported; starting solo game.")
            campaign = Campaign(load_scenarios(), difficulty=difficulty)
            game_loop(campaign)
        elif choice in {"2", "load"}:
            path = _data_path("savegame.json")
            if os.path.exists(path):
                try:
                    campaign = Campaign.load(path, load_scenarios())
                    print("Loaded.")
                    game_loop(campaign)
                except Exception:
                    print("Failed to load save.")
            else:
                print("No save found.")
        elif choice in {"3", "how", "help"}:
            how_to_play()
        elif choice in {"4", "exit", "quit"}:
            break
        else:
            print("Unknown command. Choose 1-4.")


def main() -> None:
    main_menu()


if __name__ == "__main__":  # pragma: no cover - manual execution only
    main()
