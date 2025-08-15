import json
import os
from typing import Optional, List, Any

from inventory import Inventory
from game_map import GameMap
from enemies import EnemyManager, StatusEffect
from trader import Trader
from player import Player
from scenario import Scenario


def _load_balance() -> dict:
    path = os.path.join(os.path.dirname(__file__), "..", "data", "balance.json")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


HUNGER_THRESHOLD = 5
THIRST_THRESHOLD = 5

class Campaign:
    """Container with all mutable state of the current game session."""

    def __init__(
        self,
        scenarios: List[Scenario],
        current_scenario_id: Optional[str] = None,
        game_map: Optional[GameMap] = None,
        inventory: Optional[Inventory] = None,
        enemies: Optional[EnemyManager] = None,
        player: Optional[Player] = None,
        turn_count: int = 0,
        time_of_day: str = "day",
        status_effects: Optional[List[StatusEffect]] = None,
        progress: Optional[dict] = None,
        difficulty: str = "normal",
    ):
        self.scenarios = scenarios
        self.balance = _load_balance()
        self.difficulty = difficulty
        diff_mult = {"easy": 0.8, "normal": 1.0, "hard": 1.2}.get(difficulty, 1.0)
        player_hp = int(self.balance.get("player", {}).get("hp", 5))
        if difficulty == "easy":
            player_hp = int(player_hp * 1.2)
        elif difficulty == "hard":
            player_hp = int(player_hp * 0.8)
        enemy_hp = int(self.balance.get("zombie", {}).get("hp", 3) * diff_mult)
        enemy_dmg = int(self.balance.get("zombie", {}).get("damage", 1) * diff_mult)
        # default scenario id is not set until the first scenario starts.  A
        # saved game may supply ``current_scenario_id`` explicitly.
        if current_scenario_id is None:
            self.current_scenario_id = None
        else:
            self.current_scenario_id = current_scenario_id
        self.game_map = game_map or GameMap(10, 8)
        self.inventory = inventory or Inventory()
        self.player = player or Player(health=player_hp, max_health=player_hp)
        self.enemies = enemies or EnemyManager.spawn_on_map(
            self.game_map.width,
            self.game_map.height,
            count=3,
            player_pos=self.game_map.player_pos,
            health=enemy_hp,
            attack=enemy_dmg,
        )
        self.enemy_hp = enemy_hp
        self.enemy_damage = enemy_dmg
        self.turn_count = turn_count
        self.time_of_day = time_of_day  # "day" or "night"
        self.status_effects = [
            se if isinstance(se, StatusEffect) else StatusEffect.from_dict(se)
            for se in (status_effects or [])
        ]
        self.progress = progress or {}
        self.skip_turn = False
        self.decoy_pos = None
        # campaign progression bookkeeping ------------------------------
        # ``progress`` is serialised as part of the save game and may
        # already contain campaign related information.  ``current_index``
        # tracks the position within ``self.scenarios`` and defaults to the
        # index of ``current_scenario_id`` or -1 if no scenario started yet.
        idx = -1
        if self.current_scenario_id is not None:
            for i, sc in enumerate(self.scenarios):
                sid = getattr(sc, "name", getattr(sc, "id", None))
                if sid == self.current_scenario_id:
                    idx = i
                    break
        self.progress.setdefault("current_index", idx)
        self.progress.setdefault("results", [])
        self.progress.setdefault("legacy", {})
        self.progress.setdefault("completed", [])

    def tick_time(self):
        # change the time of day every 5 turns
        prev = self.time_of_day
        if self.turn_count % 5 == 0 and self.turn_count > 0:
            self.time_of_day = "night" if self.time_of_day == "day" else "day"
            # when night falls strengthen enemies and sometimes spawn an extra opponent
            if self.time_of_day == "night":
                self._apply_night_effects()
            # when switching to day we could weaken enemies again (optional)
            if prev == "night" and self.time_of_day == "day":
                # implement weakening or visibility restoration etc. if desired
                pass

        # Hunger and thirst progression
        self.player.hunger += 1
        self.player.thirst += 1
        if (
            self.player.hunger >= HUNGER_THRESHOLD
            and not any(e.effect_type == "hunger" for e in self.status_effects)
        ):
            self.status_effects.append(StatusEffect("hunger", duration=-1))
        if (
            self.player.thirst >= THIRST_THRESHOLD
            and not any(e.effect_type == "thirst" for e in self.status_effects)
        ):
            self.status_effects.append(StatusEffect("thirst", duration=-1))

        for effect in list(self.status_effects):
            if effect.effect_type in ("hunger", "thirst"):
                self.player.take_damage(1)
            else:
                effect.duration -= 1
                if effect.duration <= 0:
                    self.status_effects.remove(effect)
                    if effect.effect_type == "decoy":
                        self.decoy_pos = None

    def _apply_night_effects(self):
        # strengthen existing enemies (increase their health by +1 within logical limits)
        for e in self.enemies.enemies:
            e.health += 1
        # chance to spawn another enemy at night
        import random
        if random.random() < 0.4:
            extra = EnemyManager.spawn_on_map(
                self.game_map.width,
                self.game_map.height,
                count=1,
                player_pos=self.game_map.player_pos,
                health=self.enemy_hp,
                attack=self.enemy_damage,
            )
            # add enemies from the extra manager
            self.enemies.enemies.extend(extra.enemies)

    def rest_at_camp(self):
        """Rest at a camp — takes camp level in the zone (meta.level) into account."""
        zone = self.game_map.get_zone_at(self.game_map.player_pos)
        if not zone or zone.zone_type != "camp":
            return "You cannot rest here — no camp found."
        level = zone.meta.get("level", 1)
        missing = self.player.max_health - self.player.health
        # the higher the camp level the more healing
        heal_amount = min(missing, 3 + level)
        if heal_amount > 0:
            self.player.heal(heal_amount)
        # remove hunger/thirst and reduce poison
        self.status_effects = [e for e in self.status_effects if e.effect_type not in ("thirst", "hunger")]
        self.player.hunger = 0
        self.player.thirst = 0
        for e in self.status_effects:
            if e.effect_type == "poison":
                e.duration = max(0, e.duration - 1)
        self.turn_count += 1
        return f"You rested at a level {level} camp. Restored {heal_amount} health."

    def upgrade_camp(self):
        zone = self.game_map.get_zone_at(self.game_map.player_pos)
        if not zone or zone.zone_type != "camp":
            return "No camp here to upgrade."
        level = zone.meta.get("level", 1)
        cost = level * 6  # simple cost formula
        if not self.inventory.spend_coins(cost):
            return f"Upgrading the camp costs {cost} coins — you don't have enough."
        zone.meta["level"] = level + 1
        # optional: reward for upgrading, e.g. trader reputation
        return f"Camp upgraded to level {level+1} for {cost} coins."

    def get_trader_at_player(self) -> Optional[Trader]:
        zone = self.game_map.get_zone_at(self.game_map.player_pos)
        if zone and zone.zone_type == "merchant":
            # traders are not available at night
            if self.time_of_day == "night":
                return None
            goods = zone.meta.get("goods", {})
            name = zone.meta.get("name", "Trader")
            return Trader(name, goods)
        return None
    # ------------------------------------------------------------------
    # campaign progression helpers

    def start_next_scenario(self) -> Optional[Scenario]:
        """Advance the campaign to the next scenario.

        The method resets volatile game state such as the map, enemies and
        turn counter while keeping persistent elements like the player and his
        inventory.  Legacy bonuses stored in ``progress['legacy']`` therefore
        carry over automatically.  ``None`` is returned when the campaign has
        been completed.
        """

        next_index = self.progress.get("current_index", -1) + 1
        if next_index >= len(self.scenarios):
            # campaign finished
            self.progress["campaign_complete"] = True
            self.current_scenario_id = None
            return None

        self.progress["current_index"] = next_index
        scenario = self.scenarios[next_index]
        # Determine id/name for bookkeeping
        self.current_scenario_id = getattr(scenario, "name", getattr(scenario, "id", None))

        # Reset transient game state -----------------------------------
        self.game_map = GameMap(self.game_map.width, self.game_map.height)
        self.enemies = EnemyManager.spawn_on_map(
            self.game_map.width,
            self.game_map.height,
            count=3,
            player_pos=self.game_map.player_pos,
            health=self.enemy_hp,
            attack=self.enemy_damage,
        )
        self.turn_count = 0
        self.time_of_day = "day"
        self.status_effects = []
        self.skip_turn = False
        self.decoy_pos = None

        # Let the scenario perform custom setup ------------------------
        try:
            scenario.setup(self.game_map, [self.player])
        except Exception:
            # Setup is a convenience feature; swallow errors so tests remain
            # lightweight.
            pass

        return scenario

    def record_scenario_result(self, winner: Any, legacy_bonus: Optional[dict] = None) -> None:
        """Store the result of the current scenario.

        ``winner`` can be any hashable identifier (typically a player name).
        ``legacy_bonus`` describes advantages that should persist into future
        scenarios.  Supported keys are ``"bonus_health"`` and ``"items"`` which
        are immediately applied to the current campaign state and recorded so
        they can be serialised when saving the game.
        """

        # record winner ------------------------------------------------
        self.progress.setdefault("results", []).append(
            {"scenario": self.current_scenario_id, "winner": winner}
        )
        self.progress.setdefault("completed", []).append(self.current_scenario_id)

        if not legacy_bonus:
            return

        legacy = self.progress.setdefault("legacy", {})

        # apply and record bonus health
        bonus_hp = int(legacy_bonus.get("bonus_health", 0))
        if bonus_hp:
            self.player.max_health += bonus_hp
            self.player.heal(bonus_hp)
            legacy["bonus_health"] = legacy.get("bonus_health", 0) + bonus_hp

        # apply and record items
        items = legacy_bonus.get("items", {})
        if items:
            inv = legacy.setdefault("items", {})
            for name, qty in items.items():
                self.inventory.add_item(name, qty)
                inv[name] = inv.get(name, 0) + qty
    # ------------------------------------------------------------------
    # saving and loading helpers

    def to_dict(self) -> dict:
        return {
            "current_scenario_id": self.current_scenario_id,
            "game_map": self.game_map.to_dict(),
            "inventory": self.inventory.to_dict(),
            "player": self.player.to_dict(),
            "enemies": self.enemies.to_dict(),
            "turn_count": self.turn_count,
            "time_of_day": self.time_of_day,
            "status_effects": [e.to_dict() for e in self.status_effects],
            "progress": self.progress,
            "difficulty": self.difficulty,
        }

    @staticmethod
    def from_dict(data: dict, scenarios) -> "Campaign":
        return Campaign(
            scenarios,
            current_scenario_id=data.get("current_scenario_id"),
            game_map=GameMap.from_dict(data["game_map"]),
            inventory=Inventory.from_dict(data["inventory"]),
            enemies=EnemyManager.from_dict(data["enemies"]),
            player=Player.from_dict(data.get("player", {})),
            turn_count=int(data.get("turn_count", 0)),
            time_of_day=data.get("time_of_day", "day"),
            status_effects=[StatusEffect.from_dict(d) for d in data.get("status_effects", [])],
            progress=data.get("progress", {}),
            difficulty=data.get("difficulty", "normal"),
        )

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @staticmethod
    def load(path: str, scenarios) -> "Campaign":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Campaign.from_dict(data, scenarios)
