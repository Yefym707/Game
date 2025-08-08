# Survival Board Game

This repository contains a small prototype of a turn-based survival board game.
The player roams a fog-covered 10×10 grid searching for a vital antidote while
avoiding zombies. Inventory space is limited so choose carefully what to carry.

## Requirements
- Python 3.12+

## Running the Game
```bash
python game.py
```

At launch you'll be prompted to choose a difficulty level. Available options
are **easy**, **normal**, and **hard**. If unsure, press Enter for the default
normal difficulty.

### Controls

During your turn you have two actions. Enter:

- `W` `A` `S` `D` – move one tile.
- `F` – attack an adjacent zombie (70% hit chance).
- `G` – scavenge the current tile for supplies or the antidote.
- `H` – use a found medkit to recover health.
- `P` – pass the remaining actions.

 Zombies move after you finish your actions, then a random event may occur.
 Events can alter your next turn – a storm might reduce you to one action while
 an adrenaline rush grants an extra move.
 The scenario ends after 20 rounds. Win by finding the antidote and returning
 to the `S` marked starting tile.
 You can carry at most eight items (supplies and medkits combined).
 Each victory grants +1 max health for future runs, stored in `campaign_save.json`.
 Survive as long as you can before your health reaches zero.
