import json
from typing import Dict, Any, Optional
from crafting import Recipe

class Inventory:
    def __init__(self, items: Dict[str, int] = None, coins: int = 0):
        self.items = items or {}
        self.coins = coins

    def add_item(self, item_name: str, quantity: int = 1):
        self.items[item_name] = self.items.get(item_name, 0) + quantity

    def remove_item(self, item_name: str, quantity: int = 1):
        if item_name in self.items:
            self.items[item_name] -= quantity
            if self.items[item_name] <= 0:
                del self.items[item_name]

    def has_item(self, item_name: str, quantity: int = 1) -> bool:
        return self.items.get(item_name, 0) >= quantity

    def add_coins(self, amount: int):
        self.coins += amount

    def spend_coins(self, amount: int) -> bool:
        if self.coins >= amount:
            self.coins -= amount
            return True
        return False

    def can_craft(self, recipe: Recipe) -> bool:
        return all(self.has_item(item, qty) for item, qty in recipe.ingredients.items())

    def craft(self, recipe: Recipe) -> bool:
        if not self.can_craft(recipe):
            return False
        for item, qty in recipe.ingredients.items():
            self.remove_item(item, qty)
        self.add_item(recipe.result, recipe.result_qty)
        return True

    def use_item(self, item_name: str, campaign) -> str:
        """Use an item from the inventory and apply its effect to ``campaign``.

        The game originally only supported using medkits which made other
        consumables effectively useless.  To make the game loop more engaging
        this method now understands a couple of common items:

        ``аптечка`` – heals the player by three points.
        ``еда`` – removes the ``hunger`` status effect if present.
        ``вода`` – removes the ``thirst`` status effect if present.
        ``противоядие`` – cures ``poison``.

        Unknown items fall back to a default message so additional content can
        be added without changing this method.
        """

        if not self.has_item(item_name):
            return "Нет такого предмета в инвентаре."

        if item_name == "аптечка":
            if campaign.player.health < campaign.player.max_health:
                campaign.player.heal(3)
                self.remove_item(item_name, 1)
                return "Вы использовали аптечку и восстановили 3 здоровья."
            return "У вас и так максимум здоровья."

        if item_name == "еда":
            # Eating clears the hunger status effect if it is active.
            before = len(campaign.status_effects)
            campaign.status_effects = [
                e for e in campaign.status_effects if e.effect_type != "hunger"
            ]
            self.remove_item(item_name, 1)
            if len(campaign.status_effects) < before:
                return "Вы поели и утолили голод."
            return "Вы перекусили, но особых изменений не почувствовали."

        if item_name == "вода":
            # Drinking water removes thirst effects.
            campaign.status_effects = [
                e for e in campaign.status_effects if e.effect_type != "thirst"
            ]
            self.remove_item(item_name, 1)
            return "Вы утолили жажду."

        if item_name == "противоядие":
            # Antidote removes poison if present.
            removed = False
            for e in list(campaign.status_effects):
                if e.effect_type == "poison":
                    campaign.status_effects.remove(e)
                    removed = True
            if removed:
                self.remove_item(item_name, 1)
                return "Вы приняли противоядие и избавились от яда."
            return "Противоядие не требуется."

        return "Этот предмет нельзя использовать напрямую."

    def to_dict(self) -> Dict[str, Any]:
        return {"items": dict(self.items), "coins": self.coins}

    @staticmethod
    def from_dict(data: Dict[str, Any]):
        return Inventory(items=dict(data.get("items", {})), coins=int(data.get("coins", 0)))

    def __str__(self):
        if not self.items and self.coins == 0:
            return "Инвентарь пуст. Монет: 0"
        parts = []
        if self.items:
            parts += [f"{item}: {qty}" for item, qty in self.items.items()]
        parts.append(f"Монет: {self.coins}")
        return "\n".join(parts)