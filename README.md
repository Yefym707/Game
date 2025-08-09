# Survival Board Game

This repository contains a small prototype of a turn-based survival board game.
The player roams a fog-covered 10×10 grid searching for objectives while
avoiding zombies. Inventory space is limited so choose carefully what to carry.
Each turn your hunger drops – eat supplies to keep from starving.

## Requirements
- Python 3.12+

## Running the Game
```bash
python game.py
```

At launch you'll be prompted to choose a difficulty level and a scenario. If a
previous run was saved, you'll be offered to load it instead. Available
difficulties are **easy**, **normal**, and **hard**. If unsure, press Enter for
the defaults. Scenario **1** tasks you with finding an antidote and returning to
the starting tile. Scenario **2** requires locating both car keys and fuel
before escaping. Scenario **3** asks you to gather three radio parts then retreat
to the start. Scenario **4** is a final stand: call for rescue and survive until
it arrives.

### Controls

During your turn you have two actions. Enter:

- `W` `A` `S` `D` – move one tile (or two if using a double-move token).
- `F` – attack an adjacent zombie (70% hit chance, 90% if armed).
- `G` – scavenge the current tile for supplies, weapons or the antidote.
- `H` – use a found medkit to recover health.
- `E` – consume one supply to restore hunger.
- `B` – spend two supplies to barricade the current tile, blocking zombies once.
- `P` – pass the remaining actions.
- `Q` – save the game and quit.

 Zombies move after you finish your actions, then a random event may occur.
 Events can alter your next turn – a storm might reduce you to one action while
 an adrenaline rush grants an extra move.
 Exploring may also uncover special locations. Pharmacies (`M`) have a high
 chance of yielding medkits while armories (`W`) are the best spots to find
 weapons. Once revealed, their symbols remain on the board.
 Each round hunger decreases. Starving costs health.
 The scenario ends after 20 rounds. Win scenario 1 by finding the antidote and
 returning to the `S` marked starting tile. Scenario 2 is won by bringing both
 keys and fuel back to the start.
 You can carry at most eight items (supplies and medkits combined). Weapons and scenario objectives don't take space.
 Gunfire and the roar of an engine are risky – using a weapon or a double-move token may attract additional zombies.
 Each victory in scenario 1 grants +1 max health for future runs. Winning
 scenario 2 awards five double-move tokens that let you move two tiles in a
 single action on subsequent games. All campaign progress is stored in
 `campaign_save.json`. A save file is also written so you can resume a run later.
 Survive as long as you can before your health reaches zero.

### Achievements

Progress across games unlocks simple achievements that persist between runs:

- **Zombie Hunter** – slay 10 zombies in total.
- **Master Survivor** – complete all four scenarios.

Unlocked achievements are written to `campaign_save.json` together with other
campaign data.
