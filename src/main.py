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
from gamecore import i18n

tr = i18n.gettext


# ---------------------------------------------------------------------------
# helper functions


def _data_path(filename: str) -> str:
    """Return the absolute path to a data file located next to this module."""

    return os.path.join(os.path.dirname(__file__), filename)


def load_scenarios() -> List[Scenario]:
    """Return list of :class:`Scenario` objects from JSON definition."""

    with open(_data_path("scenarios.json"), "r", encoding="utf-8") as f:
        data = json.load(f)

    scenarios: List[Scenario] = []
    for sc in data:
        name = sc.get("name") or tr(sc.get("name_key", ""))
        desc = sc.get("description") or tr(sc.get("desc_key", ""))
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

    lines = tr("help_commands").split("\n")
    print(tr("commands_title") + "\n  " + "\n  ".join(lines))
    print(tr("help_text"))


def how_to_play() -> None:
    print(f"\n=== {tr('how_to_play_title')} ===")
    print(tr("how_to_play_desc"))
    print(tr("how_to_play_controls"))
    print(tr("legend"))


def interact_with_trader(campaign: Campaign) -> None:
    trader = campaign.get_trader_at_player()
    if not trader:
        print(tr("no_trader_here"))
        return
    print(trader.list_goods(campaign))
    while True:
        cmd = input(tr("trader_prompt")).strip().lower()
        if cmd == "exit":
            break
        parts = cmd.split()
        if len(parts) != 3:
            print(tr("invalid_command"))
            continue
        action, item, qty = parts[0], parts[1], int(parts[2])
        if action == "buy":
            print(trader.sell_to_player(item, campaign.inventory, qty, campaign))
        elif action == "sell":
            print(trader.buy_from_player(item, campaign.inventory, qty, campaign))
        else:
            print(tr("unknown_command"))


# ---------------------------------------------------------------------------
# Simple text front end for the survival game.

# The module now contains a small start menu which lets the player choose
# between starting a new campaign or exiting the application.  The menu loop is
# kept separate from ``game_loop`` so that once a play session finishes the
# player is returned to the menu and may start another run or quit gracefully.

# game loop

def game_loop(campaign: Campaign) -> None:
    print(tr("welcome_message"))
    print_help()
    # Display objective of the first scenario if available
    if campaign.scenarios:
        first = campaign.scenarios[0]
        desc = getattr(first, "description", "") or getattr(first, "desc", "")
        if desc:
            print(tr("objective").format(description=desc))
    while campaign.player.is_alive():
        print("\n" + tr("turn_time").format(turn=campaign.turn_count, time=campaign.time_of_day))
        print(campaign.game_map.__str__(campaign.enemies.enemies))
        inv = ", ".join(f"{k}({v})" for k, v in campaign.inventory.items.items()) or tr("empty_inventory")
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
        ) or tr("status_none")
        print(
            tr("hp_status").format(
                hp=campaign.player.health,
                max_hp=campaign.player.max_health,
                inv=inv,
                obj=obj,
                status=status,
            )
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
                    print(tr("invalid_coordinates"))
                    continue
                enemy = campaign.enemies.get_enemy_at((tx, ty))
                px, py = campaign.game_map.player_pos
                if not enemy or abs(tx - px) + abs(ty - py) != 1:
                    print(tr("no_enemy_in_range"))
                    continue
            else:
                px, py = campaign.game_map.player_pos
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    enemy = campaign.enemies.get_enemy_at((px + dx, py + dy))
                    if enemy:
                        break
                if not enemy:
                    print(tr("no_enemy_in_range"))
                    continue

            campaign.player.set_position(*campaign.game_map.player_pos)
            campaign.player.start_turn(1)
            pre_hp = enemy.health
            if campaign.player.attack(enemy):
                dmg = pre_hp - enemy.health
                if dmg > 0:
                    print(tr("you_attack_zombie").format(dmg=dmg))
                    if enemy.health <= 0:
                        print(tr("zombie_defeated"))
                        campaign.enemies.enemies.remove(enemy)
                else:
                    print(tr("attack_miss"))
                campaign.turn_count += 1
            else:
                print(tr("no_enemy_in_range"))
            # proceed to enemy phase after a valid attack
        elif command == "search":
            campaign.player.set_position(*campaign.game_map.player_pos)
            campaign.player.start_turn(1)
            found = campaign.player.search(campaign.game_map)
            if found:
                print(tr("you_found_item").format(item=found))
            else:
                print(tr("nothing_useful"))
            campaign.turn_count += 1
        elif command == "trader":
            interact_with_trader(campaign)
            continue
        elif command == "save":
            campaign.save(_data_path("savegame.json"))
            print(tr("game_saved"))
            continue
        elif command == "load":
            try:
                campaign = Campaign.load(_data_path("savegame.json"), campaign.scenarios)
                print(tr("loaded"))
            except FileNotFoundError:
                print(tr("save_not_found"))
            continue
        elif command == "help":
            print_help()
            continue
        elif command == "quit":
            break
        else:
            print(tr("unknown_command_help"))
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
            print(tr("enemy_attacks"))
            if effect:
                print(tr("gained_effect").format(effect=effect.effect_type))

        campaign.tick_time()

    print(tr("game_over"))


def main_menu() -> None:
    """Display the start menu and dispatch to the game loop."""

    while True:
        print("\n=== " + tr("main_menu_title") + " ===")
        print(f"1. {tr('menu_new_game')}")
        print(f"2. {tr('menu_load')}")
        print(f"3. {tr('menu_how_to_play')}")
        print(f"4. {tr('menu_quit')}")
        choice = input("> ").strip().lower()
        if choice in {"1", "start", "new"}:
            difficulty = input(tr("select_difficulty_prompt")).strip().lower()
            players = input(tr("number_of_players_prompt")).strip()
            try:
                num_players = max(1, int(players))
            except ValueError:
                num_players = 1
            if num_players > 1:
                print(tr("multiplayer_not_supported"))
            campaign = Campaign(load_scenarios(), difficulty=difficulty)
            game_loop(campaign)
        elif choice in {"2", "load"}:
            path = _data_path("savegame.json")
            if os.path.exists(path):
                try:
                    campaign = Campaign.load(path, load_scenarios())
                    print(tr("loaded"))
                    game_loop(campaign)
                except Exception:
                    print(tr("failed_to_load_save"))
            else:
                print(tr("save_not_found"))
        elif choice in {"3", "how", "help"}:
            how_to_play()
        elif choice in {"4", "exit", "quit"}:
            break
        else:
            print(tr("unknown_menu_choice"))


def main() -> None:
    main_menu()


if __name__ == "__main__":  # pragma: no cover - manual execution only
    main()
