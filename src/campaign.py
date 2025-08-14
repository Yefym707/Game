import json
from typing import Optional, List

from inventory import Inventory
from game_map import GameMap
from enemies import EnemyManager, StatusEffect
from trader import Trader
from player import Player

class Campaign:
    """Container with all mutable state of the current game session."""

    def __init__(
        self,
        scenarios,
        current_scenario_id: Optional[str] = None,
        game_map: Optional[GameMap] = None,
        inventory: Optional[Inventory] = None,
        enemies: Optional[EnemyManager] = None,
        player: Optional[Player] = None,
        turn_count: int = 0,
        time_of_day: str = "day",
        status_effects: Optional[List[StatusEffect]] = None,
        progress: Optional[dict] = None,
    ):
        self.scenarios = scenarios
        # default scenario id is the first one if provided
        if current_scenario_id is None and scenarios:
            current_scenario_id = scenarios[0].get("id")
        self.current_scenario_id = current_scenario_id
        self.game_map = game_map or GameMap(10, 8)
        self.inventory = inventory or Inventory()
        self.player = player or Player()
        self.enemies = enemies or EnemyManager.spawn_on_map(
            self.game_map.width, self.game_map.height, count=3, player_pos=self.game_map.player_pos
        )
        self.turn_count = turn_count
        self.time_of_day = time_of_day  # "day" or "night"
        self.status_effects = [se if isinstance(se, StatusEffect) else StatusEffect.from_dict(se) for se in (status_effects or [])]
        self.progress = progress or {}
        self.skip_turn = False

    def tick_time(self):
        # меняем время суток каждые 5 ходов
        prev = self.time_of_day
        if self.turn_count % 5 == 0 and self.turn_count > 0:
            self.time_of_day = "night" if self.time_of_day == "day" else "day"
            # если наступила ночь — усиливаем врагов и иногда появится дополнительный противник
            if self.time_of_day == "night":
                self._apply_night_effects()
            # при переходе на день можно ослабить врагов (опционально)
            if prev == "night" and self.time_of_day == "day":
                # можно реализовать ослабление или восстановление видимости и т.п.
                pass

    def _apply_night_effects(self):
        # Усиливаем существующих врагов (увеличиваем им здоровье на +1, не выше логического предела)
        for e in self.enemies.enemies:
            e.health += 1
        # шанс появления ещё одного врага ночью
        import random
        if random.random() < 0.4:
            extra = EnemyManager.spawn_on_map(self.game_map.width, self.game_map.height, count=1, player_pos=self.game_map.player_pos)
            # добавляем врагов из extra
            self.enemies.enemies.extend(extra.enemies)

    def rest_at_camp(self):
        """Отдых в лагере — учитывает уровень лагеря в зоне (meta.level)."""
        zone = self.game_map.get_zone_at(self.game_map.player_pos)
        if not zone or zone.zone_type != "camp":
            return "Здесь нельзя отдохнуть — нет лагеря."
        level = zone.meta.get("level", 1)
        missing = self.player.max_health - self.player.health
        # Чем выше уровень лагеря, тем больше восстановления (пример)
        heal_amount = min(missing, 3 + level)
        if heal_amount > 0:
            self.player.heal(heal_amount)
        # Снимаем голод/жажду и уменьшаем яд
        self.status_effects = [e for e in self.status_effects if e.effect_type not in ("thirst", "hunger")]
        for e in self.status_effects:
            if e.effect_type == "poison":
                e.duration = max(0, e.duration - 1)
        self.turn_count += 1
        return f"Вы отдохнули в лагере уровня {level}. Восстановлено {heal_amount} здоровья."

    def upgrade_camp(self):
        zone = self.game_map.get_zone_at(self.game_map.player_pos)
        if not zone or zone.zone_type != "camp":
            return "Здесь нет лагеря для улучшения."
        level = zone.meta.get("level", 1)
        cost = level * 6  # простая формула стоимости
        if not self.inventory.spend_coins(cost):
            return f"Улучшение лагеря стоит {cost} монет — у вас недостаточно монет."
        zone.meta["level"] = level + 1
        # Небольшая награда за улучшение в прогрессе (репутация у торговцев или т.п.) можно добавить
        return f"Лагерь улучшен до уровня {level+1} за {cost} монет."

    def get_trader_at_player(self) -> Optional[Trader]:
        zone = self.game_map.get_zone_at(self.game_map.player_pos)
        if zone and zone.zone_type == "merchant":
            # торговцы недоступны ночью
            if self.time_of_day == "night":
                return None
            goods = zone.meta.get("goods", {})
            name = zone.meta.get("name", "Торговец")
            return Trader(name, goods)
        return None
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
        )

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @staticmethod
    def load(path: str, scenarios) -> "Campaign":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Campaign.from_dict(data, scenarios)
