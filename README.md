# Survival Board Game

This repository contains a small prototype of a turn-based survival board game
for one to six players. The player roams a fog-covered 10×10 grid searching for objectives while
avoiding zombies and navigating around rubble walls that block movement. Inventory space is limited so choose carefully what to carry.
Players may also spend an action to scout an adjacent tile, peeking through the
fog before committing to a move.
Survivors sharing a tile can steal from or even brawl with each other, though
such skirmishes are noisy and dangerous.
Each turn your hunger drops – eat supplies to keep from starving. Zombie
numbers scale with the size of your group to keep larger teams on edge.
Scavenging pulls from a finite loot deck so items won't repeat until the deck
is reshuffled, reinforcing the tabletop feel. Both event and loot deck
compositions are stored in `decks.json` so you can tweak card frequencies or
add your own entries.
Loud actions such as gunfire or revving an engine place noise tokens on the
board. These markers linger for a couple of rounds and at the end of each
round may spawn new zombies, capturing the tension of physical board games
that track noise.
  Simple crafting lets survivors convert supplies into medkits, traps,
  campfires, flashlights and molotov cocktails for a tactical edge. A day/night cycle
reduces visibility after dark unless a survivor carries a flashlight.
Scattered shelters on the board offer weary survivors a safe place to rest
and recover extra health or hunger.
Combat and other risky actions explicitly roll dice, displaying the result so
you can cheer or lament the luck of the draw just like at a real table.
Zombie bites may also infect survivors; without an antidote they will turn
into zombies after a few rounds, adding urgency to secure the cure.

## Requirements
- Python 3.12+

## Running the Game
```bash
python game.py
```

At launch you'll be prompted to choose a difficulty level, number of players
–1–6 in hot-seat mode–and a scenario. You may also add simple AI-controlled
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
rescue and survive until it arrives. Only two seats are available on the
rescue craft, so in competitive games the survivors with the highest zombie
kill counts board first.

Each chapter begins and ends with a brief piece of flavor text, providing a
story hook before play and a short epilogue once the scenario concludes.

In cooperative mode the group shares victory conditions – once the objective is
met all surviving players must regroup on the starting tile to win together.

### Roles

Before play begins each survivor chooses a role, granting a small passive
ability reminiscent of character cards in a physical board game:

- **Fighter** – attacks are 10% more likely to hit.
- **Medic** – medkits and resting restore an extra point of health.
- **Scout** – reveals one additional tile and draws a second loot card if the
  first is empty.
  - **Engineer** – barricades, traps, campfires and flashlights cost one less supply.

These asymmetrical perks encourage different play styles while keeping the
rules light.

### Controls

During your turn you have two actions. Enter:

- `W` `A` `S` `D` – move one tile (or two if using a double-move token).
- `F` – attack an adjacent zombie; roll a d10 (≤7 hits, ≤9 if armed).
- `G` – scavenge the current tile for supplies, weapons or the antidote.
- `H` – use a found medkit to recover health.
- `V` – use the antidote to cure infection at the cost of the item.
- `E` – consume one supply to restore hunger.
- `B` – spend two supplies to barricade the current tile, blocking zombies once.
- `U` – disarm a trap on your tile, salvaging a supply.
  - `O` – scout an adjacent tile to reveal more of the map.
  - `C` – craft items (3 supplies → medkit, supply + fuel → molotov, 2 supplies → trap, 2 supplies → flashlight, 2 supplies → campfire).
- `M` – throw a molotov to burn adjacent zombies.
- `R` – attempt to steal an item from another player sharing your tile; roll a d10 (≤5 succeeds, failure costs 1 HP).
- `K` – attack another player on your tile; roll a d10 (≤5 hits, failure hurts you. The brawl creates noise.)
- `X` – trade an item with another player on your tile.
- `T` – drop the item of your choice on the current tile.
  - `Z` – rest to recover 1 hunger or heal 1 HP if already well fed (bonuses when at a campfire or shelter).
- `P` – pass the remaining actions.
- `Q` – save the game and quit.
- `?` – show a quick reference of controls and board symbols.

Players are shown on the board as numbers `1`–`6`.

Zombies move after all players finish their actions, then an event card is drawn
from a shuffled deck. Cards are not returned until the deck is exhausted,
mirroring a physical board game's event system. Fallen survivors do not stay
down—any player who dies will rise again as a zombie at that spot. Events can
alter the next round’s pace – a storm might reduce everyone to one action while
an adrenaline rush grants an extra move. Friendly survivors may appear with
supplies or medkits and, if there’s room, may even join your group. The wind
can momentarily lift the fog to reveal unexplored tiles. Rain muffles sound so
noise tokens are less likely to draw zombies in the following round. Heatwaves parch the survivors, causing extra hunger loss next turn. A sudden
blizzard both muffles noise and limits everyone to a single action with reduced
visibility on the next turn. Occasional earthquakes may raise or crumble rubble walls, reshaping the paths ahead. Exploring may also
uncover special locations. Pharmacies (`M`) have a high chance of yielding
  medkits while armories (`W`) are the best spots to find weapons. Hidden traps
  (`!`) may also appear and will injure any survivor that triggers them, though
  they can destroy zombies as well. Survivors can also rig traps or build
  temporary campfires (`C`) of their own; fires grant extra healing when resting
  and shed light that reveals adjacent tiles each round but fade after a few
  rounds. Shelters (`U`) are permanent safe spots that grant the same rest
  bonus. Traps may be disarmed to recover supplies. Once revealed, their
  symbols remain on the board. Rubble walls (`#`) are impassable obstacles that
  block movement for both survivors and zombies, forcing careful navigation.
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

  Dropped items remain on the board: supplies show as `R`, medkits as `H`, weapons as `G` and molotovs as `L` once the tile is revealed. Built campfires appear as `C`; while lit they provide better rest and illuminate adjacent tiles but burn out after a few rounds. Permanent shelters are marked `U`.
Noise markers from loud actions show their remaining turns as numbers until they attract or fade.

Experience points accumulate across the campaign. Killing zombies and
surviving scenarios grant XP; each level reached permanently adds +1 to
maximum health for future runs.
Higher campaign levels also nudge up the zombie spawn rate to keep the
challenge growing. If no survivors escape a scenario, a small cache of
supplies carries over to your next attempt as a catch-up boost.

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
