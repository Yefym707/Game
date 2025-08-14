# Gamecore

## Installation

```bash
pip install -r requirements.txt
```

## Local build: PyInstaller & Versioning

The project version is derived from git tags via `tools/versioning.py`. When no tags are present it falls back to `0.0.0+dev`.

To create a standalone executable for the current platform:

```bash
python tools/build_pyinstaller.py --target linux
```

Replace `linux` with `win` or `mac` as needed. The binary will be placed in `dist/<platform>/`. To assemble a distribution staging area:

```bash
python tools/package_release.py --target linux
```

This gathers the built binary and runtime resources in `build/staging/<platform>/`.

## Runtime tools shim

Release builds do not ship with the development helpers found in the top level
`tools/` directory.  A lightweight package under `src/tools` provides a safe
shim so `import tools` always succeeds.  When matching modules exist in the
`tools/` folder they are imported transparently; otherwise the shim returns
no‑op placeholders and logs a warning.  This keeps production builds small
while still allowing optional helpers during development.


## CI: Artifacts & Steam Upload

Pushing a git tag runs the `Release` workflow. It builds PyInstaller executables for Windows, macOS and Linux, packages the staging directory and uploads a zipped artifact named `Game-<os>-<tag>.zip`.

The `Steam Upload` workflow is triggered manually. It downloads the chosen artifact, unpacks it into `build/staging/<platform>/` and calls `scripts/steam_upload.py`. Steam credentials and depot IDs are read from GitHub Secrets.

## CLI

```bash
python -m scripts.run_cli --seed 123
```

## GUI

```bash
python -m scripts.run_gui
```

## Controls & Turn Flow

The playable prototype supports a tiny subset of the final game's controls:

* **LMB** – select a unit or target
* **RMB** – move to a cell or attack an enemy
* **Space** – end the current turn
* **Esc** – pause
* **F1** – toggle a help overlay with the current bindings

### Keybinds

Custom key bindings are stored in `~/.oko_zombie/config.json` under the
`"keybinds"` section. They can be changed in the **Settings** menu via the
corresponding buttons.

The rules module tracks action points and validates that moves stay within
range and do not pass through walls.  Failed actions return a localised reason
which the client displays as a small toast message so the player knows why an
order was rejected.  Successful actions append a short entry to the event log
(``Move``, ``Hit`` or ``End Turn``).

## Game Flow

The title screen renders a visible menu navigable with the arrow keys or the
mouse. A hint at the bottom reminds players that *Enter* or a left click selects
the highlighted item. The available actions are:

* **New Game** – opens a lightweight setup wizard where the mode, player count,
  names, difficulty and random seed can be adjusted.
* **Continue** – resumes the most recent save when a valid slot exists. If the
  last save is missing or malformed a dialog explains the issue and the wizard
  opens instead of starting an empty match.
* **Load** – lists all save slots with turn, difficulty and seed information
  and allows deleting or loading a specific slot.
* **Settings** – opens the configuration scene.
* **Exit** – quits the application.

## Crash Handling & Logs

Unexpected exceptions are written to
`%USERPROFILE%\.oko_zombie\logs\app.log` with log rotation (1 MB ×3).  A modal
dialog displays the error type and the last twenty lines of the stack trace and
offers a **Copy details** button that copies the full traceback to the
clipboard for easy bug reports.

## Safe Mode

Safe mode starts the game with heavy post effects, audio and online features
disabled and loads a lightweight high‑contrast theme.  Enable it via:

```bash
python -m scripts.run_gui --safe
```

or set the environment variable `GAME_SAFE_MODE=1`.

## Stability: Saves & Localization

Save files are written atomically using a temporary file and the previous
version is copied to `~/.oko_zombie/backups/<date>/` before being replaced.
Loading verifies size and checksum metadata so corrupted files trigger a
dialog and the **Continue** button falls back to **New Game** when no valid
save is present.

Localization lookups use `safe_get()` which falls back to the default language
and logs missing keys only once without interrupting gameplay.

## Borders & Highlights

UI elements use three border widths (`border_xs`, `border_sm`, `border_md`) and
rounded corners (`radius_sm`, `radius_md`, `radius_lg`). Highlight colors are
drawn from the active theme's `palette.ui` (`neutral`, `accent`, `danger`,
`warn`, `info`) ensuring consistent visuals across themes and scales.

## Night Vignette & High-Contrast Theme

Night scenes can optionally apply a soft vignette to gently darken the edges
of the screen.  The effect strength is adjustable via *Vignette at night* in
the accessibility settings.  A dedicated *High Contrast* theme provides dark
backgrounds, bright text and amber/blue accents alongside subtle shadow layers
to improve readability and accessibility.

## Readable UI: Panels & Minimap

The interface arranges information in scalable side panels. The left panel
shows the active unit with name, health and action points while the right side
hosts the event log and a colour coded minimap. All elements respect the global
UI scale (1.0–2.0) for legible text on both 1080p and 1366×768 displays. The
minimap highlights terrain types, players and zombies and draws a rectangle for
the current camera view; clicking it jumps the camera to the selected cell.

## Loading Screen

The client boots into a dedicated loading scene. Locales, configuration files,
tiles and fonts are prepared by an ``AsyncLoader`` which processes tasks in
small time-sliced batches each frame so the window never freezes. Progress is
shown as a percentage alongside random gameplay tips. Once all tasks complete
the application transitions to the main menu.

## Multiplayer

The project supports both local and online multiplayer.  Local co-op allows
2–4 players to take alternating turns on the same machine and works entirely
offline.  Online games use a small asyncio based websocket server which
broadcasts authoritative state updates to connected clients.  All random number
generation happens on the server to keep sessions deterministic while the
pygame client simply renders the received state.

### Online UX: Ready, Ping, Reconnect & Invite Management

Online lobbies track a ready flag per player and the match can only start once
everyone toggles ready.  Clients send periodic ping messages to measure and
display round-trip latency in milliseconds.  When a connection drops the client
automatically retries with an exponential backoff and shows a reconnecting
overlay which can be cancelled.  Invite links can be refreshed with a new
signature or revoked entirely if access should be removed.

### Online: Rejoin & Spectator

Players receive a *rejoin token* when joining a room. If their connection drops
the client uses this token to reclaim the original slot and receives a full
state snapshot. Lobbies may optionally allow late **drop‑in** joins and
spectator connections. Spectators can watch with camera control and access to
the log but cannot issue actions. Participants can vote to pause the game; a
majority vote pauses or resumes the tick loop.

## Balance

Core combat and spawn values are configured in `data/balance.json`. The loader
validates the numbers and applies difficulty presets defined in
`gamecore.rules` so tests and saved games remain deterministic across
environments.

## Scenarios

Campaign layouts and starting conditions live in `data/scenarios.json`.
Selecting the *short*, *medium* or *long* scenario loads the specified map,
distributes starting items and switches the global difficulty accordingly.

## Save versions

Every save file includes a `save_version` field. When an old save is loaded the
module `gamecore.save_migrations` upgrades it step by step until it matches the
current format, ensuring long term compatibility.

## Cloud Save Conflicts & Backups

Saves are written atomically and the previous version is always copied to
`~/.oko_zombie/backups/<date>/` before being replaced. When a cloud save
differs from the local copy the game compares metadata such as modification
time, size and checksum. Depending on the configured policy the newer version
is chosen automatically or a dialog lets the player pick the desired file and
optionally set a default preference.

## Safe Saves & Profiling

Save operations are atomic and the previous file is backed up to
``~/.oko_zombie/backups/<date>/`` before being replaced.  Automatic saves run
every N turns as configured by ``autosave_interval_turns`` in
``config.json``.  When ``enable_profiling`` is set, running
``tools/profiler_trace.py`` on the generated trace produces
``profiler_report.json`` summarising average FPS, the 95th percentile frame
time and how much time was spent in each subsystem.

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

## UI Themes & Minimap

The client supports multiple visual themes – light, dark and an "apocalypse"
variant. Themes can be switched at runtime from the settings screen and all
panels, buttons and hints update instantly. Panels animate into view by sliding
from the sides while fading in.

A optional minimap gives a quick overview of the board. It encodes tile types
by color, marks the current camera viewport and allows clicking to jump the
camera. Both the visibility and size of the minimap are configurable.

## Minimap 2.0 & Scene Transitions

The minimap now ships with a legend clarifying tile colors, a frame showing the
current viewport and clickable navigation that centers the camera on the chosen
cell. Small unicode markers highlight events such as players or zombies. Scene
changes between the menu, game and settings employ short fade or slide
transitions for a smoother flow.

## Accessibility & Controller

The settings menu now exposes an Accessibility tab. It offers an extended UI
scale slider, a high-contrast theme, optional subtitles and a dyslexia-friendly
font mode that increases letter spacing. The game auto-detects keyboard layout,
supports full gamepad mappings with optional vibration feedback and can invert
zoom direction. Press **F1** or the controller's **Select** button to display an
on-screen help overlay listing current bindings.

## Visual & UX Polish

Camera motion is smoothed with a small deadzone so the view glides when the
active unit moves. The mouse wheel zooms toward the cursor and subtle screen
shake triggers on impacts. Movement and attack ranges use different highlight
styles and preview paths are drawn with dotted lines. Damage or healing values
float upward and stack vertically to avoid overlap.

Lighting, weather and post effects (vignette, desaturation, bloom and color
curves) are controlled from the **Settings** menu. Each effect exposes an
intensity slider and can be disabled entirely if performance drops. Turning off
post-processing or lowering weather intensity helps maintain a steady 60 FPS on
mid‑range laptops.

## Performance Presets & UX

Tiles are packed into a cached atlas on load so no textures are generated
during gameplay. Post effects can be switched between **OFF**, **BALANCED** and
**HIGH** presets – the OFF preset performs a direct buffer copy for the fastest
possible rendering. Press **Esc** to open a small pause menu with *Resume*,
*Restart*, *Settings* and *Exit* actions. Transient toast messages, tooltips and
modal confirmation dialogs provide unobtrusive feedback throughout the
interface.

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

### Controls

The default input scheme is intentionally small and geared towards mouse play:

* **LMB** – select
* **RMB** – move / attack
* **Space** – end turn
* **Esc** – pause
* **F1** – show help

Bindings are defined centrally in ``src/client/input_map.py`` and later patches
may add a settings screen for rebinding.

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

## Events & Scenarios

Random encounters are described in `data/events.json` and may trigger at the
start of a player's turn. Each event defines conditions, effects and a small
unicode icon shown in the log. Scenarios in `data/scenarios.json` configure
short, medium and long campaigns with their own goals, starting items and
difficulty. The chosen scenario loads the specified map and applies its
parameters when a new game begins.

## Audio System & SFX

Short sound effects are generated procedurally using ``numpy`` and converted to
``pygame`` sounds at runtime.  Three effect channels – footsteps, hits and UI –
each have individual volume controls plus a global master level.  An ADSR
envelope provides gentle fades so tones start and end smoothly without clicks.
Volumes can be adjusted in the **Settings** menu and are applied immediately.

## Stability & Debug

The client logs fatal errors to ``~/.oko_zombie/logs/app.log``.  The file is
rotated when it grows beyond ~256 KB.  Run the game with Python's ``-O`` flag to
disable additional validation; in normal mode invariant checks may raise
exceptions to help diagnose corrupt saves or illegal moves.

## UX polish & Difficulty Presets

The client features small touches to make the board feel alive: movement and
attack ranges are highlighted, paths previewed with dotted lines and actions
queued as non-blocking animations. A compact side log displays recent events
with tiny unicode icons and can be collapsed when screen space is tight.

Before starting a match the player may select between **Easy**, **Normal** and
**Hard** difficulty. Each preset adjusts enemy aggression, loot chances, damage
and spawn rates. Restarts are gated behind a configuration flag and reuse the
original random seed for deterministic sessions.

## Cinematic Camera & Layers

A smooth camera follows the active player with configurable inertia and bounds.
Zooming centers on the mouse cursor and can range between 0.75× and 2×. Combat
events trigger subtle screen shake which stacks across impacts. Rendering is
split into ordered layers – background, tiles, entities and overlays – before
the UI is composited on top.

## Lighting & Day/Night

A lightweight lightmap simulates illumination. Each tile stores an intensity
value which is blurred with a small Gaussian kernel for soft edges. Players,
campfires and lamps act as light sources with a subtle noise driven flicker.
The lightmap is blended multiplicatively over the scene and tinted depending on
the current time of day. A simple cycle transitions through day, dusk, night
and dawn adjusting both color temperature and ambient brightness.

## Weather FX

Basic weather effects add atmosphere without relying on external assets.  Rain
and snow use a small particle system influenced by a configurable wind vector
while fog draws a pulsating noise based overlay.  Scenarios or configuration
options can enable or disable weather and adjust its default intensity.

## Post FX & Performance

The rendering pipeline can apply a small stack of post effects directly on
``pygame`` surfaces. Available options include a vignette, simple desaturation,
an RGB color matrix and a lightweight bloom achieved through downsampling and a
box blur.  Individual effects and their intensities can be toggled in the
settings menu and persist via ``config.json``. A configurable FPS cap limits the
main loop and an optional overlay displays frame time, draw calls and the time
spent on post-processing. Press **F3** at any time to toggle this overlay.

## Photo Mode & Screenshots

Press **F10** in-game to pause time and enter a free camera mode. The mouse and
W/A/S/D keys pan the view while **H** toggles the UI overlay. Capture the
current frame with **F12** – images are stored as PNG files under
`~/.oko_zombie/screenshots/` and include the session's seed in their filename.
When running the demo build a semi-transparent watermark is added
automatically.

## Telemetry & Crash Reports (Opt-in)

The game can optionally send anonymous telemetry events and crash reports to a
user configurable HTTP endpoint. Collection is disabled by default. Enable it
in the **Settings** screen and specify the endpoint. When the endpoint is
unreachable, events are stored under ``~/.oko_zombie/telemetry`` and retried
with exponential backoff on the next launch. Crash reports are written to
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
playback.  If the environment variable ``REPLAY_HMAC_KEY`` is set, recordings
are appended with an HMAC signature and the player verifies it on load.

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
register, send periodic heartbeats and unregister on shutdown.  The service
also exposes a simple ``/list`` HTTP endpoint returning JSON lobby data.
Clients can query the master via the **Browse** tab in the online menu which
lists available servers and displays basic metadata.

## Anti-Cheat, Validation & Moderation

The server validates incoming actions and rejects unsupported or out-of-bounds
requests with human readable error messages. A JSON based ban list stored in
``data/banlist.json`` allows temporary or permanent bans, and players can file
reports which are written to ``data/reports/`` for later review. Replays are
signed with HMAC and verified during playback.

## Determinism & Tests

The engine uses a single random number generator whose state is serialised in
save files. Loading a game restores the sequence so sessions remain
reproducible across runs. A small test-suite verifies deterministic behaviour,
movement bounds and save/load round-trips.

```bash
pytest -q
```

## Steamworks Integration (Fallback if SDK missing)

Setting the ``STEAM_SDK_PATH`` environment variable enables a thin
``ctypes`` based wrapper around ``steam_api``.  When initialisation succeeds
the game exposes achievements, cloud saves, rich presence and overlay status.
If the SDK is missing or any call fails, a stub implementation keeps the game
running with all features silently disabled.

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

## Invites: Links, Codes & Steam Rich Presence

The online mode supports short invite codes and clickable links. When the
server is started with an ``INVITE_SECRET`` environment variable clients can
request an invite which contains the server address, room id and an expiration
timestamp.  The payload is signed with HMAC-SHA256 to prevent tampering.

Invites are formatted as ``oko://join?host=HOST&port=PORT&room=ROOM&code=CODE``
and can be shared directly or via the Steam overlay.  Clients may paste a link
or the short ``XXXX-YYYY`` code to connect without entering an address
manually.  When Steam is available the rich presence status exposes the invite
so friends can join through "Join Game".
