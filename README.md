# Survival Board Game

This repository contains a small prototype of a turn-based survival board game.
The player roams a 10×10 grid collecting supplies while avoiding zombies.

## Requirements
- Python 3.12+

## Running the Game
```bash
python game.py
```

### Controls

During your turn you have two actions. Enter:

- `W` `A` `S` `D` – move one tile.
- `F` – attack an adjacent zombie (70% hit chance).
- `G` – scavenge the current tile for supplies.
- `H` – use a found medkit to recover health.
- `P` – pass the remaining actions.

Zombies move after you finish your actions, then a random event may occur.
The scenario ends after 20 rounds or when you collect **5 supplies**.
Survive as long as you can before your health reaches zero.
