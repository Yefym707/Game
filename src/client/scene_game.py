"""In-game scene handling rendering and input."""
from __future__ import annotations

import asyncio
import pygame
from typing import Any

from .app import Scene
from .gfx.tileset import TILE_SIZE, Tileset
from .gfx import anim
from .gfx.camera import SmoothCamera
from .gfx.layers import Layer
from .gfx.lighting import LightMap
from .gfx import weather as gweather
from .ui.widgets import (
    IconLog,
    StatusPanel,
    PauseMenu,
    PopupDialog,
    ToastManager,
    hover_hints,
)
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
        scen = None
        if new_game:
            scenarios = gscenario.load_scenarios()
            sid = self.cfg.get("scenario", "short")
            scen = scenarios.get(sid) or next(iter(scenarios.values()))
            gscenario.apply_scenario(self.state, scen)
        self._maybe_event()
        board = self.state.board
        w_px = board.width * TILE_SIZE
        h_px = board.height * TILE_SIZE
        self.camera = SmoothCamera(
            app.screen.get_size(),
            (w_px, h_px),
            self.cfg.get("camera_follow_speed", 5.0),
            self.cfg.get("camera_zoom_speed", 0.25),
            self.cfg.get("camera_shake_scale", 1.0),
        )
        player = self.state.players[self.state.active]
        self.camera.follow(
            (player.x * TILE_SIZE + TILE_SIZE / 2, player.y * TILE_SIZE + TILE_SIZE / 2)
        )
        self.log = IconLog()
        self.status = StatusPanel()
        self._last_log = 0
        self.animations: list[Any] = []
        self.hover_tile: tuple[int, int] | None = None
        self.paused = False
        self.pause_menu: PauseMenu | None = None
        self.event_popup: PopupDialog | None = None
        self.toasts = ToastManager()
        self.input.set_profile(self.state.active)
        self.recorder: Recorder | None = None
        if self.cfg.get("record_replays"):
            path = gconfig.replay_dir() / "last.jsonl"
            self.recorder = Recorder(path)
            self.recorder.start({"seed": 0, "mode": self.state.mode.name})
            self.recorder.checkpoint(self.state)
        self.lightmap = LightMap(board.width, board.height)
        self.time_phase = rules.current_time_of_day()
        # weather ------------------------------------------------------
        self.weather = None
        if self.cfg.get("weather_enabled", True):
            wtype = getattr(self.state, "weather", None)
            intensity = getattr(
                self.state, "weather_intensity", self.cfg.get("weather_intensity", 1.0)
            )
            wind = getattr(self.state, "wind", (0.0, 0.0))
            if not wtype:
                wtype = rules.RNG.choice(["rain", "snow", "fog"])
            size = self.app.screen.get_size()
            if wtype == "rain":
                self.weather = gweather.Rain(size, intensity, wind)
            elif wtype == "snow":
                self.weather = gweather.Snow(size, intensity, wind)
            elif wtype == "fog":
                self.weather = gweather.Fog(size, intensity, wind)
            self.state.weather = wtype
            self.state.weather_intensity = intensity
            self.state.wind = wind
        # minimap ------------------------------------------------------
        self.minimap_enabled = self.cfg.get("minimap_enabled", True)
        self.minimap_size = self.cfg.get("minimap_size", 200)
        self._minimap_rect: pygame.Rect | None = None
        if self.minimap_enabled:
            self._build_minimap()

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
        msg = i18n.gettext(ev.title_key)
        self.log.add(ev.icon, msg)
        self.toasts.show(msg)

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
        if self.minimap_enabled and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._minimap_rect and self._minimap_rect.collidepoint(event.pos):
                mx = event.pos[0] - self._minimap_rect.x
                my = event.pos[1] - self._minimap_rect.y
                tx = mx / self.minimap_scale * TILE_SIZE
                ty = my / self.minimap_scale * TILE_SIZE
                self.camera.follow((tx, ty))
                return
        if event.type == pygame.MOUSEMOTION:
            wx, wy = self.camera.screen_to_world(event.pos)
            x = int(wx // TILE_SIZE)
            y = int(wy // TILE_SIZE)
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
            self.camera.zoom_at(event.y, event.pos)
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
                    size = int(TILE_SIZE * self.camera.zoom)
                    img = (
                        pygame.transform.scale(tile, (size, size))
                        if size != TILE_SIZE
                        else tile
                    )
                    start = self.camera.world_to_screen((old[0] * TILE_SIZE, old[1] * TILE_SIZE))
                    end = self.camera.world_to_screen((player.x * TILE_SIZE, player.y * TILE_SIZE))
                    self.animations.append(anim.Slide(img, start, end, 0.2))
                sfx.play_step()

    def _handle_click(self, pos) -> None:
        wx, wy = self.camera.screen_to_world(pos)
        x = int(wx // TILE_SIZE)
        y = int(wy // TILE_SIZE)
        if self.state.board.in_bounds(x, y):
            msg = f"clicked {(x, y)}"
            self.state.add_log(msg)
            sfx.play_hit()
            achievements.on_zombie_kill()
            sx, sy = self.camera.world_to_screen((x * TILE_SIZE, y * TILE_SIZE))
            size = int(TILE_SIZE * self.camera.zoom)
            self.animations.append(anim.FloatText("+1", (sx + size // 2, sy)))
            self.camera.shake(0.2, 5.0, 25.0)

    # update / draw ----------------------------------------------------
    def update(self, dt: float) -> None:
        if rules.DEMO_MODE and self.state.turn >= rules.DEMO_MAX_DAYS:
            from .scene_demo_end import DemoEndScene

            self.next_scene = DemoEndScene(self.app)
            return
        player = self.state.players[self.state.active]
        self.camera.follow(
            (player.x * TILE_SIZE + TILE_SIZE / 2, player.y * TILE_SIZE + TILE_SIZE / 2)
        )
        self.camera.update(dt)
        if len(self.state.log) > self._last_log:
            for msg in self.state.log[self._last_log :]:
                self.log.add("·", msg)
            self._last_log = len(self.state.log)
        for a in list(self.animations):
            if a.update(dt):
                self.animations.remove(a)
        phase = rules.update_time_of_day(dt)
        if phase != self.time_phase:
            self.time_phase = phase
            key = getattr(i18n, phase.name, None)
            if key:
                self.log.add("·", i18n.gettext(key))
        if self.weather:
            self.weather.update(dt)
        if self.pause_menu:
            self.pause_menu.update(dt)
        if self.event_popup:
            self.event_popup.update(dt)
        self.toasts.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        w, h = surface.get_size()
        layers = {layer: pygame.Surface((w, h), pygame.SRCALPHA) for layer in Layer}
        layers[Layer.BACKGROUND].fill((0, 0, 0))
        self.tileset.draw_map(self.state.board, self.camera, layers)
        self._draw_highlights(layers[Layer.OVERLAY])
        for p in self.state.players:
            self._draw_entity(layers[Layer.ENTITY], p)
        for z in self.state.zombies:
            self._draw_entity(layers[Layer.ENTITY], z)
        for a in self.animations:
            if hasattr(a, "draw"):
                a.draw(layers[Layer.OVERLAY])
        for layer in (Layer.BACKGROUND, Layer.TILE, Layer.ENTITY, Layer.OVERLAY):
            surface.blit(layers[layer], (0, 0))
        self._apply_lighting(surface)
        if self.weather:
            self.weather.draw(surface, (self.camera.x, self.camera.y))
        log_rect = pygame.Rect(w - 200, 0, 200, h)
        self.log.draw(surface, log_rect)
        self.status.draw(surface, self.state)
        if self.event_popup:
            self.event_popup.draw(surface)
        if self.paused and self.pause_menu:
            self.pause_menu.draw(surface)
        self._draw_minimap(surface)
        self.toasts.draw(surface)
        hover_hints.draw(surface)

    def _build_minimap(self) -> None:
        board = self.state.board
        scale = self.minimap_size / max(board.width, board.height)
        self.minimap_scale = scale
        surf = pygame.Surface((int(board.width * scale), int(board.height * scale)))
        for y, row in enumerate(board.tiles):
            for x, tile in enumerate(row):
                color = self._tile_color(tile)
                rect = pygame.Rect(int(x * scale), int(y * scale), int(scale) + 1, int(scale) + 1)
                surf.fill(color, rect)
        self._minimap_surface = surf

    def _tile_color(self, tile: str) -> tuple[int, int, int]:
        if tile == ".":
            return (60, 60, 60)
        if tile == "#":
            return (100, 100, 100)
        if tile == "T":
            return (0, 120, 0)
        if tile == "W":
            return (0, 0, 120)
        return (120, 120, 120)

    def _draw_minimap(self, surface: pygame.Surface) -> None:
        if not self.minimap_enabled:
            return
        mm = self._minimap_surface.copy()
        view_rect = pygame.Rect(
            self.camera.x / TILE_SIZE * self.minimap_scale,
            self.camera.y / TILE_SIZE * self.minimap_scale,
            (self.camera.screen_w / self.camera.zoom) / TILE_SIZE * self.minimap_scale,
            (self.camera.screen_h / self.camera.zoom) / TILE_SIZE * self.minimap_scale,
        )
        pygame.draw.rect(mm, (255, 0, 0), view_rect, 1)
        x = surface.get_width() - mm.get_width() - 10
        y = 10
        self._minimap_rect = pygame.Rect(x, y, mm.get_width(), mm.get_height())
        surface.blit(mm, (x, y))

    def _draw_entity(self, surface: pygame.Surface, ent) -> None:
        tile = self.tileset.get(ent.symbol)
        if tile:
            size = int(TILE_SIZE * self.camera.zoom)
            img = (
                pygame.transform.scale(tile, (size, size))
                if size != TILE_SIZE
                else tile
            )
            sx, sy = self.camera.world_to_screen((ent.x * TILE_SIZE, ent.y * TILE_SIZE))
            surface.blit(img, (sx, sy))

    def _draw_highlights(self, surface: pygame.Surface) -> None:
        tile_size = int(TILE_SIZE * self.camera.zoom)
        player = self.state.players[self.state.active]
        px, py = player.x, player.y
        for dx, dy in rules.DIRECTIONS.values():
            tx, ty = px + dx, py + dy
            sx, sy = self.camera.world_to_screen((tx * TILE_SIZE, ty * TILE_SIZE))
            rect = pygame.Rect(sx, sy, tile_size, tile_size)
            pygame.draw.rect(surface, (0, 255, 0), rect, 1)
        for z in self.state.zombies:
            if abs(z.x - px) + abs(z.y - py) == 1:
                sx, sy = self.camera.world_to_screen((z.x * TILE_SIZE, z.y * TILE_SIZE))
                rect = pygame.Rect(sx, sy, tile_size, tile_size)
                pygame.draw.rect(surface, (255, 0, 0), rect, 2)
        if self.hover_tile:
            path = self._simple_path((px, py), self.hover_tile)
        for step in path:
            sx, sy = self.camera.world_to_screen((step[0] * TILE_SIZE, step[1] * TILE_SIZE))
            pygame.draw.circle(
                surface, (255, 255, 0), (sx + tile_size // 2, sy + tile_size // 2), 3
            )

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

    # lighting -----------------------------------------------------------
    def _ambient_for_phase(self) -> float:
        mapping = {
            rules.TimeOfDay.DAY: 1.0,
            rules.TimeOfDay.DUSK: 0.7,
            rules.TimeOfDay.NIGHT: 0.3,
            rules.TimeOfDay.DAWN: 0.7,
        }
        return mapping.get(self.time_phase, 1.0)

    def _color_for_phase(self) -> tuple[int, int, int]:
        mapping = {
            rules.TimeOfDay.DAY: (255, 255, 255),
            rules.TimeOfDay.DUSK: (255, 200, 150),
            rules.TimeOfDay.NIGHT: (150, 150, 200),
            rules.TimeOfDay.DAWN: (255, 220, 200),
        }
        return mapping.get(self.time_phase, (255, 255, 255))

    def _apply_lighting(self, surface: pygame.Surface) -> None:
        ambient = self._ambient_for_phase()
        self.lightmap.clear(ambient)
        lconf = self.balance.get("lighting", {})
        flicker = lconf.get("flicker", 0.0)
        for p in self.state.players:
            self.lightmap.add_light(
                p.x,
                p.y,
                int(lconf.get("player_radius", 5)),
                float(lconf.get("player_intensity", 1.0)),
            )
        board = self.state.board
        for y, row in enumerate(board.tiles):
            for x, ch in enumerate(row):
                if ch == "f":
                    inten = float(lconf.get("campfire_intensity", 1.5))
                    inten *= rules.RNG.uniform(1 - flicker, 1 + flicker)
                    self.lightmap.add_light(
                        x,
                        y,
                        int(lconf.get("campfire_radius", 7)),
                        inten,
                    )
                elif ch == "l":
                    inten = float(lconf.get("lamp_intensity", 1.2))
                    inten *= rules.RNG.uniform(1 - flicker, 1 + flicker)
                    self.lightmap.add_light(
                        x,
                        y,
                        int(lconf.get("lamp_radius", 6)),
                        inten,
                    )
        self.lightmap.blur()
        lm = self.lightmap.to_surface(TILE_SIZE)
        lm = pygame.transform.scale(lm, surface.get_size())
        surface.blit(lm, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        tint = pygame.Surface(surface.get_size())
        tint.fill(self._color_for_phase())
        surface.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
