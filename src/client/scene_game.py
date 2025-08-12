"""In-game scene handling rendering and input."""
from __future__ import annotations

import asyncio
import pygame
from typing import Any

from .app import Scene
from .gfx.tileset import TILE_SIZE, Tileset
from .gfx import anim
from .ui.widgets import IconLog, StatusPanel, PauseMenu, PopupDialog
from .input import InputManager
from . import sfx
from .net_client import NetClient
from gamecore import board as gboard
from gamecore import rules, saveio, config as gconfig, achievements
from gamecore import balance as gbalance, events as gevents, scenario as gscenario, i18n
from replay.recorder import Recorder

try:  # pragma: no cover - optional dependency
    import pygame.messagebox as messagebox
except Exception:  # pragma: no cover - fallback if missing
    messagebox = None


class GameScene(Scene):
    """Render the board and process user input."""

    def __init__(self, app, new_game: bool = True, net_client: NetClient | None = None) -> None:
        super().__init__(app)
        self.cfg = app.cfg
        self.input: InputManager = app.input
        self.tileset = Tileset()
        self.quick_path = gconfig.quicksave_path()
        self.autosave_path = gconfig.autosave_path()
        self.net_client = net_client
        if new_game:
            pconf = self.cfg.get("players")
            count = len(pconf) if isinstance(pconf, list) and pconf else 1
            mode = rules.GameMode.LOCAL_COOP if count > 1 else rules.GameMode.SOLO
            self.state = gboard.create_game(players=count, mode=mode)
            if isinstance(pconf, list):
                for pdata, player in zip(pconf, self.state.players):
                    player.name = pdata.get("name", player.name)
                    player.color = pdata.get("color", player.color)
            achievements.on_game_start(len(self.state.players))
        else:
            try:
                self.state = saveio.load_game(self.autosave_path)
            except Exception as exc:
                self.state = gboard.create_game()
                self._show_error(str(exc))
            achievements.on_game_start(len(self.state.players))
        rules.set_seed(0)
        self.balance = gbalance.load_balance()
        self.events = gevents.load_events()
        if new_game:
            scenarios = gscenario.load_scenarios()
            sid = self.cfg.get("scenario", "short")
            scen = scenarios.get(sid) or next(iter(scenarios.values()))
            gscenario.apply_scenario(self.state, scen)
        self._maybe_event()
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.scale = 1.0
        self.log = IconLog()
        self.status = StatusPanel()
        self._last_log = 0
        self.animations: list[Any] = []
        self.hover_tile: tuple[int, int] | None = None
        self.paused = False
        self.pause_menu: PauseMenu | None = None
        self.event_popup: PopupDialog | None = None
        self.input.set_profile(self.state.active)
        self.recorder: Recorder | None = None
        if self.cfg.get("record_replays"):
            path = gconfig.replay_dir() / "last.jsonl"
            self.recorder = Recorder(path)
            self.recorder.start({"seed": 0, "mode": self.state.mode.name})
            self.recorder.checkpoint(self.state)

    def _show_error(self, msg: str) -> None:
        """Display an error message without crashing."""

        if messagebox:
            try:
                messagebox.show("Error", msg)
                return
            except Exception:  # pragma: no cover - fallback
                pass
        # Fallback to console/log output
            print("Error:", msg)
        if hasattr(self, "log"):
            self.log.add("!", msg)

    def _maybe_event(self) -> None:
        """Trigger a random event if conditions allow."""

        ev = gevents.maybe_trigger(self.state, self.balance)
        if not ev:
            return
        w, h = self.app.screen.get_size()
        rect = pygame.Rect(w // 2 - 150, h // 2 - 100, 300, 180)

        def make_cb(effect):
            def _cb() -> None:
                gevents.apply_effect(self.state, effect)
                self.event_popup = None
            return _cb

        choices = [(i18n.gettext(e.text_key), make_cb(e)) for e in ev.effects]
        self.event_popup = PopupDialog(
            rect,
            ev.icon,
            i18n.gettext(ev.title_key),
            i18n.gettext(ev.desc_key),
            choices,
        )
        self.log.add(ev.icon, i18n.gettext(ev.title_key))

    def _open_pause_menu(self) -> None:
        """Create the pause menu overlay."""

        if not self.paused:
            w, h = self.app.screen.get_size()
            rect = pygame.Rect(w // 2 - 150, h // 2 - 120, 300, 220)
            callbacks = {
                "resume": self._resume,
                "restart": self._restart,
                "settings": self._goto_settings,
                "exit": self._exit_to_menu,
            }
            self.pause_menu = PauseMenu(rect, callbacks)
            self.paused = True

    def _resume(self) -> None:
        self.paused = False

    def _goto_settings(self) -> None:
        from .scene_settings import SettingsScene

        self.next_scene = SettingsScene(self.app)

    def _exit_to_menu(self) -> None:
        from .scene_menu import MenuScene

        if self.recorder:
            self.recorder.stop()
        self.next_scene = MenuScene(self.app)

    def _restart(self) -> None:
        self.state = saveio.restart_state(self.state, 0, self.cfg)
        self.log.entries.clear()
        self._last_log = 0
        self.input.set_profile(self.state.active)
        self.paused = False

    # event handling ---------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if self.event_popup:
            self.event_popup.handle_event(event)
            return
        if self.paused:
            if self.pause_menu:
                self.pause_menu.handle_event(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.paused = False
            return
        if event.type == pygame.MOUSEMOTION:
            tile_size = int(TILE_SIZE * self.scale)
            x = int((event.pos[0] + self.camera_x) // tile_size)
            y = int((event.pos[1] + self.camera_y) // tile_size)
            self.hover_tile = (x, y)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._open_pause_menu()
                return
            action = self.input.action_from_key(event.key)
            if action == "pause":
                self._open_pause_menu()
            elif action == "end_turn":
                if self.state.mode == rules.GameMode.ONLINE and self.net_client:
                    asyncio.create_task(self.net_client.send({"t": "ACTION", "p": {"end_turn": True}}))
                else:
                    gboard.end_turn(self.state)
                    if self.recorder:
                        self.recorder.record({"type": "END_TURN", "turn": self.state.turn})
                        self.recorder.checkpoint(self.state)
                    self.input.set_profile(self.state.active)
                    try:
                        saveio.save_game(self.state, self.autosave_path)
                    except Exception as exc:
                        self._show_error(str(exc))
                    self._maybe_event()
            elif action == "quick_save":
                if self.state.mode != rules.GameMode.ONLINE:
                    try:
                        saveio.save_game(self.state, self.quick_path)
                    except Exception as exc:
                        self._show_error(str(exc))
            elif action == "quick_load":
                if self.state.mode != rules.GameMode.ONLINE:
                    try:
                        self.state = saveio.load_game(self.quick_path)
                        self.log.entries.clear()
                        self._last_log = 0
                        self.input.set_profile(self.state.active)
                    except Exception as exc:
                        self._show_error(str(exc))
            elif action in ("move_up", "move_down", "move_left", "move_right"):
                self._handle_move(action)
            elif action == "rest":
                self.state.add_log("rest")
                achievements.on_campaign_win()
            elif action == "scavenge":
                self.state.add_log("scavenge")
        elif event.type == pygame.MOUSEWHEEL:
            self.scale *= 1.25 if event.y > 0 else 0.8
            self.scale = max(0.75, min(2.0, self.scale))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.log.handle_event(event)
            self._handle_click(event.pos)

    def _handle_move(self, action: str) -> None:
        mapping = {
            "move_up": "w",
            "move_down": "s",
            "move_left": "a",
            "move_right": "d",
        }
        if self.state.mode == rules.GameMode.ONLINE and self.net_client:
            asyncio.create_task(
                self.net_client.send({"t": "ACTION", "p": {"move": mapping[action]}})
            )
        else:
            player = self.state.players[self.state.active]
            old = (player.x, player.y)
            if gboard.player_move(self.state, mapping[action]):
                if self.recorder:
                    self.recorder.record(
                        {
                            "type": "MOVE",
                            "turn": self.state.turn,
                            "player": self.state.active,
                            "dir": mapping[action],
                        }
                    )
                tile = self.tileset.get(player.symbol)
                if tile:
                    size = int(TILE_SIZE * self.scale)
                    img = pygame.transform.scale(tile, (size, size)) if size != TILE_SIZE else tile
                    start = (old[0] * size - self.camera_x, old[1] * size - self.camera_y)
                    end = (player.x * size - self.camera_x, player.y * size - self.camera_y)
                    self.animations.append(anim.Slide(img, start, end, 0.2))
                sfx.play_step()

    def _handle_click(self, pos) -> None:
        mx, my = pos
        tile_size = int(TILE_SIZE * self.scale)
        x = int((mx + self.camera_x) // tile_size)
        y = int((my + self.camera_y) // tile_size)
        if self.state.board.in_bounds(x, y):
            msg = f"clicked {(x, y)}"
            self.state.add_log(msg)
            sfx.play_hit()
            achievements.on_zombie_kill()
            sx = x * tile_size - self.camera_x + tile_size // 2
            sy = y * tile_size - self.camera_y
            self.animations.append(anim.FloatText("+1", (sx, sy)))

    # update / draw ----------------------------------------------------
    def update(self, dt: float) -> None:
        if rules.DEMO_MODE and self.state.turn >= rules.DEMO_MAX_DAYS:
            from .scene_demo_end import DemoEndScene

            self.next_scene = DemoEndScene(self.app)
            return
        pressed = pygame.key.get_pressed()
        speed = 400 * dt
        if pressed[pygame.K_w]:
            self.camera_y -= speed
        if pressed[pygame.K_s]:
            self.camera_y += speed
        if pressed[pygame.K_a]:
            self.camera_x -= speed
        if pressed[pygame.K_d]:
            self.camera_x += speed
        if len(self.state.log) > self._last_log:
            for msg in self.state.log[self._last_log :]:
                self.log.add("·", msg)
            self._last_log = len(self.state.log)
        for a in list(self.animations):
            if a.update(dt):
                self.animations.remove(a)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        tile_size = int(TILE_SIZE * self.scale)
        board = self.state.board
        for y, row in enumerate(board.tiles):
            for x, ch in enumerate(row):
                tile = self.tileset.get(ch)
                if tile:
                    if tile_size != TILE_SIZE:
                        img = pygame.transform.scale(tile, (tile_size, tile_size))
                    else:
                        img = tile
                    sx = x * tile_size - self.camera_x
                    sy = y * tile_size - self.camera_y
                    surface.blit(img, (sx, sy))
        # highlights
        self._draw_highlights(surface, tile_size)
        # entities
        for p in self.state.players:
            self._draw_entity(surface, p, tile_size)
        for z in self.state.zombies:
            self._draw_entity(surface, z, tile_size)
        # animations overlay
        for a in self.animations:
            if hasattr(a, "draw"):
                a.draw(surface)
        # UI
        w, h = surface.get_size()
        log_rect = pygame.Rect(w - 200, 0, 200, h)
        self.log.draw(surface, log_rect)
        self.status.draw(surface, self.state)
        if self.event_popup:
            self.event_popup.draw(surface)
        if self.paused and self.pause_menu:
            self.pause_menu.draw(surface)

    def _draw_entity(self, surface: pygame.Surface, ent, tile_size: int) -> None:
        tile = self.tileset.get(ent.symbol)
        if tile:
            if tile_size != TILE_SIZE:
                img = pygame.transform.scale(tile, (tile_size, tile_size))
            else:
                img = tile
            sx = ent.x * tile_size - self.camera_x
            sy = ent.y * tile_size - self.camera_y
            surface.blit(img, (sx, sy))

    def _draw_highlights(self, surface: pygame.Surface, tile_size: int) -> None:
        player = self.state.players[self.state.active]
        px, py = player.x, player.y
        for dx, dy in rules.DIRECTIONS.values():
            tx, ty = px + dx, py + dy
            rect = pygame.Rect(
                tx * tile_size - self.camera_x,
                ty * tile_size - self.camera_y,
                tile_size,
                tile_size,
            )
            pygame.draw.rect(surface, (0, 255, 0), rect, 1)
        for z in self.state.zombies:
            if abs(z.x - px) + abs(z.y - py) == 1:
                rect = pygame.Rect(
                    z.x * tile_size - self.camera_x,
                    z.y * tile_size - self.camera_y,
                    tile_size,
                    tile_size,
                )
                pygame.draw.rect(surface, (255, 0, 0), rect, 2)
        if self.hover_tile:
            path = self._simple_path((px, py), self.hover_tile)
            for step in path:
                cx = step[0] * tile_size - self.camera_x + tile_size // 2
                cy = step[1] * tile_size - self.camera_y + tile_size // 2
                pygame.draw.circle(surface, (255, 255, 0), (cx, cy), 3)

    def _simple_path(self, start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
        x, y = start
        tx, ty = end
        path = []
        while (x, y) != (tx, ty):
            if x < tx:
                x += 1
            elif x > tx:
                x -= 1
            elif y < ty:
                y += 1
            elif y > ty:
                y -= 1
            path.append((x, y))
            if len(path) > 100:
                break
        return path
