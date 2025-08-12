# Gamecore

## Installation

```bash
pip install -r requirements.txt
```

## CLI

```bash
python -m scripts.run_cli --seed 123
```

## GUI

```bash
python -m scripts.run_gui
```

## Demo Mode

A limited demo version is available. Launch it with the ``--demo`` flag:

```bash
python -m scripts.run_gui --demo
```

The demo restricts the campaign to three in-game days, a single map and
reduced loot drops. When the limit is reached an end screen offers a shortcut
to purchase the full version via the Steam overlay.

### Main Menu & Navigation

The GUI starts in a lightweight main menu rendered entirely with pygame. The
background features a procedurally animated parallax grid while game modes are
presented as selectable cards. Navigation supports both mouse and keyboard
input – use the arrow keys to move focus and **Enter** to activate a card.

Available cards currently include **Solo**, **Local Coop** and **Online**. A
separate **Continue** button resumes the latest save, and **Settings** opens
the configuration screen where volume, language and bindings can be adjusted.
Scene changes employ short fade transitions for a smooth experience.

## Saves & Config

Game data is stored inside the user's home directory in `~/.oko_zombie`.
Configuration options are kept in `config.json` and individual saves reside
in the `saves/` subdirectory.  The save files include a `save_version` field
so future releases can detect incompatible formats.

### Save File Versions & Migrations

Older save files are automatically upgraded when loaded.  The loader checks
the embedded `save_version` and applies any required migration functions in
sequence until the current version is reached.  Each migration is a pure and
deterministic transformation, ensuring existing saves remain compatible with
new releases.

From the game you can quick save with **F5** and quick load with **F9**. The
game also performs an automatic save after each turn.

The **Settings** menu exposes basic options like volume, language, window
size and fullscreen state.  Changing these values writes them to
`config.json` for the next session.

### Controls & Rebinding

Movement uses the arrow keys (or a gamepad's left stick) while actions such as
*End Turn*, *Rest* and *Scavenge* have their own keys.  In the settings screen
each action can be rebound; the chosen bindings are stored inside
`~/.oko_zombie/config.json` under the ``bindings`` section.

### Gamepad

The client will automatically enable the first detected gamepad via the
``pygame.joystick`` API.  Default mapping follows the common XInput layout – A
confirms/end turn, B cancels, X scavenges, Y rests and the left stick pans the
camera.

### Tutorial

On the very first launch a short interactive tutorial is shown explaining the
basics of movement and ending a turn.  Completing it clears the ``first_run``
flag in the configuration so it only appears once.

## Tiles pipeline

Tile graphics are generated from `textures.json`. Run the helper script to
build individual 64×64 tiles and an atlas:

```bash
python tools/build_tiles.py
```

The client also checks `assets/tiles/` on startup and will automatically
invoke this script if the directory is empty, producing fallback tiles from
the JSON mapping.

## Localization

Text shown by both the CLI and the GUI is translated via a simple JSON based
system. Locale files live in `data/locales/<lang>.json` and the desired
language is stored in `~/.oko_zombie/config.json` under the `"lang"` key.
Missing keys default to the lookup key itself.

## Telemetry & Crash Reports (Opt-in)

The game can optionally send anonymous telemetry events and crash reports to a
user configurable HTTP endpoint. Collection is disabled by default. Enable it
in the **Settings** screen and specify the endpoint. When the endpoint is
unreachable, events are stored under ``~/.oko_zombie/telemetry`` and retried on
the next launch. Crash reports are written to
``~/.oko_zombie/crashes`` regardless of connectivity and uploaded only when
opted in.

## Sandbox Editor & Balance JSON

A built-in sandbox editor lets you place tiles and experiment with custom maps.
Use the **Save Map**, **Load Map** and **Test Map** buttons to manage maps.
Saved layouts are written as JSON files under `mods/maps/` for easy sharing.

Core gameplay numbers such as loot chances or zombie stats are stored in
`data/balance.json`.  The game validates this file on load so modders can tweak
values while maintaining sane ranges.

## Replays (Record & Playback)

The engine contains a lightweight system to record deterministic sessions. When
`record_replays` is enabled in the configuration, completed matches are stored
as JSON lines under `~/.oko_zombie/replays`. The :mod:`replay.recorder` module
captures events and regular state checkpoints while
:mod:`replay.player` can load a file, seek to a specific turn and resume
playback.

### Local Co-op (Hot-Seat)

The game now supports a local co-op mode for 2–4 players sharing the same
screen. Players take turns on one device and the status panel highlights the
currently active survivor. Save files record the game mode and player order so
hot-seat sessions can be resumed later without losing track of whose turn it
is.

## Online mode (Server/Client)

An experimental online mode is included.  A lightweight authoritative server
built on ``asyncio`` and ``websockets`` keeps the official game state and
relays actions between players.  To start the server locally run:

```bash
python -m scripts.run_server --host 0.0.0.0 --port 8765
```

Clients connect through the **Online** option in the main menu.  The protocol
uses JSON messages with a small set of types such as ``HELLO``, ``ACTION`` and
``STATE``.  The implementation is intentionally minimal but provides a solid
foundation for further development.

## Master Server & Server Browser

A small discovery service allows public game servers to announce themselves so
players can join without manually typing IP addresses.  Run the master server
locally with:

```bash
python -m scripts.run_master --host 0.0.0.0 --port 8080
```

Game servers started with the ``--master`` option will automatically
register, send periodic heartbeats and unregister on shutdown.  Clients can
query the master via the **Browse** tab in the online menu which lists
available servers and displays basic metadata.

## Anti-Cheat, Validation & Moderation

The server validates actions and enforces per-IP rate limits. A JSON based ban list allows temporary or permanent bans. Replays are signed with HMAC and players may submit in-game reports stored on the server.

## Tests

```bash
pytest -q
```

## Steam Achievements & Cloud Saves

When the environment variable ``STEAM_SDK_PATH`` points to a Steamworks SDK
installation the game enables achievement tracking and uses
``ISteamRemoteStorage`` for saves.  Outside of Steam a small stub keeps the
game fully playable while simply ignoring these features.

## Build & Steam upload

Create platform-specific executables with PyInstaller:

```bash
pyinstaller tools/build_spec.win.spec
pyinstaller tools/build_spec.mac.spec
pyinstaller tools/build_spec.linux.spec
```

The resulting files are placed in the `dist/` directory.

To publish on Steam, set up depots for each platform in Steamworks and use SteamCMD to upload the builds. Each depot should reference the matching `dist` output. A simple upload command looks like:

```bash
steamcmd +login <user> +run_app_build path/to/app_build.vdf +quit
```

Replace `<user>` and the VDF path with your account and build script.
