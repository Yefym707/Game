# Survival Board Game

This repository contains a small prototype of a turn-based survival board game.
The player roams a fog-covered 10×10 grid searching for objectives while
avoiding zombies. Inventory space is limited so choose carefully what to carry.
Players may also spend an action to scout an adjacent tile, peeking through the
fog before committing to a move.
Survivors sharing a tile can steal from or even brawl with each other, though
such skirmishes are noisy and dangerous.
Each turn your hunger drops – eat supplies to keep from starving. Zombie
numbers scale with the size of your group to keep larger teams on edge.
Scavenging pulls from a finite loot deck so items won't repeat until the deck
is reshuffled, reinforcing the tabletop feel.
Loud actions such as gunfire or revving an engine place noise tokens on the
board. These markers linger for a couple of rounds and at the end of each
round may spawn new zombies, capturing the tension of physical board games
that track noise.
Combat and other risky actions explicitly roll dice, displaying the result so
you can cheer or lament the luck of the draw just like at a real table.

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
cooperative mode where all survivors must escape together. Selecting scenario
**0** launches a full four-part campaign, automatically progressing to the next
chapter after each victory. Scenario **1** tasks you with finding an antidote
and returning to the starting tile. Scenario **2** requires locating both car
keys and fuel before escaping. Scenario **3** asks you to gather three radio
parts then retreat to the start. Scenario **4** is a final stand: call for
rescue and survive until it arrives.

In cooperative mode the group shares victory conditions – once the objective is
met all surviving players must regroup on the starting tile to win together.

### Controls

During your turn you have two actions. Enter:

- `W` `A` `S` `D` – move one tile (or two if using a double-move token).
- `F` – attack an adjacent zombie; roll a d10 (≤7 hits, ≤9 if armed).
- `G` – scavenge the current tile for supplies, weapons or the antidote.
- `H` – use a found medkit to recover health.
- `E` – consume one supply to restore hunger.
- `B` – spend two supplies to barricade the current tile, blocking zombies once.
- `O` – scout an adjacent tile to reveal more of the map.
- `C` – craft items (3 supplies → medkit, supply + fuel → molotov).
- `M` – throw a molotov to burn adjacent zombies.
- `R` – attempt to steal an item from another player sharing your tile; roll a d10 (≤5 succeeds, failure costs 1 HP).
- `K` – attack another player on your tile; roll a d10 (≤5 hits, failure hurts you. The brawl creates noise.)
- `X` – trade an item with another player on your tile.
- `T` – drop the item of your choice on the current tile.
- `Z` – rest to recover 1 hunger or heal 1 HP if already well fed.
- `P` – pass the remaining actions.
- `Q` – save the game and quit.

Players are shown on the board as numbers `1`–`4`.

Zombies move after all players finish their actions, then an event card is drawn
from a shuffled deck. Cards are not returned until the deck is exhausted,
mirroring a physical board game's event system. Fallen survivors do not stay
down—any player who dies will rise again as a zombie at that spot. Events can
alter the next round’s pace – a storm might reduce everyone to one action while
an adrenaline rush grants an extra move. Friendly survivors may appear with
supplies or medkits and, if there’s room, may even join your group. The wind
can momentarily lift the fog to reveal unexplored tiles. Exploring may also
uncover special locations. Pharmacies (`M`) have a high chance of yielding
medkits while armories (`W`) are the best spots to find weapons. Hidden traps
(`!`) may also appear and will injure any survivor that triggers them, though
they can destroy zombies as well. Once revealed, their symbols remain on the board.
Each round hunger decreases for every
survivor. Starving costs health. The scenario ends after 20 rounds. Win scenario
1 by finding the antidote and returning to the `S` marked starting tile. Scenario
2 is won by bringing both keys and fuel back to the start. You can carry at most
eight items (supplies and medkits combined). Weapons and scenario objectives
don't take space. Gunfire, engines and molotov blasts leave noise tokens that
linger for several rounds and may attract additional zombies when the round
ends. Each victory in scenario 1
grants +1 max health for future runs. Winning scenario 2 awards five double-move
tokens that let you move two tiles in a single action on subsequent games. All
campaign progress is stored in `campaign_save.json`. A save file is also written
so you can resume a run later. Survive as long as you can before your health
reaches zero.

Dropped items remain on the board: supplies show as `R`, medkits as `H`, weapons as `G` and molotovs as `L` once the tile is revealed.
Noise markers from loud actions show their remaining turns as numbers until they attract or fade.

Experience points accumulate across the campaign. Killing zombies and
surviving scenarios grant XP; each level reached permanently adds +1 to
maximum health for future runs.

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
