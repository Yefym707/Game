import json
from typing import Optional, List
from inventory import Inventory
from game_map import GameMap
from enemies import EnemyManager, StatusEffect
from trader import Trader

class Campaign:
    def __init__(self, scenarios, current_scenario_id=None, game_map: Optional[GameMap]=None, inventory: Optional[Inventory]=None, enemies: Optional[EnemyManager]=None, turn_count: int = 0, time_of_day: str = "day", status_effects: Optional[List[dict]] = None):
        self.scenarios = scenarios
        self.current_scenario_id = current_scenario_id
        self.game_map = game_map or GameMap(10, 8)
        self.inventory = inventory or Inventory()
        self.enemies = enemies or EnemyManager.spawn_on_map(self.game_map.width, self.game_map.height, count=3, player_pos=self.game_map.player_pos)
        self.turn_count = turn_count
        self.time_of_day = time_of_day  # "day" or "night"
        self.status_effects = [StatusEffect.from_dict(d) for d in (status_effects or [])]
        self.progress = {}
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

    # остальной код save/load/аттак/эффекты — без изменений (поддерживает status_effects и progress)
