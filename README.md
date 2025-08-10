# Survival Board Game

This repository contains a small prototype of a turn-based survival board game.
The player roams a fog-covered 10×10 grid searching for objectives while
avoiding zombies. Inventory space is limited so choose carefully what to carry.
Each turn your hunger drops – eat supplies to keep from starving. Zombie
numbers scale with the size of your group to keep larger teams on edge.

## Requirements
- Python 3.12+

## Running the Game
```bash
python game.py
```

At launch you'll be prompted to choose a difficulty level, number of players
–1–4 in hot-seat mode–and a scenario. You may also add simple AI-controlled
survivors to fill any empty slots. More players mean extra starting zombies and
a higher spawn rate, and in scenario four the rescue takes longer to arrive.
These bots heal, eat, scavenge and pathfind toward revealed objectives and
supplies. If a previous run was saved, you'll be offered to load it instead.
Available difficulties are **easy**, **normal**, and
**hard**. If unsure, press Enter for the defaults. You can optionally enable a
cooperative mode where all survivors must escape together. Scenario **1** tasks you with
finding an antidote and returning to the starting tile. Scenario **2** requires
locating both car keys and fuel before escaping. Scenario **3** asks you to
gather three radio parts then retreat to the start. Scenario **4** is a final
stand: call for rescue and survive until it arrives.

In cooperative mode the group shares victory conditions – once the objective is
met all surviving players must regroup on the starting tile to win together.

### Controls

During your turn you have two actions. Enter:

- `W` `A` `S` `D` – move one tile (or two if using a double-move token).
- `F` – attack an adjacent zombie (70% hit chance, 90% if armed).
- `G` – scavenge the current tile for supplies, weapons or the antidote.
- `H` – use a found medkit to recover health.
- `E` – consume one supply to restore hunger.
- `B` – spend two supplies to barricade the current tile, blocking zombies once.
- `C` – craft items (3 supplies → medkit, supply + fuel → molotov).
- `M` – throw a molotov to burn adjacent zombies.
- `R` – attempt to steal an item from another player sharing your tile (50% success, -1 HP on failure).
- `T` – drop the item of your choice on the current tile.
- `P` – pass the remaining actions.
- `Q` – save the game and quit.

Players are shown on the board as numbers `1`–`4`.

Zombies move after all players finish their actions, then a random event may
occur. Fallen survivors do not stay down—any player who dies will rise again as
a zombie at that spot. Events can alter the next round’s pace – a storm might
reduce everyone to one action while an adrenaline rush grants an extra move.
Friendly survivors may appear with supplies or medkits and the wind can
momentarily lift the fog to reveal unexplored tiles. Exploring may also uncover
special locations. Pharmacies
(`M`) have a high chance of yielding medkits while armories (`W`) are the best
spots to find weapons. Once revealed, their symbols remain on the board. Each round hunger decreases for every
survivor. Starving costs health. The scenario ends after 20 rounds. Win scenario
1 by finding the antidote and returning to the `S` marked starting tile. Scenario
2 is won by bringing both keys and fuel back to the start. You can carry at most
eight items (supplies and medkits combined). Weapons and scenario objectives
don't take space. Gunfire and the roar of an engine are risky – using a weapon or
a double-move token may attract additional zombies. Each victory in scenario 1
grants +1 max health for future runs. Winning scenario 2 awards five double-move
tokens that let you move two tiles in a single action on subsequent games. All
campaign progress is stored in `campaign_save.json`. A save file is also written
so you can resume a run later. Survive as long as you can before your health
reaches zero.

Dropped items remain on the board: supplies show as `R`, medkits as `H`, weapons as `G` and molotovs as `L` once the tile is revealed.

### Achievements

Progress across games unlocks simple achievements that persist between runs:

- **Zombie Hunter** – slay 10 zombies in total.
- **Master Survivor** – complete all four scenarios.
- **Scenario 1 Complete** – finish the antidote mission.
- **Scenario 2 Complete** – escape with keys and fuel.
- **Scenario 3 Complete** – assemble the radio.
- **Scenario 4 Complete** – survive the final rescue.
- **Last Breath** – win a scenario with only 1 HP remaining.
- **Pacifist** – win a scenario without killing any zombies.

Unlocked achievements are written to `campaign_save.json` together with other
campaign data.
